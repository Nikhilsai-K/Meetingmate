FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip hatchling && \
    pip install .

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
ENV PYTHONPATH=/app/src

EXPOSE 8000
CMD ["uvicorn", "meetingmate.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
