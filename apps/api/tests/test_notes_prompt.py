"""Test the notes generation prompt builder is stable (structure only)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the worker src to path so we can import notes_generator under pytest.
# Resolve relative to this file rather than cwd so it works from any invocation.
_WORKER_SRC = (Path(__file__).parent.parent.parent / "worker" / "src").resolve()
if _WORKER_SRC.is_dir():
    sys.path.insert(0, str(_WORKER_SRC))

import pytest

pytest.importorskip("meetingmate_worker.notes_generator")

from meetingmate_worker.notes_generator import _build_prompt  # noqa: E402


def test_prompt_includes_template_and_transcript() -> None:
    transcript = [
        {
            "speaker_id": "0",
            "speaker_name": "Vikram",
            "start_ms": 0,
            "end_ms": 1200,
            "original_text": "こんにちは",
            "translated_text": "Hello",
        }
    ]
    out = _build_prompt(transcript, "standup", "en")
    assert "standup" in out.lower() or "daily standup" in out.lower()
    assert "こんにちは" in out
    assert "Hello" in out
    assert "JSON" in out
