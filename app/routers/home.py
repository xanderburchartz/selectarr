"""Home page — library statistics overview."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.config import get_config
from app.database import get_log_entries

router = APIRouter(tags=["home"])
from app.templates_env import templates

_STATS_TTL = 900  # 15 minutes
_stats_cache: list = []


def _fmt_date(iso: Optional[str]) -> Optional[str]:
    if not iso or iso.startswith("0001"):
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %-d, %Y")
    except Exception:
        return None


def _gb(b: int) -> float:
    return round(b / 1_073_741_824, 1)


def _human_space(b: int) -> str:
    """Format a byte count as a human-readable size (TB when >= 1 TB, else GB)."""
    gb = b / 1_073_741_824
    if gb >= 1024:
        return f"{gb / 1024:.1f} TB"
    return f"{gb:.1f} GB"


async def _fetch_movies(config) -> Optional[dict]:
    if not config.radarr:
        return None
    try:
        from app.services.radarr import RadarrService
        movies = await RadarrService(config.radarr.url, config.radarr.api_key).get_movies()
        downloaded = [m for m in movies if m.get("hasFile")]
        total = sum(m.get("sizeOnDisk", 0) or 0 for m in downloaded)
        dated = sorted(
            [m for m in downloaded if m.get("added") and not m["added"].startswith("0001")],
            key=lambda m: m["added"], reverse=True,
        )
        last = dated[0] if dated else None
        return {
            "count": len(downloaded),
            "size_gb": _gb(total),
            "last_added": {"title": f"{last['title']} ({last.get('year', '?')})", "date": _fmt_date(last["added"])} if last else None,
        }
    except Exception:
        return {"error": True}


async def _fetch_series(config) -> Optional[dict]:
    if not config.sonarr:
        return None
    try:
        from app.services.sonarr import SonarrService
        series = await SonarrService(config.sonarr.url, config.sonarr.api_key).get_series()
        total = sum(s.get("statistics", {}).get("sizeOnDisk", 0) or 0 for s in series)
        season_count = sum(
            len([sn for sn in s.get("seasons", [])
                 if sn.get("seasonNumber", 0) > 0
                 and sn.get("statistics", {}).get("episodeFileCount", 0) > 0])
            for s in series
        )
        ep_count = sum(s.get("statistics", {}).get("episodeFileCount", 0) for s in series)
        dated = sorted(
            [s for s in series if s.get("added") and not s["added"].startswith("0001")],
            key=lambda s: s["added"], reverse=True,
        )
        last = dated[0] if dated else None
        return {
            "count": len(series),
            "season_count": season_count,
            "episode_count": ep_count,
            "size_gb": _gb(total),
            "last_added": {"title": last["title"], "date": _fmt_date(last["added"])} if last else None,
        }
    except Exception:
        return {"error": True}


async def _fetch_music(config) -> Optional[dict]:
    if not config.lidarr:
        return None
    try:
        from app.services.lidarr import LidarrService
        svc = LidarrService(config.lidarr.url, config.lidarr.api_key)
        artists, all_albums = await asyncio.gather(svc.get_artists(), svc.get_all_albums())
        artists_with_files = [a for a in artists if a.get("statistics", {}).get("trackFileCount", 0) > 0]
        total = sum(a.get("statistics", {}).get("sizeOnDisk", 0) or 0 for a in artists_with_files)
        album_count = sum(
            1 for a in all_albums if a.get("statistics", {}).get("trackFileCount", 0) > 0
        )
        track_count = sum(a.get("statistics", {}).get("trackFileCount", 0) for a in artists_with_files)
        dated = sorted(
            [a for a in artists_with_files if a.get("added") and not a["added"].startswith("0001")],
            key=lambda a: a["added"], reverse=True,
        )
        last = dated[0] if dated else None
        return {
            "artist_count": len(artists_with_files),
            "album_count": album_count,
            "track_count": track_count,
            "size_gb": _gb(total),
            "last_added": {"title": last["artistName"], "date": _fmt_date(last["added"])} if last else None,
        }
    except Exception:
        return {"error": True}


async def _fetch_disk_space(config) -> Optional[dict]:
    """Aggregate free/total disk space across the configured *arr services.

    Mount points are de-duplicated by path so a drive shared by Radarr, Sonarr
    and Lidarr is only counted once. Returns None when no service reports space.
    """
    tasks = []
    if config.radarr:
        from app.services.radarr import RadarrService
        tasks.append(RadarrService(config.radarr.url, config.radarr.api_key).get_disk_space())
    if config.sonarr:
        from app.services.sonarr import SonarrService
        tasks.append(SonarrService(config.sonarr.url, config.sonarr.api_key).get_disk_space())
    if config.lidarr:
        from app.services.lidarr import LidarrService
        tasks.append(LidarrService(config.lidarr.url, config.lidarr.api_key).get_disk_space())
    if not tasks:
        return None

    results = await asyncio.gather(*tasks, return_exceptions=True)
    by_path: dict[str, tuple[int, int]] = {}
    for r in results:
        if isinstance(r, BaseException) or not r:
            continue
        for d in r:
            path = d.get("path")
            if path and path not in by_path:
                by_path[path] = (d.get("freeSpace", 0) or 0, d.get("totalSpace", 0) or 0)

    if not by_path:
        return None

    free = sum(v[0] for v in by_path.values())
    total = sum(v[1] for v in by_path.values())
    return {
        "free_human": _human_space(free),
        "total_human": _human_space(total),
        "used_pct": round((total - free) / total * 100) if total else 0,
    }


async def _fetch_last_deleted() -> dict:
    try:
        entries = await get_log_entries(limit=500)
        result: dict = {}
        for mt in ("movie", "series", "music"):
            last = next(
                (e for e in entries if e.media_type == mt and e.success and not e.dry_run and e.level != "refresh"),
                None,
            )
            result[mt] = {"title": last.title, "date": _fmt_date(last.timestamp)} if last else None
        return result
    except Exception:
        return {"movie": None, "series": None, "music": None}


def invalidate_stats_cache() -> None:
    """Drop the cached Overview stats so the next load recomputes from the *arr APIs.

    Called after a successful deletion so the library size and free disk space
    on the Overview reflect the change immediately, instead of after the TTL.
    """
    global _stats_cache
    _stats_cache = []


async def _build_stats(config, force: bool = False) -> dict:
    global _stats_cache
    if not force and _stats_cache and time.monotonic() - _stats_cache[0] < _STATS_TTL:
        return _stats_cache[1]

    movies, series, music, disk, last_del = await asyncio.gather(
        _fetch_movies(config),
        _fetch_series(config),
        _fetch_music(config),
        _fetch_disk_space(config),
        _fetch_last_deleted(),
    )

    if movies and not movies.get("error"):
        movies["last_deleted"] = last_del.get("movie")
    if series and not series.get("error"):
        series["last_deleted"] = last_del.get("series")
    if music and not music.get("error"):
        music["last_deleted"] = last_del.get("music")

    total_gb = round(sum(
        s.get("size_gb", 0) for s in [movies, series, music]
        if s and not s.get("error")
    ), 1)

    data = {"movies": movies, "series": series, "music": music, "total_gb": total_gb, "disk": disk}
    _stats_cache = [time.monotonic(), data]
    return data


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    config = get_config()
    stats = await _build_stats(config)
    return templates.TemplateResponse(request, "home.html", {"stats": stats})


@router.get("/stats", response_class=HTMLResponse)
async def stats_partial(request: Request, refresh: bool = False):
    config = get_config()
    stats = await _build_stats(config, force=refresh)
    return templates.TemplateResponse(request, "partials/stats.html", {"stats": stats})
