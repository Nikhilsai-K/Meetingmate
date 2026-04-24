"""OAuth-based integrations (Todoist / Notion / Google Tasks).

We store credentials encrypted in `integrations.credentials_encrypted` (AES-GCM).
On post-meeting completion, the worker pushes action items to active integrations.
"""

from __future__ import annotations

import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..core.crypto import encrypt
from ..db.models import Integration
from ..db.session import get_session
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


PROVIDER_CONFIG = {
    "todoist": {
        "authorize": "https://todoist.com/oauth/authorize",
        "token": "https://todoist.com/oauth/access_token",
        "scope": "data:read_write",
    },
    "notion": {
        "authorize": "https://api.notion.com/v1/oauth/authorize",
        "token": "https://api.notion.com/v1/oauth/token",
        "scope": "",
    },
    "google_tasks": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "scope": "https://www.googleapis.com/auth/tasks",
    },
}


def _creds(provider: str, settings: Settings) -> tuple[str, str]:
    if provider == "todoist":
        return settings.todoist_client_id or "", settings.todoist_client_secret or ""
    if provider == "notion":
        return settings.notion_client_id or "", settings.notion_client_secret or ""
    if provider == "google_tasks":
        return settings.google_client_id or "", settings.google_client_secret or ""
    raise HTTPException(400, "unknown_provider")


@router.get("")
async def list_integrations(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await get_or_create_user(session, auth)
    rows = (
        await session.execute(select(Integration).where(Integration.user_id == user.id))
    ).scalars().all()
    return {
        "items": [
            {"id": str(r.id), "provider": r.provider, "status": r.status, "config": r.config}
            for r in rows
        ]
    }


@router.post("/{provider}/oauth/start")
async def oauth_start(
    provider: str,
    auth: AuthContext = Depends(get_current_auth),
    settings: Settings = Depends(get_settings),
) -> dict:
    if provider not in PROVIDER_CONFIG:
        raise HTTPException(400, "unknown_provider")
    client_id, _ = _creds(provider, settings)
    if not client_id:
        raise HTTPException(503, "provider_not_configured")
    cfg = PROVIDER_CONFIG[provider]
    state = f"{auth.clerk_user_id}:{uuid.uuid4()}"
    params = {
        "client_id": client_id,
        "scope": cfg["scope"],
        "state": state,
        "redirect_uri": f"{settings.api_base_url}/v1/integrations/{provider}/oauth/callback",
        "response_type": "code",
    }
    return {"url": f"{cfg['authorize']}?{urlencode(params)}", "state": state}


@router.get("/{provider}/oauth/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if provider not in PROVIDER_CONFIG:
        raise HTTPException(400, "unknown_provider")
    client_id, client_secret = _creds(provider, settings)
    cfg = PROVIDER_CONFIG[provider]
    async with httpx.AsyncClient(timeout=10.0) as hc:
        resp = await hc.post(
            cfg["token"],
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": f"{settings.api_base_url}/v1/integrations/{provider}/oauth/callback",
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    clerk_user_id, _nonce = state.split(":", 1)
    from ..core.auth import AuthContext

    ctx = AuthContext(clerk_user_id=clerk_user_id, email=None, raw_claims={})
    user = await get_or_create_user(session, ctx)

    blob = encrypt(str(data).encode("utf-8"), settings.integration_credential_aes_key)

    # Upsert: one per provider per user
    existing = (
        await session.execute(
            select(Integration).where(
                Integration.user_id == user.id, Integration.provider == provider
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.credentials_encrypted = blob
        existing.status = "active"
    else:
        session.add(
            Integration(
                id=uuid.uuid4(),
                user_id=user.id,
                provider=provider,
                credentials_encrypted=blob,
                status="active",
            )
        )
    await session.commit()
    return RedirectResponse(f"{settings.web_base_url}/dashboard?integration={provider}")


@router.delete("/{integration_id}")
async def remove_integration(
    integration_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await get_or_create_user(session, auth)
    await session.execute(
        delete(Integration).where(
            Integration.id == integration_id, Integration.user_id == user.id
        )
    )
    await session.commit()
    return {"ok": True}
