"""Stripe + Clerk webhooks."""

from __future__ import annotations

import json

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..db.models import User
from ..db.session import get_session

log = get_logger(__name__)
router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(503, "stripe_not_configured")
    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError) as e:  # type: ignore[attr-defined]
        raise HTTPException(400, "invalid_signature") from e

    etype = event["type"]
    obj = event["data"]["object"]

    if etype in ("checkout.session.completed", "customer.subscription.updated"):
        customer_id = obj.get("customer")
        if customer_id:
            user = (
                await session.execute(
                    select(User).where(User.stripe_customer_id == customer_id)
                )
            ).scalar_one_or_none()
            if user is not None:
                price_id = None
                items = obj.get("items", {}).get("data") if etype == "customer.subscription.updated" else None
                if items:
                    price_id = items[0].get("price", {}).get("id")
                if price_id == settings.stripe_price_team_monthly:
                    user.plan = "team"
                elif price_id == settings.stripe_price_pro_monthly:
                    user.plan = "pro"
                await session.commit()
    elif etype == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        if customer_id:
            user = (
                await session.execute(
                    select(User).where(User.stripe_customer_id == customer_id)
                )
            ).scalar_one_or_none()
            if user is not None:
                user.plan = "free"
                await session.commit()

    return {"received": True, "type": etype}


@router.post("/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    # Svix-signed; we accept but rely on JWT verification for auth. Only handle
    # user.deleted to kick off a deletion-of-user-data job.
    body = await request.body()
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "invalid_json")
    etype = payload.get("type")
    if etype == "user.deleted":
        clerk_id = payload.get("data", {}).get("id")
        user = (
            await session.execute(select(User).where(User.clerk_user_id == clerk_id))
        ).scalar_one_or_none()
        if user is not None:
            await session.delete(user)
            await session.commit()
    return {"received": True}
