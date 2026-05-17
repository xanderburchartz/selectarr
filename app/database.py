"""SQLite activity log database using aiosqlite."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

from app.models import LogEntry

_DB_PATHS = [
    Path("/config/selectarr.db"),
    Path("./config/selectarr.db"),
    Path("./selectarr.db"),
]


def _get_db_path() -> Path:
    """Return the first writable database path."""
    for path in _DB_PATHS:
        if path.parent.exists():
            return path
    return _DB_PATHS[-1]


async def init_db() -> None:
    """Create the activity log table if it doesn't exist."""
    async with aiosqlite.connect(_get_db_path()) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                media_type TEXT NOT NULL,
                title TEXT NOT NULL,
                level TEXT NOT NULL,
                dry_run INTEGER NOT NULL,
                success INTEGER NOT NULL,
                details TEXT
            )
            """
        )
        await db.commit()


async def log_action(
    media_type: str,
    title: str,
    level: str,
    dry_run: bool,
    success: bool,
    details: Optional[str] = None,
) -> int:
    """Insert a deletion action into the activity log and return the new row id."""
    timestamp = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute(
            """
            INSERT INTO activity_log (timestamp, media_type, title, level, dry_run, success, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, media_type, title, level, int(dry_run), int(success), details),
        )
        await db.commit()
        return cursor.lastrowid


async def get_log_entries(limit: int = 200, offset: int = 0) -> list[LogEntry]:
    """Return recent activity log entries, newest first."""
    async with aiosqlite.connect(_get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM activity_log ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()

    return [
        LogEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            media_type=row["media_type"],
            title=row["title"],
            level=row["level"],
            dry_run=bool(row["dry_run"]),
            success=bool(row["success"]),
            details=row["details"],
        )
        for row in rows
    ]


async def clear_log() -> int:
    """Delete all log entries and return the number removed."""
    async with aiosqlite.connect(_get_db_path()) as db:
        cursor = await db.execute("DELETE FROM activity_log")
        await db.commit()
        return cursor.rowcount
