"""Shared pytest fixtures."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_BUCKET_TRANSCRIPTS", "test-bucket")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin")
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("CLERK_JWKS_URL", "https://example.com/.well-known/jwks.json")
os.environ.setdefault("CLERK_ISSUER", "https://example.com")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-fake")
os.environ.setdefault("DEEPGRAM_API_KEY", "fake")
os.environ.setdefault("VOYAGE_API_KEY", "fake")
os.environ.setdefault("COHERE_API_KEY", "fake")


@pytest.fixture
def fake_clerk_user_id() -> str:
    return f"user_{uuid.uuid4().hex[:10]}"


@pytest_asyncio.fixture
async def fake_app() -> AsyncIterator["FastAPI"]:  # type: ignore[name-defined]
    from meetingmate.main import app

    yield app
