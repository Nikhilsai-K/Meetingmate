"""Per-utterance translation with Claude Haiku 4.5, streaming tokens back.

- System prompt is prompt-cached (user glossary + instructions).
- Anthropic SDK direct usage; no LangChain.
- Emits token deltas as they arrive.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from ..core.logging import get_logger

log = get_logger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"

LANGUAGE_NAMES = {
    "ja": "Japanese",
    "en": "English",
    "ko": "Korean",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


@dataclass(slots=True)
class TranslationUsage:
    input_tokens: int
    output_tokens: int
    cached_tokens: int


def _system_prompt(
    source_lang: str,
    target_lang: str,
    glossary: list[dict],
    recent_context: list[str],
) -> list[dict]:
    src = LANGUAGE_NAMES.get(source_lang, source_lang)
    tgt = LANGUAGE_NAMES.get(target_lang, target_lang)
    glossary_lines = "\n".join(
        f"- {g.get('term', '')}: {g.get('translation', '')}" for g in glossary[:50]
    ) or "(none)"
    context = "\n".join(recent_context[-5:]) or "(start of meeting)"
    return [
        {
            "type": "text",
            "text": (
                f"You are a professional real-time interpreter translating {src} into {tgt} "
                "for a business meeting. Rules:\n"
                "- Translate faithfully; preserve technical terms, names, numbers.\n"
                "- Do NOT summarize, interpret motives, or add commentary.\n"
                "- Keep the same speaker register (polite/formal/casual).\n"
                "- If the utterance is already in the target language, output it verbatim.\n"
                "- If the utterance is a partial/unclear fragment, output the best literal rendering without hedging.\n\n"
                f"User glossary (always honor these mappings):\n{glossary_lines}\n"
            ),
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": f"Recent meeting context (previous utterances, already translated):\n{context}",
        },
    ]


class Translator:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)

    async def stream(
        self,
        utterance: str,
        source_lang: str,
        target_lang: str,
        glossary: list[dict],
        recent_context: list[str],
    ) -> AsyncIterator[tuple[str, TranslationUsage | None]]:
        system = _system_prompt(source_lang, target_lang, glossary, recent_context)
        usage: TranslationUsage | None = None
        async with self._client.messages.stream(
            model=HAIKU_MODEL,
            max_tokens=600,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": f"Translate this utterance to {LANGUAGE_NAMES.get(target_lang, target_lang)}:\n\n{utterance}",
                }
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text, None
            final = await stream.get_final_message()
            usage = TranslationUsage(
                input_tokens=final.usage.input_tokens,
                output_tokens=final.usage.output_tokens,
                cached_tokens=getattr(final.usage, "cache_read_input_tokens", 0) or 0,
            )
        yield "", usage


def estimate_haiku_cost_cents(input_tokens: int, output_tokens: int, cached_tokens: int) -> int:
    """Claude Haiku 4.5 pricing (per 1M tokens): ~$1 input, $5 output, $0.1 cached."""
    uncached_in = max(0, input_tokens - cached_tokens)
    cost_usd = (
        uncached_in / 1_000_000 * 1.00
        + cached_tokens / 1_000_000 * 0.10
        + output_tokens / 1_000_000 * 5.00
    )
    return int(round(cost_usd * 100))
