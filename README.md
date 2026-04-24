# MeetingMate

Live translation + AI notes for Google Meet. Chromium extension (Manifest V3) + FastAPI backend + Celery worker + Next.js web dashboard.

> **Status.** This repository contains the Phase-1 production foundation: scaffolded monorepo, MV3 extension (service worker + content script + sidebar React app + AudioWorklet), FastAPI API (auth, live WebSocket audio relay, Deepgram Nova-3 STT integration, Haiku translation with prompt caching, chat RAG, search, vocabulary, billing, Stripe/Clerk webhooks, integrations OAuth), Celery worker (post-meeting notes generation with Sonnet 4.6, embeddings to Qdrant, action-item sync to Todoist/Notion/Google Tasks, golden-set eval suite), Postgres schema with RLS, Alembic migrations, Next.js landing/privacy/terms/pricing/dashboard, Docker Compose dev stack, CI workflows, tests, and docs.
>
> Phases 2-4 (speaker-name mapping, meeting templates, search polish, team tier, Zoom/Teams support, additional languages) are laid out in [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Quick start

```bash
# 1. install deps
pnpm install
python3 -m pip install -e 'apps/api[dev]'
python3 -m pip install -e apps/worker

# 2. start local infra (Postgres, Redis, Qdrant, MinIO, Langfuse)
cp .env.example .env
pnpm docker:up

# 3. migrate + seed
pnpm db:migrate

# 4. run everything
pnpm --filter @meetingmate/api dev       # :8000
pnpm --filter @meetingmate/web dev       # :3000
pnpm --filter @meetingmate/extension dev # HMR-built extension in apps/extension/dist
cd apps/worker && celery -A meetingmate_worker.celery_app worker -l info -Q meetingmate
```

Load the unpacked extension from `apps/extension/dist` in `chrome://extensions` (Developer mode ON).

## Architecture

See [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) for the "why" and [`docs/PERMISSIONS.md`](docs/PERMISSIONS.md) for Chrome Web Store permission justifications.

## Layout

```
apps/
  extension/   Chromium MV3 extension (React sidebar, AudioWorklet, WS client)
  api/         FastAPI — auth, WS relay, meetings, chat, search, billing, webhooks
  worker/      Celery — post-meeting notes, embeddings, integrations sync, evals
  web/         Next.js — landing, pricing, privacy, terms, dashboard
packages/
  shared-types/  cross-workspace TypeScript types
infra/
  fly/         Fly.io app configs (api + worker, both Tokyo)
  terraform/   IaC module definitions
  postgres/    init SQL (extensions + roles)
  evals/       golden-set meetings for nightly eval
docs/          architecture, permissions, Chrome Web Store listing, roadmap
.github/       CI/CD workflows
```

## License

Proprietary — © MeetingMate.
