FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install API package (shared models/services) first
COPY apps/api /app/api
COPY apps/worker /app/worker

RUN pip install --upgrade pip hatchling && \
    pip install /app/api && \
    pip install /app/worker

ENV PYTHONPATH=/app/worker/src:/app/api/src

CMD ["celery", "-A", "meetingmate_worker.celery_app", "worker", "-l", "info", "-Q", "meetingmate", "-c", "4"]
