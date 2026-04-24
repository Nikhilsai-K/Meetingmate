"""Celery app. Task modules are auto-imported here."""

from __future__ import annotations

from celery import Celery
from meetingmate.core.config import get_settings
from meetingmate.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = Celery(
    "meetingmate_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "meetingmate_worker.tasks.post_process",
        "meetingmate_worker.tasks.integrations_sync",
        "meetingmate_worker.tasks.eval_runner",
    ],
)
app.conf.task_default_queue = "meetingmate"
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_soft_time_limit = 60 * 10
app.conf.task_time_limit = 60 * 15
