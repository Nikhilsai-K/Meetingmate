"""User pinned vocabulary — boosts Deepgram STT + used as Haiku glossary."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..db.session import get_session
from ..schemas.api import VocabularyItem, VocabularyListResponse
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1/vocabulary", tags=["vocabulary"])


@router.get("", response_model=VocabularyListResponse)
async def list_vocab(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> VocabularyListResponse:
    user = await get_or_create_user(session, auth)
    return VocabularyListResponse(
        items=[VocabularyItem(**v) for v in (user.pinned_vocabulary or [])]
    )


@router.post("", response_model=VocabularyListResponse)
async def add_vocab(
    item: VocabularyItem,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> VocabularyListResponse:
    user = await get_or_create_user(session, auth)
    existing = list(user.pinned_vocabulary or [])
    existing = [v for v in existing if v.get("term") != item.term]
    existing.append(item.model_dump())
    user.pinned_vocabulary = existing
    await session.commit()
    return VocabularyListResponse(items=[VocabularyItem(**v) for v in existing])


@router.delete("/{term}", response_model=VocabularyListResponse)
async def remove_vocab(
    term: str,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> VocabularyListResponse:
    user = await get_or_create_user(session, auth)
    existing = [v for v in (user.pinned_vocabulary or []) if v.get("term") != term]
    user.pinned_vocabulary = existing
    await session.commit()
    return VocabularyListResponse(items=[VocabularyItem(**v) for v in existing])
