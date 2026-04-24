"""Deepgram Nova-3 streaming STT relay.

The relay sits between the extension WebSocket and Deepgram's WebSocket. We:
  - forward raw 16kHz mono PCM frames to Deepgram
  - parse Deepgram's JSON responses
  - emit normalized `TranscriptEvent` objects (interim + final) to the caller

Audio bytes are never written to disk and never logged. Langfuse receives only metadata
(duration, model, language, cost).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from ..core.logging import get_logger

log = get_logger(__name__)

DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


@dataclass(slots=True)
class TranscriptEvent:
    is_final: bool
    speaker_id: str
    start_ms: int
    end_ms: int
    text: str
    confidence: float
    detected_language: str | None


def _build_params(language: str, keyterms: list[str] | None) -> str:
    params: dict[str, Any] = {
        "model": "nova-3",
        "language": language or "multi",
        "smart_format": "true",
        "punctuate": "true",
        "diarize": "true",
        "interim_results": "true",
        "encoding": "linear16",
        "sample_rate": "16000",
        "channels": "1",
        "vad_events": "true",
        "endpointing": "300",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    if keyterms:
        # keyterm boosting for user's pinned vocabulary (STT custom vocab)
        for term in keyterms[:50]:
            query += f"&keyterm={term}"
    return query


class DeepgramSession:
    """One session per live meeting. Thread-safe for single-writer single-reader use."""

    def __init__(
        self,
        api_key: str,
        language: str = "multi",
        keyterms: list[str] | None = None,
    ) -> None:
        self.api_key = api_key
        self.language = language
        self.keyterms = keyterms or []
        self._ws: ClientConnection | None = None
        self._total_audio_ms = 0
        self._started_at: float | None = None

    async def __aenter__(self) -> DeepgramSession:
        url = f"{DEEPGRAM_WS_URL}?{_build_params(self.language, self.keyterms)}"
        self._ws = await websockets.connect(
            url,
            additional_headers={"Authorization": f"Token {self.api_key}"},
            max_size=2**23,
            ping_interval=5,
        )
        self._started_at = time.monotonic()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def send_audio(self, frame: bytes) -> None:
        if self._ws is None:
            raise RuntimeError("not connected")
        # 100ms @ 16kHz mono 16-bit = 3200 bytes
        if frame:
            self._total_audio_ms += int((len(frame) / 2) / 16)
        await self._ws.send(frame)

    async def finalize(self) -> None:
        if self._ws is None:
            return
        # Deepgram "CloseStream" control message to flush.
        await self._ws.send(json.dumps({"type": "CloseStream"}))

    async def close(self) -> None:
        if self._ws is not None:
            try:
                await self._ws.close()
            finally:
                self._ws = None

    @property
    def total_audio_ms(self) -> int:
        return self._total_audio_ms

    async def events(self) -> AsyncIterator[TranscriptEvent]:
        if self._ws is None:
            raise RuntimeError("not connected")
        async for msg in self._ws:
            if isinstance(msg, bytes):
                continue
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue

            if data.get("type") != "Results":
                continue

            channel = data.get("channel", {})
            alts = channel.get("alternatives") or []
            if not alts:
                continue
            alt = alts[0]
            text = (alt.get("transcript") or "").strip()
            if not text:
                continue

            words = alt.get("words") or []
            speaker_id = "0"
            if words and isinstance(words[0], dict):
                speaker_id = str(words[0].get("speaker", 0))

            start_s = float(data.get("start", 0.0))
            duration_s = float(data.get("duration", 0.0))
            conf = float(alt.get("confidence", 0.0))
            lang = alt.get("detected_language")
            is_final = bool(data.get("is_final"))

            yield TranscriptEvent(
                is_final=is_final,
                speaker_id=speaker_id,
                start_ms=int(start_s * 1000),
                end_ms=int((start_s + duration_s) * 1000),
                text=text,
                confidence=conf,
                detected_language=lang,
            )


def estimate_stt_cost_cents(duration_s: int) -> int:
    """Deepgram Nova-3 streaming pricing ~$0.0043/min. Return cents."""
    minutes = duration_s / 60.0
    return int(round(minutes * 0.43))


# Guard we expose so the WS handler can race against a cancellation.
async def consume_with_cancel(
    session: DeepgramSession, cancel_event: asyncio.Event
) -> AsyncIterator[TranscriptEvent]:
    iterator = session.events()
    while not cancel_event.is_set():
        try:
            next_event = asyncio.ensure_future(iterator.__anext__())
            done, _ = await asyncio.wait(
                {next_event, asyncio.ensure_future(cancel_event.wait())},
                return_when=asyncio.FIRST_COMPLETED,
                timeout=30,
            )
            if cancel_event.is_set():
                if not next_event.done():
                    next_event.cancel()
                return
            if next_event in done:
                yield next_event.result()
        except StopAsyncIteration:
            return
