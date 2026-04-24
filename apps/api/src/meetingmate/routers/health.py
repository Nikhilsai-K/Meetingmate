from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/v1/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"ok": True}


@router.get("/v1/ready")
async def ready() -> dict:
    return {"ok": True}
