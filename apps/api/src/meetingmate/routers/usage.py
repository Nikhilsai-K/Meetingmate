"""Usage + consent + me endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..db.session import get_session
from ..schemas.api import UsageResponse
from ..services.rate_limit import get_current
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1", tags=["usage"])


@router.get("/usage/current", response_model=UsageResponse)
async def current_usage(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UsageResponse:
    user = await get_or_create_user(session, auth)
    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    try:
        used = await get_current(redis, str(user.id))
    finally:
        await redis.close()
    limit_hours = (
        settings.rate_limit_pro_meeting_hours_per_day
        if user.plan in ("pro", "team")
        else settings.rate_limit_free_meeting_hours_per_day
    )
    return UsageResponse(
        minutes_today=used // 60,
        minutes_limit=limit_hours * 60,
        plan=user.plan,
        cost_usd_today=0.0,
    )


@router.get("/me")
async def me(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await get_or_create_user(session, auth)
    return {
        "id": str(user.id),
        "email": user.email,
        "plan": user.plan,
        "preferred_source_lang": user.preferred_source_lang,
        "preferred_target_lang": user.preferred_target_lang,
        "consent_recording_ack_at": user.consent_recording_ack_at.isoformat()
        if user.consent_recording_ack_at
        else None,
    }


@router.post("/me/consent/recording")
async def ack_recording_consent(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await get_or_create_user(session, auth)
    user.consent_recording_ack_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True, "at": user.consent_recording_ack_at.isoformat()}


@router.patch("/me/preferences")
async def update_preferences(
    body: dict,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await get_or_create_user(session, auth)
    if "preferred_source_lang" in body:
        user.preferred_source_lang = str(body["preferred_source_lang"])[:8]
    if "preferred_target_lang" in body:
        user.preferred_target_lang = str(body["preferred_target_lang"])[:8]
    await session.commit()
    return {"ok": True}
