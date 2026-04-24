"""Push action items to external task managers."""

from __future__ import annotations

import asyncio
import ast
import uuid
from typing import Any

import httpx
from meetingmate.core.config import get_settings
from meetingmate.core.crypto import decrypt
from meetingmate.core.logging import get_logger
from meetingmate.db.models import Integration, Meeting
from meetingmate.db.session import get_session, init_engine
from sqlalchemy import select

from ..celery_app import app

log = get_logger(__name__)


def _decode_creds(blob: bytes, key_hex: str) -> dict[str, Any]:
    raw = decrypt(blob, key_hex).decode("utf-8")
    try:
        return ast.literal_eval(raw) if raw.startswith("{") else {}
    except (ValueError, SyntaxError):
        return {}


async def _push_todoist(creds: dict[str, Any], items: list[dict]) -> int:
    token = creds.get("access_token")
    if not token:
        return 0
    async with httpx.AsyncClient(timeout=10.0) as hc:
        count = 0
        for it in items:
            resp = await hc.post(
                "https://api.todoist.com/rest/v2/tasks",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "content": it.get("task", "Action item"),
                    "description": f"Owner: {it.get('owner', '')}",
                    "due_string": it.get("deadline") or "",
                },
            )
            if resp.status_code < 300:
                count += 1
    return count


async def _push_notion(creds: dict[str, Any], items: list[dict], database_id: str | None) -> int:
    token = creds.get("access_token")
    if not token or not database_id:
        return 0
    async with httpx.AsyncClient(timeout=10.0) as hc:
        count = 0
        for it in items:
            resp = await hc.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                },
                json={
                    "parent": {"database_id": database_id},
                    "properties": {
                        "Name": {"title": [{"text": {"content": it.get("task", "Action item")}}]}
                    },
                },
            )
            if resp.status_code < 300:
                count += 1
    return count


async def _push_google_tasks(creds: dict[str, Any], items: list[dict]) -> int:
    token = creds.get("access_token")
    if not token:
        return 0
    async with httpx.AsyncClient(timeout=10.0) as hc:
        lists = await hc.get(
            "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
            headers={"Authorization": f"Bearer {token}"},
        )
        if lists.status_code >= 300 or not lists.json().get("items"):
            return 0
        list_id = lists.json()["items"][0]["id"]
        count = 0
        for it in items:
            resp = await hc.post(
                f"https://tasks.googleapis.com/tasks/v1/lists/{list_id}/tasks",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": it.get("task", "Action item"),
                    "notes": f"Owner: {it.get('owner', '')}",
                },
            )
            if resp.status_code < 300:
                count += 1
    return count


async def _run(meeting_id: str) -> dict[str, Any]:
    settings = get_settings()
    init_engine(settings)
    mid = uuid.UUID(meeting_id)

    async for session in get_session(settings):
        m = await session.get(Meeting, mid)
        if m is None or not m.action_items:
            return {"ok": True, "pushed": 0}
        user_id = m.user_id
        integrations = (
            (
                await session.execute(
                    select(Integration).where(
                        Integration.user_id == user_id, Integration.status == "active"
                    )
                )
            )
            .scalars()
            .all()
        )
        pushed = 0
        for integ in integrations:
            try:
                creds = _decode_creds(
                    integ.credentials_encrypted, settings.integration_credential_aes_key
                )
                if integ.provider == "todoist":
                    pushed += await _push_todoist(creds, m.action_items)
                elif integ.provider == "notion":
                    db_id = (integ.config or {}).get("database_id")
                    pushed += await _push_notion(creds, m.action_items, db_id)
                elif integ.provider == "google_tasks":
                    pushed += await _push_google_tasks(creds, m.action_items)
            except Exception as e:
                log.warning(
                    "integration_push_failed", provider=integ.provider, error=str(e)
                )
        break
    return {"ok": True, "pushed": pushed}


@app.task(name="meetingmate.push_integrations", max_retries=2, default_retry_delay=60)
def push_action_items(meeting_id: str) -> dict[str, Any]:
    return asyncio.run(_run(meeting_id))
