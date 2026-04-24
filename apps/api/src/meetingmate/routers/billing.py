"""Stripe Checkout + Customer Portal."""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException

from ..core.auth import AuthContext, get_current_auth
from ..core.config import Settings, get_settings
from ..db.session import get_session
from ..services.users import get_or_create_user

router = APIRouter(prefix="/v1/billing", tags=["billing"])


@router.post("/checkout")
async def create_checkout(
    body: dict,
    auth: AuthContext = Depends(get_current_auth),
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not settings.stripe_secret_key:
        raise HTTPException(503, "stripe_not_configured")
    stripe.api_key = settings.stripe_secret_key
    user = await get_or_create_user(session, auth)

    tier = body.get("tier", "pro")
    if tier == "pro":
        price_id = settings.stripe_price_pro_monthly
    elif tier == "team":
        price_id = settings.stripe_price_team_monthly
    else:
        raise HTTPException(400, "invalid_tier")
    if not price_id:
        raise HTTPException(503, "price_not_configured")

    if not user.stripe_customer_id:
        cust = stripe.Customer.create(email=user.email, metadata={"user_id": str(user.id)})
        user.stripe_customer_id = cust.id
        await session.commit()

    checkout = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.web_base_url}/dashboard?upgraded=1",
        cancel_url=f"{settings.web_base_url}/pricing",
        allow_promotion_codes=True,
    )
    return {"url": checkout.url}


@router.post("/portal")
async def create_portal(
    auth: AuthContext = Depends(get_current_auth),
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    if not settings.stripe_secret_key:
        raise HTTPException(503, "stripe_not_configured")
    stripe.api_key = settings.stripe_secret_key
    user = await get_or_create_user(session, auth)
    if not user.stripe_customer_id:
        raise HTTPException(400, "no_customer")
    portal = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.web_base_url}/dashboard",
    )
    return {"url": portal.url}
