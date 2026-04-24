"""WebSocket endpoint /v1/live — the core audio relay.

Flow per meeting:
  1. extension connects with JWT in `Sec-WebSocket-Protocol` (we read both protocols
     `meetingmate.v1` and `bearer.<jwt>`).
  2. we verify JWT, load user, open Deepgram session.
  3. incoming binary frames → forwarded to Deepgram.
  4. Deepgram `TranscriptEvent`s → we fork:
       - emit `{type:"interim"|"final", ...}` to extension
       - on `is_final`, persist Utterance + fire Haiku translation stream
       - stream translation tokens as `{type:"translation-delta"}` + `{type:"translation-done"}`
  5. on client close or `{type:"end"}` message → close Deepgram, enqueue Celery post-process job.

Audio bytes are never persisted. Only Utterance rows (text + metadata) land in Postgres.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
import uuid
from typing import Any

import orjson
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from redis.asyncio import Redis

from ..core.auth import verify_clerk_jwt
from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..db.models import Meeting, Utterance
from ..db.session import get_session, init_engine
from ..services.deepgram_relay import (
    DeepgramSession,
    estimate_stt_cost_cents,
)
from ..services.langfuse_client import log_stt, log_translation
from ..services.rate_limit import check_and_increment
from ..services.translator import Translator, estimate_haiku_cost_cents
from ..services.users import get_or_create_user

log = get_logger(__name__)
router = APIRouter(tags=["live"])


def _extract_jwt_from_subprotocols(protocols: list[str]) -> str | None:
    # Chrome extensions can't set arbitrary headers on WS, so the token is smuggled
    # as a subprotocol: "bearer.<jwt>".
    for p in protocols:
        p = p.strip()
        if p.startswith("bearer."):
            return p[len("bearer.") :]
    return None


async def _send_json(ws: WebSocket, payload: dict[str, Any]) -> None:
    # orjson is faster; fastapi's send_json uses json.
    await ws.send_bytes(orjson.dumps(payload))


async def _persist_utterance(
    session_factory, meeting_id: uuid.UUID, data: dict[str, Any]
) -> Utterance:
    async for sess in session_factory():
        u = Utterance(
            id=uuid.uuid4(),
            meeting_id=meeting_id,
            speaker_id=data["speaker_id"],
            start_ms=data["start_ms"],
            end_ms=data["end_ms"],
            original_text=data["text"],
            confidence=data.get("confidence"),
        )
        sess.add(u)
        await sess.commit()
        await sess.refresh(u)
        return u
    raise RuntimeError("session generator exhausted")


@router.websocket("/v1/live")
async def live_ws(
    ws: WebSocket,
    meeting_id: uuid.UUID = Query(...),
    source_lang: str = Query("ja"),
    target_lang: str = Query("en"),
) -> None:
    settings = get_settings()
    init_engine(settings)

    offered = ws.headers.get("sec-websocket-protocol", "")
    protocols = [p.strip() for p in offered.split(",")] if offered else []
    token = _extract_jwt_from_subprotocols(protocols)
    if not token:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing_token")
        return

    try:
        ctx = await verify_clerk_jwt(token, settings)
    except Exception:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="auth_failed")
        return

    await ws.accept(subprotocol="meetingmate.v1")

    redis = Redis.from_url(settings.redis_url, decode_responses=False)

    # Validate meeting ownership + consent + plan
    async for session in get_session(settings):
        user = await get_or_create_user(session, ctx)
        meeting = await session.get(Meeting, meeting_id)
        if meeting is None or meeting.user_id != user.id:
            await _send_json(ws, {"type": "error", "code": "not_found"})
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        if user.consent_recording_ack_at is None:
            await _send_json(ws, {"type": "error", "code": "consent_required"})
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        glossary = user.pinned_vocabulary or []
        keyterms = [g["term"] for g in glossary if isinstance(g, dict) and g.get("term")]
        plan = user.plan
        user_id_str = str(user.id)
        break

    await _send_json(ws, {"type": "ready", "meeting_id": str(meeting_id)})

    translator = Translator(settings.anthropic_api_key)
    cancel_event = asyncio.Event()
    session_started_at = time.monotonic()

    recent_context: list[str] = []

    async def translate_and_emit(
        utterance_id: uuid.UUID, text: str, start_ms: int, end_ms: int
    ) -> None:
        start = time.monotonic()
        collected: list[str] = []
        try:
            async for delta, usage in translator.stream(
                text, source_lang, target_lang, glossary, recent_context
            ):
                if delta:
                    collected.append(delta)
                    await _send_json(
                        ws,
                        {
                            "type": "translation-delta",
                            "utterance_id": str(utterance_id),
                            "delta": delta,
                        },
                    )
                if usage is not None:
                    cost_cents = estimate_haiku_cost_cents(
                        usage.input_tokens, usage.output_tokens, usage.cached_tokens
                    )
                    latency_ms = int((time.monotonic() - start) * 1000)
                    log_translation(
                        settings,
                        user_id=user_id_str,
                        meeting_id=str(meeting_id),
                        source_lang=source_lang,
                        target_lang=target_lang,
                        input_tokens=usage.input_tokens,
                                                output_tokens=usage.output_tokens,
                        cached_tokens=usage.cached_tokens,
                        cost_cents=cost_cents,
                        latency_ms=latency_ms,
                    )
                    final_text = "".join(collected).strip()
                    # Persist translation
                    async for sess in get_session(settings):
                        u = await sess.get(Utterance, utterance_id)
                        if u is not None:
                            u.translated_text = final_text
                            m = await sess.get(Meeting, meeting_id)
                            if m is not None:
                                m.llm_cost_cents = (m.llm_cost_cents or 0) + cost_cents
                            await sess.commit()
                        break
                    await _send_json(
                        ws,
                        {
                            "type": "translation-done",
                            "utterance_id": str(utterance_id),
                            "text": final_text,
                            "start_ms": start_ms,
                            "end_ms": end_ms,
                        },
                    )
                    recent_context.append(f"{text} → {final_text}")
                    if len(recent_context) > 8:
                        del recent_context[: len(recent_context) - 8]
        except Exception as e:
            log.warning("translation_failed", error=str(e))
            await _send_json(
                ws,
                {
                    "type": "translation-failed",
                    "utterance_id": str(utterance_id),
                    "reason": "retry_available",
                },
            )

    async def run_deepgram(dg: DeepgramSession) -> None:
        translation_tasks: set[asyncio.Task[None]] = set()
        try:
            async for event in dg.events():
                if cancel_event.is_set():
                    break
                if not event.is_final:
                    await _send_json(
                        ws,
                        {
                            "type": "interim",
                            "speaker_id": event.speaker_id,
                            "text": event.text,
                            "start_ms": event.start_ms,
                            "end_ms": event.end_ms,
                        },
                    )
                    continue

                u = await _persist_utterance(
                    lambda: get_session(settings),
                    meeting_id,
                    {
                        "speaker_id": event.speaker_id,
                        "start_ms": event.start_ms,
                        "end_ms": event.end_ms,
                        "text": event.text,
                        "confidence": event.confidence,
                    },
                )
                await _send_json(
                    ws,
                    {
                        "type": "final",
                        "utterance_id": str(u.id),
                        "speaker_id": event.speaker_id,
                        "text": event.text,
                        "start_ms": event.start_ms,
                        "end_ms": event.end_ms,
                        "detected_language": event.detected_language,
                    },
                )
                task = asyncio.create_task(
                    translate_and_emit(u.id, event.text, event.start_ms, event.end_ms)
                )
                translation_tasks.add(task)
                task.add_done_callback(translation_tasks.discard)
        finally:
            if translation_tasks:
                await asyncio.gather(*translation_tasks, return_exceptions=True)

    async with DeepgramSession(
        settings.deepgram_api_key, language="multi", keyterms=keyterms
    ) as dg:
        dg_task = asyncio.create_task(run_deepgram(dg))
        audio_secs_this_batch = 0
        last_rate_check = time.monotonic()
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if "bytes" in msg and msg["bytes"] is not None:
                    await dg.send_audio(msg["bytes"])
                    audio_secs_this_batch += len(msg["bytes"]) / (16000 * 2)
                    # Every ~5s, increment usage counter + check rate limit
                    if time.monotonic() - last_rate_check > 5.0:
                        ok, _current, _limit = await check_and_increment(
                            redis, user_id_str, int(audio_secs_this_batch), plan, settings
                        )
                        audio_secs_this_batch = 0
                        last_rate_check = time.monotonic()
                        if not ok:
                            await _send_json(
                                ws, {"type": "error", "code": "rate_limit_exceeded"}
                            )
                            break
                elif "text" in msg and msg["text"] is not None:
                    try:
                        payload = json.loads(msg["text"])
                    except json.JSONDecodeError:
                        continue
                    if payload.get("type") == "end":
                        break
                    if payload.get("type") == "pause":
                        # Pause — client will stop sending audio until "resume"
                        continue
        except WebSocketDisconnect:
            pass
        finally:
            cancel_event.set()
            with contextlib.suppress(Exception):
                await dg.finalize()
            with contextlib.suppress(Exception):
                await asyncio.wait_for(dg_task, timeout=10.0)

            # Update meeting with duration and enqueue post-process
            duration_s = int(time.monotonic() - session_started_at)
            stt_cents = estimate_stt_cost_cents(duration_s)
            async for sess in get_session(settings):
                m = await sess.get(Meeting, meeting_id)
                if m is not None:
                    m.status = "processing"
                    m.duration_s = duration_s
                    m.stt_cost_cents = (m.stt_cost_cents or 0) + stt_cents
                    await sess.commit()
                break

            log_stt(
                settings,
                user_id=user_id_str,
                meeting_id=str(meeting_id),
                language=source_lang,
                duration_s=duration_s,
                cost_cents=stt_cents,
            )

            # Enqueue Celery post-processing
            try:
                from ..services.task_queue import enqueue_post_process

                enqueue_post_process(meeting_id=str(meeting_id))
            except Exception as e:
                log.error("enqueue_post_process_failed", error=str(e))

            with contextlib.suppress(Exception):
                await _send_json(ws, {"type": "ended", "duration_s": duration_s})
            with contextlib.suppress(Exception):
                await ws.close()
            await redis.close()
