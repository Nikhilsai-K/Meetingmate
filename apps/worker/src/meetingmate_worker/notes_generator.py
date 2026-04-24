"""Structured notes generation with Claude Sonnet 4.6."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from anthropic import AsyncAnthropic
from meetingmate.core.config import Settings

SONNET_MODEL = "claude-sonnet-4-6"


TEMPLATE_INSTRUCTIONS = {
    "default": (
        "Produce a general-purpose meeting summary suited to any business meeting."
    ),
    "standup": (
        "Optimize for a daily standup. Group by person. Emphasize blockers and next-day plans."
    ),
    "one_on_one": (
        "Optimize for a 1:1. Emphasize feedback, growth topics, and followups between the two people."
    ),
    "client_call": (
        "Optimize for an external client call. Emphasize client asks, commitments, and next steps."
    ),
}


def _build_prompt(transcript: list[dict[str, Any]], template: str, target_lang: str) -> str:
    lines = []
    for u in transcript:
        ts = f"{u['start_ms'] // 60000:02d}:{(u['start_ms'] // 1000) % 60:02d}"
        speaker = u.get("speaker_name") or f"Speaker {u['speaker_id']}"
        lines.append(f"[{ts}] {speaker}: {u['original_text']}")
        if u.get("translated_text"):
            lines.append(f"    ({u['translated_text']})")
    body = "\n".join(lines)

    tmpl_note = TEMPLATE_INSTRUCTIONS.get(template, TEMPLATE_INSTRUCTIONS["default"])
    return (
        f"Write the notes in {target_lang}. {tmpl_note}\n\n"
        "Return JSON with keys: summary (1 paragraph, 3-5 sentences), "
        "decisions (list of strings), "
        "action_items (list of {owner, task, deadline}), "
        "open_questions (list of strings), "
        "glossary (list of {term, pronunciation, meaning, example}).\n\n"
        f"Transcript:\n{body}\n"
    )


async def generate_notes(
    settings: Settings,
    transcript: list[dict[str, Any]],
    template: str,
    target_lang: str,
) -> dict[str, Any]:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(transcript, template, target_lang)

    system = [
        {
            "type": "text",
            "text": (
                "You are an expert business-meeting note-taker. Be precise. "
                "Never invent attendees, decisions, or action items that are not clearly supported by the transcript. "
                "Respond with ONLY a valid JSON object (no prose, no markdown fence)."
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    resp = await client.messages.create(
        model=SONNET_MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")

    # Defensive: strip fences if any model added them despite instructions
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Retry once, asking to repair
        retry = await client.messages.create(
            model=SONNET_MODEL,
            max_tokens=4000,
            system=system,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": text},
                {"role": "user", "content": "The JSON above was invalid. Return ONLY valid JSON."},
            ],
        )
        text2 = "".join(b.text for b in retry.content if b.type == "text").strip().strip("`")
        parsed = json.loads(text2 if not text2.startswith("json") else text2[4:].strip())

    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cached_tokens": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
    }
    return {"notes": parsed, "usage": usage}


def run_generate_notes(
    settings: Settings,
    transcript: list[dict[str, Any]],
    template: str,
    target_lang: str,
) -> dict[str, Any]:
    return asyncio.run(generate_notes(settings, transcript, template, target_lang))
