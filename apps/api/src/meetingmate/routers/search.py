"""Cross-meeting semantic search.

Hybrid: Postgres BM25 (utterances_orig_tsv + translated_tsv) UNION'd with Qdrant vector
search, then Cohere reranked.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..db.session import get_session
from ..integrations.qdrant_search import qdrant_search
from ..integrations.reranker import rerank
from ..schemas.api import SearchResponse
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1", tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, max_length=500),
    limit: int = Query(default=20, ge=1, le=50),
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    user = await get_or_create_user(session, auth)

    # BM25 side
    rows = (
        await session.execute(
            sa_text(
                """
                SELECT u.id, u.meeting_id, u.start_ms, u.original_text, u.translated_text,
                       m.title as meeting_title
                FROM utterances u
                JOIN meetings m ON m.id = u.meeting_id
                WHERE m.user_id = :uid
                  AND (u.original_text_tsv @@ plainto_tsquery('simple', :q)
                    OR u.translated_text_tsv @@ plainto_tsquery('simple', :q))
                ORDER BY ts_rank(u.original_text_tsv, plainto_tsquery('simple', :q)) DESC
                LIMIT :k
                """
            ),
            {"uid": str(user.id), "q": q, "k": limit * 3},
        )
    ).mappings().all()

    bm25_hits = [
        {
            "utterance_id": str(r["id"]),
            "meeting_id": str(r["meeting_id"]),
            "meeting_title": r["meeting_title"],
            "start_ms": r["start_ms"],
            "text": r["original_text"],
            "translated": r.get("translated_text"),
            "source": "bm25",
        }
        for r in rows
    ]

    # Vector side
    try:
        vec_hits = await qdrant_search(settings, user_id=str(user.id), query=q, limit=limit * 3)
    except Exception:
        vec_hits = []

    # Merge + dedupe by utterance_id
    seen: set[str] = set()
    merged: list[dict] = []
    for h in bm25_hits + vec_hits:
        uid = h.get("utterance_id")
        if uid and uid not in seen:
            seen.add(uid)
            merged.append(h)

    # Rerank
    docs = [f"{h.get('text', '')}\n{h.get('translated') or ''}" for h in merged]
    try:
        order = await rerank(settings, q, docs, top_n=limit)
        results = [merged[i] for i, _ in order]
    except Exception:
        results = merged[:limit]

    return SearchResponse(items=results)
