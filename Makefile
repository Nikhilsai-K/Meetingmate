.PHONY: dev up down logs migrate api worker web ext test lint

up:
	pnpm docker:up

down:
	pnpm docker:down

logs:
	pnpm docker:logs

migrate:
	cd apps/api && alembic upgrade head

api:
	cd apps/api && uvicorn meetingmate.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd apps/worker && celery -A meetingmate_worker.celery_app worker -l info -Q meetingmate

web:
	pnpm --filter @meetingmate/web dev

ext:
	pnpm --filter @meetingmate/extension dev

test:
	cd apps/api && pytest
	pnpm --filter @meetingmate/extension test

lint:
	cd apps/api && ruff check src tests
	pnpm lint
