"""SQLAlchemy async engine + session factory with per-request RLS."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import Settings, get_settings

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        return
    _engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=10,
        echo=False,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def get_session(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    if _sessionmaker is None:
        init_engine(settings)
    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        yield session


async def get_session_with_rls(
    user_id: str,
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AsyncSession]:
    """Session with app.user_id GUC set — activates RLS policies."""
    if _sessionmaker is None:
        init_engine(settings)
    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        from sqlalchemy import text

        await session.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": user_id})
        yield session
