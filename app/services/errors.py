"""Shared utilities for classifying and displaying external-service errors."""
from __future__ import annotations

import httpx


class ServiceError(Exception):
    """Raised when an external *arr service is unavailable or returns an error.

    Carries a user-friendly message suitable for display in the UI.
    """


def classify_error(service: str, exc: Exception) -> str:
    """Convert an httpx (or other) exception into a one-line friendly message."""
    if isinstance(exc, httpx.ConnectError):
        return (
            f"Could not connect to {service}. "
            "Check your settings or verify the service is running."
        )
    if isinstance(exc, httpx.TimeoutException):
        return (
            f"Connection to {service} timed out. "
            "The service may be slow or unreachable."
        )
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        if code == 401:
            return f"Invalid API key for {service}. Update it in Settings."
        if code == 403:
            return f"Access denied by {service}. Check your API key permissions."
        return f"{service} returned an unexpected error (HTTP {code})."
    return f"Could not reach {service}: {type(exc).__name__}"


def error_html(message: str) -> str:
    """Return a self-contained HTML error block for inline / HTMX responses."""
    return (
        '<div style="background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;'
        'padding:1rem 1.25rem;border-radius:6px;margin:0.5rem 0;">'
        "<strong>&#9888; Service unavailable</strong><br>"
        f"{message}<br>"
        '<small style="margin-top:0.5rem;display:inline-block;">'
        '<a href="/settings">Check Settings &rarr;</a></small>'
        "</div>"
    )
