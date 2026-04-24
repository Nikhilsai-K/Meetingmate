# Observability & cost control

## What we track
- Every Deepgram session emits an event to Langfuse with `{model: nova-3, duration_s, cost_cents, meeting_id, language}`.
- Every Haiku translation emits a `generation` to Langfuse with input / output / cached tokens, cost cents, latency ms.
- Every Sonnet notes generation likewise (via the worker).
- Per-request logs (structlog JSON) include meeting_id, user_id, path, latency, status.
- Sentry captures exceptions in API, worker, web, and extension — with `send_default_pii=False` and transcript text stripped.

## Alerts

Configured in BetterStack / PagerDuty:
1. Any single user's daily cost > $5 — possible abuse or runaway integration.
2. `utterance_final → translation_done` p95 > 3 s over 5 min — degrades the hero UX.
3. Deepgram error rate > 2% over 5 min — fall back to Azure Speech automatically (see `deepgram_relay.py` TODO for the fallback wiring path).
4. Chrome Web Store star rating drops below 4.0 (scraped daily).
5. Any unhandled backend exception rate > 1/min.

## Budgets
- Per-user daily cost is computed from Langfuse events and summed in `usage_ledger`. Displayed to the user in the Settings tab.
- Org-level budget alert (AWS Budgets, Fly cost API) at 80% and 100% of monthly target.
