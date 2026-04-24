"""Rate-limit unit test — mocks redis since we just assert the arithmetic/logic."""

from __future__ import annotations

import pytest

from meetingmate.core.config import Settings
from meetingmate.services.rate_limit import check_and_increment


class FakePipeline:
    def __init__(self, store: dict[str, int]) -> None:
        self._store = store
        self._key: str | None = None
        self._incr_by = 0

    def incrby(self, key: str, amount: int) -> None:
        self._key = key
        self._incr_by = amount

    def expire(self, _key: str, _ttl: int) -> None: ...

    async def execute(self):
        assert self._key is not None
        self._store[self._key] = self._store.get(self._key, 0) + self._incr_by
        return self._store[self._key], True

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def pipeline(self, transaction: bool = True):  # noqa: ARG002
        return FakePipeline(self.store)


@pytest.mark.asyncio
async def test_rate_limit_passes_below_cap() -> None:
    settings = Settings()  # type: ignore[call-arg]
    redis = FakeRedis()
    ok, current, limit = await check_and_increment(redis, "u1", 3600, "free", settings)
    assert ok
    assert current == 3600
    assert limit == settings.rate_limit_free_meeting_hours_per_day * 3600


@pytest.mark.asyncio
async def test_rate_limit_trips_over_cap() -> None:
    settings = Settings()  # type: ignore[call-arg]
    redis = FakeRedis()
    cap = settings.rate_limit_free_meeting_hours_per_day * 3600
    # Prime the bucket just over the limit
    redis.store["rate:meeting-seconds:u1:whatever"] = 0
    ok, _, _ = await check_and_increment(redis, "u1", cap + 1, "free", settings)
    assert ok is False
