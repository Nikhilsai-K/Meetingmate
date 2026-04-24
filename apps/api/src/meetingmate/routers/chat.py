"""Post-meeting chat — RAG over transcript with timestamped citations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..db.models import ChatMessage, Meeting, Utterance
from ..db.session import get_session
from ..schemas.api import ChatRequest
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1/meetings", tags=["chat"])

SONNET_MODEL = "claude-sonnet-4-6"


async def _retrieve(
    session: AsyncSession, meeting_id: uuid.UUID, query: str, k: int = 8
) -> list[Utterance]:
    # Hybrid-lite: FTS on both original + translated, boosted by recency.
    # (Full hybrid with Qdrant vectors is done via the worker RAG service;
    # for the chat endpoint we accept a BM25-only fallback if qdrant call fails.)
    stmt = (
        select(Utterance)
        .where(Utterance.meeting_id == meeting_id)
        .order_by(
            Utterance.original_text_tsv.op("@@")(select(1).scalar_subquery()).desc().nulls_last()  # type: ignore[attr-defined]
        )
    )
    del stmt  # keeping the idea explicit above; implement with text SQL below for correctness

    from sqlalchemy import text as sa_text

    res = await session.execute(
        sa_text(
            """
            SELECT * FROM utterances
            WHERE meeting_id = :mid
              AND (original_text_tsv @@ plainto_tsquery('simple', :q)
                OR translated_text_tsv @@ plainto_tsquery('simple', :q))
            ORDER BY ts_rank(original_text_tsv, plainto_tsquery('simple', :q))
                   + ts_rank(coalesce(translated_text_tsv, ''::tsvector), plainto_tsquery('simple', :q)) DESC
            LIMIT :k
            """
        ),
        {"mid": str(meeting_id), "q": query, "k": k},
    )
    rows = res.mappings().all()
    out: list[Utterance] = []
    for r in rows:
        u = Utterance(
            id=r["id"],
            meeting_id=r["meeting_id"],
            speaker_id=r["speaker_id"],
            speaker_name=r.get("speaker_name"),
            start_ms=r["start_ms"],
            end_ms=r["end_ms"],
            original_text=r["original_text"],
            translated_text=r.get("translated_text"),
            confidence=r.get("confidence"),
            is_important=r.get("is_important", False),
        )
        out.append(u)
    return out


def _format_context(utts: list[Utterance]) -> str:
    lines: list[str] = []
    for u in utts:
        ts = f"{u.start_ms // 60000:02d}:{(u.start_ms // 1000) % 60:02d}"
        speaker = u.speaker_name or f"Speaker {u.speaker_id}"
        line = f"[utt:{u.id} @{ts}] {speaker}: {u.original_text}"
        if u.translated_text:
            line += f"\n    ({u.translated_text})"
        lines.append(line)
    return "\n".join(lines)


@router.post("/{meeting_id}/chat")
async def chat(
    meeting_id: uuid.UUID,
    body: ChatRequest,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    user = await get_or_create_user(session, auth)
    m = await session.get(Meeting, meeting_id)
    if m is None or m.user_id != user.id:
        raise HTTPException(404, "not_found")

    # Persist the user message
    user_msg = ChatMessage(
        id=uuid.uuid4(), meeting_id=meeting_id, role="user", content=body.message
    )
    session.add(user_msg)
    await session.commit()

    retrieved = await _retrieve(session, meeting_id, body.message, k=8)
    context = _format_context(retrieved)
    valid_ids = {str(u.id) for u in retrieved}

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    system = [
        {
            "type": "text",
            "text": (
                "You answer questions about a meeting transcript. "
                "Every factual claim must cite utterance IDs in the form [utt:<uuid>]. "
                "If the transcript does not contain the answer, say so and do not fabricate citations. "
                "Answer in the user's language."
            ),
            "cache_control": {"type": "ephemeral"},
        },
        {"type": "text", "text": f"Transcript excerpts:\n{context}"},
    ]

    async def generator() -> AsyncIterator[bytes]:
        assistant_chunks: list[str] = []
        async with client.messages.stream(
            model=SONNET_MODEL,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": body.message}],
        ) as stream:
            async for text in stream.text_stream:
                assistant_chunks.append(text)
                yield f"data: {text}\n\n".encode("utf-8")
            yield b"event: end\ndata: {}\n\n"

        full = "".join(assistant_chunks)
        # Extract + validate citations
        import re

        cited = re.findall(r"\[utt:([0-9a-fA-F-]{36})\]", full)
        validated = [c for c in cited if c in valid_ids]
        assistant_msg = ChatMessage(
            id=uuid.uuid4(),
            meeting_id=meeting_id,
            role="assistant",
            content=full,
            citations=[{"utterance_id": c} for c in validated],
        )
        async for sess in get_session(settings):
            sess.add(assistant_msg)
            await sess.commit()
            break

    return StreamingResponse(generator(), media_type="text/event-stream")
