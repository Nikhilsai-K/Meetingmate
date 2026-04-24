"""Meetings REST API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..db.models import Meeting, User, Utterance
from ..db.session import get_session
from ..schemas.api import (
    CreateMeetingRequest,
    CreateMeetingResponse,
    MeetingListResponse,
    MeetingOut,
    UtteranceListResponse,
    UtteranceOut,
)
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1/meetings", tags=["meetings"])


async def _require_user(
    auth: AuthContext, session: AsyncSession
) -> User:
    return await get_or_create_user(session, auth)


@router.post("", response_model=CreateMeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    body: CreateMeetingRequest,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CreateMeetingResponse:
    user = await _require_user(auth, session)

    if user.consent_recording_ack_at is None:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="recording_consent_required",
        )

    meeting = Meeting(
        id=uuid.uuid4(),
        user_id=user.id,
        title=body.title,
        source_language=body.source_language,
        target_language=body.target_language,
        google_meet_code=body.google_meet_code,
        template=body.template,
        status="recording",
    )
    session.add(meeting)
    await session.commit()
    await session.refresh(meeting)

    ws_base = settings.api_base_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = (
        f"{ws_base}/v1/live?meeting_id={meeting.id}"
        f"&source_lang={meeting.source_language}&target_lang={meeting.target_language}"
    )
    return CreateMeetingResponse(meeting_id=meeting.id, ws_url=ws_url)


@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> MeetingListResponse:
    user = await _require_user(auth, session)
    stmt = (
        select(Meeting)
        .where(Meeting.user_id == user.id, Meeting.is_saved.is_(True))
        .order_by(desc(Meeting.created_at))
        .limit(limit + 1)
    )
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            cursor_row = await session.get(Meeting, cursor_id)
            if cursor_row is not None:
                stmt = stmt.where(Meeting.created_at < cursor_row.created_at)
        except ValueError:
            pass
    rows = (await session.execute(stmt)).scalars().all()
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    next_cursor = str(rows[-1].id) if has_more and rows else None
    return MeetingListResponse(
        items=[MeetingOut.model_validate(r) for r in rows], next_cursor=next_cursor
    )


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> MeetingOut:
    user = await _require_user(auth, session)
    m = await session.get(Meeting, meeting_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(404, "not_found")
    return MeetingOut.model_validate(m)


@router.get("/{meeting_id}/utterances", response_model=UtteranceListResponse)
async def list_utterances(
    meeting_id: uuid.UUID,
    limit: int = Query(default=200, ge=1, le=1000),
    after_ms: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> UtteranceListResponse:
    user = await _require_user(auth, session)
    m = await session.get(Meeting, meeting_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(404, "not_found")
    stmt = (
        select(Utterance)
        .where(Utterance.meeting_id == meeting_id, Utterance.start_ms > after_ms)
        .order_by(Utterance.start_ms)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return UtteranceListResponse(items=[UtteranceOut.model_validate(r) for r in rows])


@router.post("/{meeting_id}/utterances/{utterance_id}/mark-important")
async def mark_important(
    meeting_id: uuid.UUID,
    utterance_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await _require_user(auth, session)
    m = await session.get(Meeting, meeting_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(404, "not_found")
    u = await session.get(Utterance, utterance_id)
    if u is None or u.meeting_id != meeting_id:
        raise HTTPException(404, "not_found")
    u.is_important = not u.is_important
    await session.commit()
    return {"id": str(u.id), "is_important": u.is_important}


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> None:
    user = await _require_user(auth, session)
    m = await session.get(Meeting, meeting_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(404, "not_found")
    await session.execute(delete(Meeting).where(Meeting.id == meeting_id))
    await session.commit()
