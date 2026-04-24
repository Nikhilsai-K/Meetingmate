"""Post-meeting pipeline:
  1. Load utterances
  2. Generate summary/decisions/action_items/glossary with Sonnet
  3. Embed utterances + upsert to Qdrant
  4. Upload transcript JSON to S3
  5. Mark meeting status=complete
  6. Enqueue integrations sync job
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from meetingmate.core.config import get_settings
from meetingmate.core.logging import get_logger
from meetingmate.db.models import Meeting, Utterance
from meetingmate.db.session import get_session, init_engine
from meetingmate.integrations.embeddings import embed_many
from meetingmate.integrations.qdrant_search import qdrant_client as make_qdrant
from meetingmate.services.s3 import upload_transcript
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sqlalchemy import select

from ..celery_app import app
from ..notes_generator import generate_notes

log = get_logger(__name__)

COLLECTION = "utterances"
EMBED_DIM = 1024  # voyage-3


async def _ensure_collection(settings) -> None:
    client = make_qdrant(settings)
    try:
        collections = await client.get_collections()
        if COLLECTION not in [c.name for c in collections.collections]:
            await client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
            )
    finally:
        await client.close()


async def _run(meeting_id: str) -> dict[str, Any]:
    settings = get_settings()
    init_engine(settings)

    mid = uuid.UUID(meeting_id)
    async for session in get_session(settings):
        m = await session.get(Meeting, mid)
        if m is None:
            log.warning("post_process_meeting_not_found", meeting_id=meeting_id)
            return {"ok": False}

        utts = (
            (
                await session.execute(
                    select(Utterance)
                    .where(Utterance.meeting_id == mid)
                    .order_by(Utterance.start_ms)
                )
            )
            .scalars()
            .all()
        )

        if not utts:
            m.status = "complete"
            await session.commit()
            return {"ok": True, "empty": True}

        transcript = [
            {
                "id": str(u.id),
                "speaker_id": u.speaker_id,
                "speaker_name": u.speaker_name,
                "start_ms": u.start_ms,
                "end_ms": u.end_ms,
                "original_text": u.original_text,
                "translated_text": u.translated_text,
            }
            for u in utts
        ]

        # Notes generation
        try:
            notes_result = await generate_notes(
                settings, transcript, m.template, m.target_language
            )
            notes = notes_result["notes"]
            m.summary = notes.get("summary")
            m.decisions = notes.get("decisions") or []
            m.action_items = notes.get("action_items") or []
            m.open_questions = notes.get("open_questions") or []
            m.glossary = notes.get("glossary") or []
        except Exception as e:
            log.error("notes_generation_failed", meeting_id=meeting_id, error=str(e))
            m.status = "failed"
            await session.commit()
            return {"ok": False, "reason": "notes_failed"}

        # Embeddings
        try:
            await _ensure_collection(settings)
            batch_size = 64
            qc = make_qdrant(settings)
            try:
                for i in range(0, len(utts), batch_size):
                    batch = utts[i : i + batch_size]
                    texts = [
                        f"{u.original_text}\n{u.translated_text or ''}".strip() for u in batch
                    ]
                    vecs = await embed_many(settings, texts)
                    points = []
                    for u, v in zip(batch, vecs):
                        point_id = uuid.uuid4()
                        u.qdrant_point_id = point_id
                        points.append(
                            PointStruct(
                                id=str(point_id),
                                vector=v,
                                payload={
                                    "user_id": str(m.user_id),
                                    "meeting_id": str(m.id),
                                    "meeting_title": m.title or "",
                                    "utterance_id": str(u.id),
                                    "start_ms": u.start_ms,
                                    "original_text": u.original_text,
                                    "translated_text": u.translated_text,
                                },
                            )
                        )
                    await qc.upsert(collection_name=COLLECTION, points=points)
            finally:
                await qc.close()
        except Exception as e:
            log.warning("embedding_failed", meeting_id=meeting_id, error=str(e))

        # Transcript upload
        try:
            key = upload_transcript(
                settings,
                str(m.id),
                {
                    "meeting": {
                        "id": str(m.id),
                        "title": m.title,
                        "started_at": m.started_at.isoformat() if m.started_at else None,
                        "duration_s": m.duration_s,
                        "source_language": m.source_language,
                        "target_language": m.target_language,
                    },
                    "utterances": transcript,
                    "notes": {
                        "summary": m.summary,
                        "decisions": m.decisions,
                        "action_items": m.action_items,
                        "open_questions": m.open_questions,
                        "glossary": m.glossary,
                    },
                },
            )
            m.transcript_s3_key = key
        except Exception as e:
            log.warning("transcript_upload_failed", meeting_id=meeting_id, error=str(e))

        m.status = "complete"
        await session.commit()

    # Kick integrations sync
    try:
        from .integrations_sync import push_action_items

        push_action_items.delay(meeting_id)
    except Exception as e:
        log.warning("enqueue_integrations_sync_failed", error=str(e))

    return {"ok": True, "meeting_id": meeting_id}


@app.task(name="meetingmate.post_process_meeting", bind=True, max_retries=3, default_retry_delay=30)
def post_process_meeting(self, meeting_id: str) -> dict[str, Any]:  # noqa: ANN001
    try:
        return asyncio.run(_run(meeting_id))
    except Exception as exc:
        raise self.retry(exc=exc)
