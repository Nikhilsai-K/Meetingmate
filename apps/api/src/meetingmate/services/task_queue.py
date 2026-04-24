"""Thin Celery client used from FastAPI to enqueue jobs.

The actual worker lives in apps/worker; this module just knows the task name.
"""

from __future__ import annotations

from celery import Celery

from ..core.config import get_settings

_celery: Celery | None = None


def get_celery() -> Celery:
    global _celery
    if _celery is not None:
        return _celery
    settings = get_settings()
    app = Celery(
        "meetingmate",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )
    app.conf.task_default_queue = "meetingmate"
    _celery = app
    return app


def enqueue_post_process(meeting_id: str) -> None:
    app = get_celery()
    app.send_task("meetingmate.post_process_meeting", args=[meeting_id], queue="meetingmate")


def enqueue_push_integrations(meeting_id: str) -> None:
    app = get_celery()
    app.send_task("meetingmate.push_integrations", args=[meeting_id], queue="meetingmate")
