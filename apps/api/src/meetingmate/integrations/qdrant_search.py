"""Qdrant vector search (scoped by user_id filter)."""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from ..core.config import Settings
from .embeddings import embed_one

COLLECTION = "utterances"


def qdrant_client(settings: Settings) -> AsyncQdrantClient:
    return AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


async def qdrant_search(
    settings: Settings, *, user_id: str, query: str, limit: int = 20
) -> list[dict]:
    client = qdrant_client(settings)
    try:
        vec = await embed_one(settings, query)
        results = await client.query_points(
            collection_name=COLLECTION,
            query=vec,
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
        )
        out: list[dict] = []
        for p in results.points:
            payload = p.payload or {}
            out.append(
                {
                    "utterance_id": payload.get("utterance_id"),
                    "meeting_id": payload.get("meeting_id"),
                    "meeting_title": payload.get("meeting_title"),
                    "start_ms": payload.get("start_ms", 0),
                    "text": payload.get("original_text", ""),
                    "translated": payload.get("translated_text"),
                    "score": p.score,
                    "source": "vector",
                }
            )
        return out
    finally:
        await client.close()
