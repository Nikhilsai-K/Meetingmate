"""FastAPI application entrypoint."""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from . import __version__
from .core.config import get_settings
from .core.logging import configure_logging, get_logger
from .db.session import init_engine
from .routers import (
    billing,
    chat,
    health,
    integrations,
    live_ws,
    meetings,
    search,
    usage,
    vocabulary,
    webhooks,
)

log = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration(transaction_style="endpoint")],
            traces_sample_rate=0.1,
            # Never capture request bodies (may contain transcript text)
            send_default_pii=False,
        )

    init_engine(settings)
    log.info("api_started", version=__version__, env=settings.environment)
    yield
    log.info("api_stopped")


def _cors_origin_check(origin: str) -> bool:
    # Accept chrome-extension://<id> for the published extension IDs + localhost.
    if origin.startswith("chrome-extension://"):
        return True
    return origin in get_settings().allowed_origins


app = FastAPI(
    title="MeetingMate API",
    version=__version__,
    docs_url="/v1/docs" if get_settings().environment != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(chrome-extension://[a-z0-9]+|https://meetingmate\.app|http://localhost:3000)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
    log.exception("unhandled_error", path=str(request.url.path))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "message": "We had trouble handling that request."},
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=()"
    return resp


app.include_router(health.router)
app.include_router(meetings.router)
app.include_router(chat.router)
app.include_router(vocabulary.router)
app.include_router(usage.router)
app.include_router(search.router)
app.include_router(billing.router)
app.include_router(integrations.router)
app.include_router(webhooks.router)
app.include_router(live_ws.router)
