"""Voyage embeddings client (multilingual, strong on Japanese)."""

from __future__ import annotations

import voyageai

from ..core.config import Settings

VOYAGE_MODEL = "voyage-3"


async def embed_many(settings: Settings, texts: list[str]) -> list[list[float]]:
    client = voyageai.Client(api_key=settings.voyage_api_key)
    # voyageai is sync; it's fast enough to run inline (<150ms for batch of 32)
    result = client.embed(texts, model=VOYAGE_MODEL, input_type="document")
    return result.embeddings


async def embed_one(settings: Settings, text: str) -> list[float]:
    client = voyageai.Client(api_key=settings.voyage_api_key)
    result = client.embed([text], model=VOYAGE_MODEL, input_type="query")
    return result.embeddings[0]
