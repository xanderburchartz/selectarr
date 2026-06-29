"""In-memory session management."""
from __future__ import annotations

import secrets
import time
from typing import Optional

_SESSION_TTL = 24 * 3600  # 1 day
_COOKIE = "selectarr_session"

_sessions: dict[str, dict] = {}


def create_session(user_id: str, username: str, is_admin: bool, jellyfin_token: str) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = {
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
        "jellyfin_token": jellyfin_token,
        "created_at": time.monotonic(),
    }
    return token


def get_session(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    session = _sessions.get(token)
    if not session:
        return None
    if time.monotonic() - session["created_at"] > _SESSION_TTL:
        del _sessions[token]
        return None
    return session


def delete_session(token: str) -> None:
    _sessions.pop(token, None)
