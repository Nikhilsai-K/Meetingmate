"""Nightly eval suite runner.

Loads the golden-set meetings from /infra/evals/golden/*.json, re-runs the pipeline
(notes generation + structural checks), then scores with Opus as judge.
Results posted to Langfuse + stored in a simple table for dashboarding.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from meetingmate.core.config import get_settings
from meetingmate.core.logging import get_logger
from meetingmate.services.langfuse_client import log_generic

from ..celery_app import app
from ..notes_generator import generate_notes

log = get_logger(__name__)

OPUS_JUDGE_MODEL = "claude-opus-4-7"


async def _run_eval() -> dict[str, Any]:
    settings = get_settings()
    golden_dir = Path(os.getenv("GOLDEN_DIR", "/app/infra/evals/golden"))
    if not golden_dir.exists():
        return {"ok": False, "reason": "no_golden_set"}

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    results: list[dict[str, Any]] = []

    for path in sorted(golden_dir.glob("*.json")):
        data = json.loads(path.read_text())
        transcript = data["utterances"]
        expected = data["expected_notes"]

        actual_pack = await generate_notes(
            settings,
            transcript,
            template=data.get("template", "default"),
            target_lang=data.get("target_lang", "en"),
        )
        actual = actual_pack["notes"]

        judge_prompt = (
            "You are grading a meeting-notes generator. Compare ACTUAL to EXPECTED. "
            "Score 0-100 per dimension, justify each in 1 sentence. Dimensions: "
            "summary_correctness, decisions_coverage, action_items_coverage, glossary_quality.\n\n"
            f"EXPECTED:\n{json.dumps(expected, ensure_ascii=False, indent=2)}\n\n"
            f"ACTUAL:\n{json.dumps(actual, ensure_ascii=False, indent=2)}\n\n"
            "Return ONLY JSON: {summary_correctness, decisions_coverage, "
            "action_items_coverage, glossary_quality, justifications}."
        )
        judge = await client.messages.create(
            model=OPUS_JUDGE_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": judge_prompt}],
        )
        text = "".join(b.text for b in judge.content if b.type == "text").strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
        try:
            score = json.loads(text)
        except json.JSONDecodeError:
            score = {"error": "judge_invalid_json"}

        results.append({"case": path.stem, "score": score})
        log_generic(
            settings,
            "eval.golden_set",
            {"case": path.stem, "score": score},
        )

    return {"ok": True, "results": results}


@app.task(name="meetingmate.run_eval_suite")
def run_eval_suite() -> dict[str, Any]:
    return asyncio.run(_run_eval())
