# Architecture Decision Record

Key decisions made in Phase 1. Each decision is dated and labeled with its alternatives and rationale.

---

## ADR-001 — MV3 with `chrome.tabCapture` (not `getDisplayMedia`)
**Date:** 2026-01-10 · **Status:** Accepted

`chrome.tabCapture.capture()` is the only API that lets an extension silently capture a tab's audio after a single user gesture. `getDisplayMedia` would require the user to pick a tab every time from an OS-level picker — too much friction for a meeting assistant.

Constraint to live with: `tabCapture.capture()` must be called **synchronously** inside a user-gesture-originated message handler. The sidebar click is forwarded to the background service worker via `chrome.runtime.sendMessage`, which preserves the user-gesture context for Chrome.

---

## ADR-002 — Audio format: raw 16kHz PCM over WS (not Opus)
**Date:** 2026-01-11 · **Status:** Accepted

Deepgram Nova-3 accepts both, but streaming raw 16kHz mono Int16 PCM gives us:
- Deterministic frame timing (100ms = 3200 bytes).
- No encoder latency on the client.
- No ABI risk with Opus encoder deltas in different Chrome versions.

Cost: bandwidth. 32 kBps is trivial for the WebSocket path.

An `AudioWorklet` does the downsampling on the audio thread — the main thread is never blocked.

---

## ADR-003 — Direct Anthropic SDK, no LangChain
**Date:** 2026-01-12 · **Status:** Accepted

LangChain obscures prompt caching, streaming behavior, and retry semantics — all of which matter for our per-utterance Haiku translation (p95 < 2s). We call `anthropic.AsyncAnthropic` directly and use `messages.stream` for streaming, with `cache_control: ephemeral` on the system prompt.

---

## ADR-004 — Postgres RLS for tenant isolation
**Date:** 2026-01-12 · **Status:** Accepted

Every user-scoped table (`meetings`, `utterances`, `chat_messages`, `integrations`) has RLS policies that read `current_setting('app.user_id')`. The API sets the GUC at the start of every request-scoped session. Defense in depth: even a query-level bug cannot return another user's rows. A separate DB role `meetingmate_app` is used in production so the policies are actually enforced (superusers bypass RLS).

---

## ADR-005 — JWT via WebSocket subprotocol
**Date:** 2026-01-13 · **Status:** Accepted

Chrome extensions cannot set arbitrary headers on WebSocket handshakes. We pass the Clerk JWT as the `Sec-WebSocket-Protocol` subprotocol value `bearer.<jwt>`. The API reads both `meetingmate.v1` (to negotiate) and `bearer.<jwt>` (auth), validates the JWT, then accepts the connection with `meetingmate.v1` as the negotiated subprotocol.

---

## ADR-006 — Tokyo-primary for the API
**Date:** 2026-01-14 · **Status:** Accepted

Our primary user base is foreign workers in Japan — their Google Meet peers are in Japan. Deepgram has PoPs that service Tokyo with low RTT. Running the API in `nrt` (Fly) keeps the round-trip for audio frames and translation responses under 60ms intra-region.

---

## ADR-007 — Audio never persisted; only transcripts
**Date:** 2026-01-14 · **Status:** Accepted

Privacy positioning in Japanese corporate environments matters. We hold audio frames in memory strictly for the Deepgram relay and discard them within 60s of the final utterance being received. The `s3_bucket_transcripts` bucket has a bucket policy that rejects PUTs for any key outside `transcripts/**` (enforced by Terraform; absent here in the early scaffold but documented).

---

## ADR-008 — Separate worker process for post-meeting
**Date:** 2026-01-15 · **Status:** Accepted

Sonnet 4.6 notes generation can take ~15-30 seconds for a long meeting. We queue it to Celery immediately when the WebSocket closes and poll `/v1/meetings/:id` from the extension until `status='complete'`. This frees the API to service live meetings without head-of-line blocking.

---

## ADR-009 — Hybrid retrieval (BM25 + Qdrant) with Cohere rerank
**Date:** 2026-01-16 · **Status:** Accepted

BM25 (Postgres `tsvector`) is strong for quoted terms, personal names, numbers, acronyms — common in meeting chat queries. Dense embeddings (Voyage) handle paraphrased semantic queries. We run both, union, dedupe on utterance id, and rerank with Cohere `rerank-v3.5`. Fallback path: if Qdrant or Cohere are down, BM25 alone still serves usable results.

---

## ADR-010 — Golden-set evals nightly
**Date:** 2026-01-17 · **Status:** Accepted

Ten hand-curated Japanese meetings (varying speaker counts, speeds, background noise, code-switching levels) with known-correct action items, decisions, and glossary. Opus 4.7 judges actual vs. expected on four dimensions. Langfuse stores scores. A weekly drop > 5% pages the on-call.
