"""User upsert from Clerk claims."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext
from ..db.models import User


async def get_or_create_user(session: AsyncSession, ctx: AuthContext) -> User:
    result = await session.execute(select(User).where(User.clerk_user_id == ctx.clerk_user_id))
    user = result.scalar_one_or_none()
    if user is not None:
        if ctx.email and user.email != ctx.email:
            user.email = ctx.email
            await session.commit()
        return user

    user = User(
        id=uuid.uuid4(),
        clerk_user_id=ctx.clerk_user_id,
        email=ctx.email or "",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
