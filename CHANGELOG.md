# Changelog

All notable changes to MeetingMate are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to [SemVer](https://semver.org/).

## [Unreleased]
### Added
- Phase-1 foundation: MV3 extension (service worker + content script + sidebar React + AudioWorklet), FastAPI backend (Clerk auth, WS audio relay, Deepgram Nova-3 STT, Haiku translation streaming, chat RAG with citation validation, hybrid search, vocabulary, billing, webhooks, integrations OAuth), Celery worker (Sonnet 4.6 notes, Voyage embeddings → Qdrant, integrations sync, nightly golden-set eval), Next.js web dashboard (landing, pricing, privacy, terms, dashboard), Postgres schema with row-level security, Alembic migration, docker-compose dev stack, Fly.io production configs, GitHub Actions CI/CD, pytest + Vitest + Playwright tests, and complete Chrome Web Store documentation.
