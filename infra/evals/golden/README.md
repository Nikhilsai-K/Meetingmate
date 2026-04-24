# Golden set

Ten hand-curated Japanese business meetings used by the nightly eval in `apps/worker/src/meetingmate_worker/tasks/eval_runner.py`.

Each `*.json` file contains:

```json
{
  "template": "default | standup | one_on_one | client_call",
  "target_lang": "en",
  "utterances": [
    {
      "speaker_id": "0",
      "speaker_name": "Takashi",
      "start_ms": 0,
      "end_ms": 3200,
      "original_text": "...",
      "translated_text": "..."
    }
  ],
  "expected_notes": {
    "summary": "...",
    "decisions": [...],
    "action_items": [...],
    "glossary": [...]
  }
}
```

The eval task embeds no fixture audio — we assume transcription is already correct for the golden set, because we're specifically grading the notes-generation path.

A tiny placeholder is included so the runner succeeds in CI. Replace with real transcripts before enabling the nightly schedule.
