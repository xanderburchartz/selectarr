"""Activity log routes."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.database import clear_log, get_log_entries
from app.models import LogEntry

router = APIRouter(prefix="/logs", tags=["logs"])
from app.templates_env import templates


@router.get("", response_class=HTMLResponse)
async def logs_page(request: Request, limit: int = 200):
    """Activity log page."""
    entries = await get_log_entries(limit=limit)
    return templates.TemplateResponse(
        request, "logs.html", {"entries": entries, "limit": limit}
    )


@router.post("/clear", response_class=HTMLResponse)
async def logs_clear(request: Request):
    """Clear the activity log and refresh the log list."""
    count = await clear_log()
    entries = await get_log_entries()
    return templates.TemplateResponse(
        request, "partials/logs_list.html", {"entries": entries, "cleared": count}
    )


@router.get("/api", summary="List activity log entries")
async def api_logs(limit: int = 200, offset: int = 0) -> list[LogEntry]:
    """Return recent activity log entries."""
    return await get_log_entries(limit=limit, offset=offset)
