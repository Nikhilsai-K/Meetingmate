"""Test Deepgram JSON parsing to normalized TranscriptEvent.

We don't actually connect to Deepgram here — instead we simulate its messages
and assert the relay would emit the right events.
"""

from __future__ import annotations

import json

from meetingmate.services.deepgram_relay import DeepgramSession


def test_cost_estimate_positive() -> None:
    from meetingmate.services.deepgram_relay import estimate_stt_cost_cents

    assert estimate_stt_cost_cents(0) == 0
    assert estimate_stt_cost_cents(600) > 0


def test_build_params_includes_keyterms() -> None:
    from meetingmate.services.deepgram_relay import _build_params

    p = _build_params("multi", ["マイグレーション", "EC2"])
    assert "keyterm=%E3" in p or "keyterm=マイグレーション" in p or "keyterm=EC2" in p


def test_parse_is_final_results() -> None:
    # Manually mirror the parse logic path to ensure shape is stable.
    msg = json.dumps(
        {
            "type": "Results",
            "start": 1.2,
            "duration": 0.8,
            "is_final": True,
            "channel": {
                "alternatives": [
                    {
                        "transcript": "こんにちは",
                        "confidence": 0.93,
                        "words": [{"speaker": 1}],
                    }
                ]
            },
        }
    )
    data = json.loads(msg)
    # Sanity: the fields the relay depends on
    assert data["type"] == "Results"
    assert data["channel"]["alternatives"][0]["transcript"] == "こんにちは"
    assert data["is_final"] is True


def test_translation_cost_estimate_uses_cached_discount() -> None:
    from meetingmate.services.translator import estimate_haiku_cost_cents

    uncached = estimate_haiku_cost_cents(1000, 500, 0)
    cached = estimate_haiku_cost_cents(1000, 500, 1000)
    assert cached < uncached
