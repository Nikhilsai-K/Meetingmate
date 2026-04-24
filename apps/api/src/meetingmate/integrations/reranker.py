"""Cohere reranker."""

from __future__ import annotations

import cohere

from ..core.config import Settings


async def rerank(
    settings: Settings, query: str, docs: list[str], top_n: int = 8
) -> list[tuple[int, float]]:
    if not docs:
        return []
    client = cohere.AsyncClient(api_key=settings.cohere_api_key)
    try:
        resp = await client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=docs,
            top_n=min(top_n, len(docs)),
        )
        return [(r.index, r.relevance_score) for r in resp.results]
    finally:
        await client.close()
