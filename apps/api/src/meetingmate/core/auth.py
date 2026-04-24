"""Clerk JWT verification.

Clerk issues short-lived JWTs signed with RS256 using keys published at a JWKS URL.
We cache the JWKS for 60s and verify iss + exp + signature on every request.

For the WebSocket endpoint the JWT is passed via the `Sec-WebSocket-Protocol`
subprotocol (Chrome extensions cannot add arbitrary headers to WS handshakes).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from .config import Settings, get_settings
from .logging import get_logger

log = get_logger(__name__)

_jwks_cache: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL_SECONDS = 60.0

security_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthContext:
    clerk_user_id: str
    email: str | None
    raw_claims: dict[str, Any]


async def _load_jwks(url: str) -> list[dict[str, Any]]:
    now = time.monotonic()
    if _jwks_cache["keys"] is not None and now - _jwks_cache["fetched_at"] < _JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]  # type: ignore[return-value]
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    _jwks_cache["keys"] = data.get("keys", [])
    _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]  # type: ignore[return-value]


async def verify_clerk_jwt(token: str, settings: Settings) -> AuthContext:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid token header") from e

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing kid")

    keys = await _load_jwks(settings.clerk_jwks_url)
    key = next((k for k in keys if k.get("kid") == kid), None)
    if key is None:
        # Rotate: force refresh
        _jwks_cache["fetched_at"] = 0.0
        keys = await _load_jwks(settings.clerk_jwks_url)
        key = next((k for k in keys if k.get("kid") == kid), None)
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="unknown kid")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}") from e

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing sub")

    return AuthContext(
        clerk_user_id=str(sub),
        email=claims.get("email"),
        raw_claims=claims,
    )


async def get_current_auth(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    if creds is None or not creds.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    ctx = await verify_clerk_jwt(creds.credentials, settings)
    # Stash on request state so middleware / logs can pick it up
    request.state.clerk_user_id = ctx.clerk_user_id
    return ctx
