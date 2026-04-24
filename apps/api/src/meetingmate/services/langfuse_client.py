"""Langfuse integration — log every LLM/STT call with meeting_id metadata.

NEVER include transcript text in logged prompts; only metadata (model, tokens, cost, latency).
"""

from __future__ import annotations

from typing import Any

from langfuse import Langfuse

from ..core.config import Settings
from ..core.logging import get_logger

log = get_logger(__name__)

_client: Langfuse | None = None


def get_langfuse(settings: Settings) -> Langfuse | None:
    global _client
    if _client is not None:
        return _client
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    _client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return _client


def log_translation(
    settings: Settings,
    *,
    user_id: str,
    meeting_id: str,
    source_lang: str,
    target_lang: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int,
    cost_cents: int,
    latency_ms: int,
) -> None:
    client = get_langfuse(settings)
    if client is None:
        return
    try:
        client.generation(
            name="haiku.translate",
            model="claude-haiku-4-5",
            user_id=user_id,
            metadata={
                "meeting_id": meeting_id,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "cost_cents": cost_cents,
                "latency_ms": latency_ms,
            },
            usage={
                "input": input_tokens,
                "output": output_tokens,
                "input_cached": cached_tokens,
                "unit": "TOKENS",
            },
        )
    except Exception as e:  # observability must never break the request path
        log.warning("langfuse_log_failed", error=str(e))


def log_stt(
    settings: Settings,
    *,
    user_id: str,
    meeting_id: str,
    language: str,
    duration_s: int,
    cost_cents: int,
) -> None:
    client = get_langfuse(settings)
    if client is None:
        return
    try:
        client.event(
            name="deepgram.stt",
            user_id=user_id,
            metadata={
                "meeting_id": meeting_id,
                "language": language,
                "duration_s": duration_s,
                "cost_cents": cost_cents,
                "model": "nova-3",
            },
        )
    except Exception as e:
        log.warning("langfuse_log_failed", error=str(e))


def log_generic(settings: Settings, name: str, metadata: dict[str, Any]) -> None:
    client = get_langfuse(settings)
    if client is None:
        return
    try:
        client.event(name=name, metadata=metadata)
    except Exception:
        pass
