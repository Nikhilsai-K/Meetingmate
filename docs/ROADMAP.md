# Roadmap

## Phase 1 — Launchable MVP (in this repo)
Foundation delivered: MV3 extension, FastAPI backend, Celery worker, Next.js web, Postgres schema with RLS, Alembic migrations, docker-compose dev stack, CI, tests, docs.

Remaining Phase-1 work to ship publicly:
- [ ] Rasterize `public/icons/icon.svg` → 16/32/48/128 PNGs (one-shot `sharp-cli` command).
- [ ] Fill `.env` with real Clerk + Deepgram + Anthropic + Voyage + Cohere + Stripe keys.
- [ ] Deploy API + worker to Fly (`fly launch` then `flyctl secrets set` for the env vars).
- [ ] Deploy web to Vercel.
- [ ] Produce 5 screenshots + 30s promo video per `docs/store_listing.md`.
- [ ] Submit to Chrome Web Store (targets Chrome + Edge + Brave).

## Phase 2 — Daily-driver polish
- Speaker name mapping via Meet DOM scraping (already scaffolded in `content-script.ts`; the wiring to match diarized speaker IDs to names is the missing step).
- Meeting templates (standup / 1:1 / client — already supported in notes prompt).
- PDF export via `reportlab` (worker dependency already added).
- Notion / Todoist one-click export in the sidebar (API already pushes on meeting end via integrations).
- Full-text search UI in the web dashboard.
- Keyboard shortcut to "mark important" (already wired — ⌘⇧I).

## Phase 3 — Intelligence + paid tier
- Pre-meeting briefs via Google Calendar OAuth (integrations scaffolding already present; scope add + Calendar read are the incremental work).
- Personal glossary + spaced-repetition retention view in the dashboard.
- Stripe Checkout + Customer Portal (already wired server-side; needs UI polish).
- Admin console for Team tier.

## Phase 4 — Expansion
- Additional source/target languages: Korean, Chinese, Spanish, French, German. All pipeline code is language-agnostic — add options to the language picker + Voyage supports multilingual embeddings.
- Zoom support: detect `zoom.us/j/*` URLs, same audio pipeline, different launcher placement heuristics.
- MS Teams support: similar to Zoom but in-browser experience is `teams.microsoft.com`.
- Public launch: Product Hunt, r/japanlife, r/japanresidents, r/movingtojapan, expat Slack/Discord.
