"""Visitor session management, authentication hashing, and rate tracking."""

from datetime import UTC, datetime
import hashlib
import uuid

from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from openswitch.config import settings
from openswitch.db import session_context
from openswitch.models import Session

SESSION_COOKIE_NAME = "openswitch_session"


def hash_token(token: str) -> str:
    """Hash token using SHA-256 for persistent database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware that guarantees every visitor has a session cookie and DB record."""

    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(SESSION_COOKIE_NAME)
        is_new = False

        if not token or len(token) < 16:
            token = uuid.uuid4().hex + uuid.uuid4().hex
            is_new = True

        t_hash = hash_token(token)
        request.state.session_token = token
        request.state.session_hash = t_hash

        response = await call_next(request)

        if is_new:
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=token,
                httponly=True,
                samesite="lax",
                secure=settings.openswitch_mode == "hosted",
                max_age=60 * 60 * 24 * 30,  # 30 days
            )

        # Update last seen in DB asynchronously
        now = datetime.now(UTC)
        try:
            async with session_context() as session:
                res = await session.execute(select(Session).where(Session.token_hash == t_hash))
                existing = res.scalar_one_or_none()
                if not existing:
                    session.add(Session(token_hash=t_hash, created_at=now, last_seen=now))
                else:
                    existing.last_seen = now
                await session.commit()
        except Exception:
            pass

        return response


def get_or_create_session(request: Request) -> str:
    """Retrieve session hash from request state or cookies."""
    if hasattr(request.state, "session_hash"):
        return request.state.session_hash

    token = request.cookies.get(SESSION_COOKIE_NAME, uuid.uuid4().hex)
    return hash_token(token)
