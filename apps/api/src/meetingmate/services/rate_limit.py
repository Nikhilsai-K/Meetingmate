"""Per-user daily meeting-hours rate limiting backed by Redis.

Key: `rate:meeting-seconds:<user_id>:<YYYY-MM-DD>` = seconds of audio transcribed today.
TTL: 48h (we only ever check today's bucket).
"""

from __future__ import annotations

from datetime import datetime, timezone

from redis.asyncio import Redis

from ..core.config import Settings


def _today_key(user_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"rate:meeting-seconds:{user_id}:{today}"


async def check_and_increment(
    redis: Redis, user_id: str, seconds: int, plan: str, settings: Settings
) -> tuple[bool, int, int]:
    """Atomically increment usage and return (ok, current_seconds, limit_seconds)."""
    limit_hours = (
        settings.rate_limit_pro_meeting_hours_per_day
        if plan in ("pro", "team")
        else settings.rate_limit_free_meeting_hours_per_day
    )
    limit_seconds = limit_hours * 3600
    key = _today_key(user_id)
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incrby(key, seconds)
        pipe.expire(key, 48 * 3600)
        current, _ = await pipe.execute()
    return bool(int(current) <= limit_seconds), int(current), limit_seconds


async def get_current(redis: Redis, user_id: str) -> int:
    val = await redis.get(_today_key(user_id))
    return int(val) if val else 0
