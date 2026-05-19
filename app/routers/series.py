"""Series routes: browsing, season/episode expansion, confirmation, and deletion."""
from __future__ import annotations

from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse

from app.config import get_config
from app.database import log_action
from app.models import (
    DeleteResult,
    DeleteResultItem,
    EpisodeItem,
    SeasonItem,
    SeriesItem,
)
from app.services.errors import ServiceError, classify_error, error_html
from app.services.jellyfin import JellyfinService, make_watch_status_builder
from app.services.sonarr import SonarrService

router = APIRouter(prefix="/series", tags=["series"])
from app.templates_env import templates


async def _refresh_after_series_delete(config, sonarr_id: int, title: str) -> None:
    sonarr = SonarrService(config.sonarr.url, config.sonarr.api_key)
    try:
        await sonarr.rescan_series(sonarr_id)
        await log_action("series", title, "refresh", dry_run=False, success=True, details="Sonarr: RescanSeries")
    except Exception as exc:
        await log_action("series", title, "refresh", dry_run=False, success=False, details=f"Sonarr: {exc}")

    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    try:
        await jf.refresh_library()
        await log_action("series", "Jellyfin library", "refresh", dry_run=False, success=True, details="Jellyfin: library refresh")
    except Exception as exc:
        await log_action("series", "Jellyfin library", "refresh", dry_run=False, success=False, details=f"Jellyfin: {exc}")

FILTER_OPTIONS = [
    ("all", "Show all"),
    ("watched_all", "Watched by all users"),
    ("watched_any", "Watched by at least one user"),
    ("unwatched", "Not watched by anyone"),
    ("watched_by_user", "Watched by specific user"),
]


def _get_services(config=None):
    if config is None:
        config = get_config()
    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    sonarr = SonarrService(config.sonarr.url, config.sonarr.api_key) if config.sonarr else None
    return jf, sonarr


def _build_series_item(
    s: dict,
    per_user: dict[str, bool],
    partial_per_user: dict[str, bool],
    build_ws,
) -> SeriesItem:
    """Convert a raw Sonarr series dict to a SeriesItem."""
    seasons = []
    for season in s.get("seasons", []):
        sn = season.get("seasonNumber", 0)
        if sn == 0:
            continue
        stats = season.get("statistics", {})
        seasons.append(
            SeasonItem(
                number=sn,
                episode_count=stats.get("totalEpisodeCount", 0),
                episode_file_count=stats.get("episodeFileCount", 0),
                watch_status=None,
            )
        )
    seasons.sort(key=lambda x: x.number)

    stats = s.get("statistics", {})
    return SeriesItem(
        sonarr_id=s["id"],
        title=s["title"],
        year=s.get("year", 0),
        tvdb_id=s.get("tvdbId"),
        has_files=stats.get("episodeFileCount", 0) > 0,
        total_size_bytes=stats.get("sizeOnDisk", 0),
        watch_status=build_ws(per_user, partial_per_user) if per_user is not None else None,
        seasons=seasons,
    )


async def _build_series_list(
    filter_type: str,
    filter_user_id: Optional[str],
    config=None,
) -> tuple[list[SeriesItem], list, list, Optional[str]]:
    """Fetch and filter series.

    Returns (series, users, filter_options, jellyfin_warning).
    Jellyfin failures degrade gracefully. Sonarr failures raise ServiceError.
    """
    if config is None:
        config = get_config()

    jf, sonarr = _get_services(config)

    jellyfin_warning: Optional[str] = None
    try:
        users = await jf.get_users()
        watch_map = await jf.build_series_watch_map(users)
        partial_map = await jf.build_series_partial_map(users)
    except httpx.HTTPError as exc:
        users = []
        watch_map = {}
        partial_map = {}
        jellyfin_warning = classify_error("Jellyfin", exc)

    build_ws = make_watch_status_builder(users)
    user_ids = [u.id for u in users]

    try:
        raw_series = await sonarr.get_series() if sonarr else []
    except httpx.HTTPError as exc:
        raise ServiceError(classify_error("Sonarr", exc)) from exc

    result = []
    for s in raw_series:
        tvdb_id = str(s.get("tvdbId", "")) or None
        per_user = watch_map.get(tvdb_id, {}) if tvdb_id else {}
        partial_per_user = partial_map.get(tvdb_id, {}) if tvdb_id else {}
        watched = [per_user.get(uid, False) for uid in user_ids]

        if filter_type == "watched_all" and (not user_ids or not all(watched)):
            continue
        if filter_type == "watched_any" and not any(watched):
            continue
        if filter_type == "unwatched" and any(watched):
            continue
        if filter_type == "watched_by_user" and filter_user_id:
            if not per_user.get(filter_user_id, False):
                continue

        result.append(_build_series_item(s, per_user, partial_per_user, build_ws))

    result.sort(key=lambda s: s.title.lower())
    return result, users, FILTER_OPTIONS, jellyfin_warning


def _apply_user_defaults(request: Request, filter: Optional[str], user_id: Optional[str]):
    return filter or "all", user_id


@router.get("", response_class=HTMLResponse)
async def series_page(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Full series page."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.sonarr:
        return templates.TemplateResponse(
            request, "error.html", {"message": "Sonarr is not configured."}
        )

    try:
        series, users, filter_options, jellyfin_warning = await _build_series_list(
            filter, user_id, config
        )
    except ServiceError as exc:
        return templates.TemplateResponse(
            request,
            "series.html",
            {
                "series_list": [],
                "users": [],
                "filter": filter,
                "filter_user_id": user_id,
                "filter_options": FILTER_OPTIONS,
                "service_error": str(exc),
                "dry_run": config.dry_run,
            },
        )

    return templates.TemplateResponse(
        request,
        "series.html",
        {
            "series_list": series,
            "users": users,
            "filter": filter,
            "filter_user_id": user_id,
            "filter_options": filter_options,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
        },
    )


@router.get("/list", response_class=HTMLResponse)
async def series_list(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: filtered series list."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.sonarr:
        return HTMLResponse("<p>Sonarr is not configured.</p>")

    try:
        series, users, _, jellyfin_warning = await _build_series_list(filter, user_id, config)
    except ServiceError as exc:
        return HTMLResponse(error_html(str(exc)))

    if sort_by == "size":
        series.sort(key=lambda s: s.total_size_bytes or 0, reverse=(sort_dir != "asc"))

    return templates.TemplateResponse(
        request,
        "partials/series_list.html",
        {
            "series_list": series,
            "users": users,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.get("/{sonarr_id}/seasons", response_class=HTMLResponse)
async def seasons_list(
    request: Request,
    sonarr_id: int,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: seasons for a series with episode file counts and watch status."""
    config = get_config()
    jf, sonarr = _get_services(config)

    try:
        all_series = await sonarr.get_series()
        series = next((s for s in all_series if s["id"] == sonarr_id), None)
        if not series:
            return HTMLResponse("<p class='error'>Series not found.</p>")
        episode_files = await sonarr.get_episode_files(sonarr_id)
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Sonarr", exc)))

    tvdb_id = str(series.get("tvdbId", "")) or None

    # Fetch Jellyfin episode watch data, aggregated per season.
    # We aggregate from episodes (not season-level UserData) because Jellyfin may
    # not update season/series PlayedPercentage promptly after episodes are watched.
    users: list = []
    # {season_num: {user_id: {played: int, total: int}}}
    season_ep_stats: dict[int, dict[str, dict]] = {}
    jf_series_id: Optional[str] = None
    try:
        users = await jf.get_users()
        if tvdb_id and users:
            jf_series_id = await jf.get_jellyfin_series_id(users[0].id, tvdb_id)
            if jf_series_id:
                for user in users:
                    sw = await jf.get_season_watch_stats(user.id, jf_series_id)
                    for sn, stats_data in sw.items():
                        season_ep_stats.setdefault(sn, {})[user.id] = stats_data
    except Exception:
        pass

    build_ws = make_watch_status_builder(users)
    user_ids = [u.id for u in users]

    files_by_season: dict[int, list] = {}
    for f in episode_files:
        sn = f.get("seasonNumber", 0)
        files_by_season.setdefault(sn, []).append(f)

    seasons = []
    for season in series.get("seasons", []):
        sn = season.get("seasonNumber", 0)
        if sn == 0:
            continue
        season_files = files_by_season.get(sn, [])
        file_count = len(season_files)
        if file_count == 0:
            continue
        stats = season.get("statistics", {})

        per_user: dict[str, bool] = {}
        partial_per_user: dict[str, bool] = {}
        for uid in user_ids:
            ep_stats = season_ep_stats.get(sn, {}).get(uid, {})
            total = ep_stats.get("total", 0)
            played = ep_stats.get("played", 0)
            if total > 0 and played == total:
                per_user[uid] = True
            elif total > 0 and played > 0:
                partial_per_user[uid] = True
        ws = build_ws(per_user, partial_per_user) if users else None

        seasons.append(
            SeasonItem(
                number=sn,
                episode_count=stats.get("totalEpisodeCount", 0),
                episode_file_count=file_count,
                size_bytes=sum(f.get("size", 0) for f in season_files),
                watch_status=ws,
            )
        )

    if sort_by == "size":
        seasons.sort(key=lambda x: x.size_bytes or 0, reverse=(sort_dir != "asc"))
    else:
        seasons.sort(key=lambda x: x.number)

    return templates.TemplateResponse(
        request,
        "partials/seasons_list.html",
        {
            "series_id": sonarr_id,
            "series_title": series["title"],
            "jf_series_id": jf_series_id or "",
            "seasons": seasons,
            "users": users,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.get("/{sonarr_id}/seasons/{season_number}/episodes", response_class=HTMLResponse)
async def episodes_list(
    request: Request,
    sonarr_id: int,
    season_number: int,
    jf_series_id: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: episodes for a specific season with watch status."""
    config = get_config()
    jf, sonarr = _get_services(config)

    try:
        episodes_raw = await sonarr.get_episodes(sonarr_id)
        episode_files = await sonarr.get_episode_files(sonarr_id)
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Sonarr", exc)))

    # Fetch Jellyfin episode watch data — graceful degradation on failure.
    users: list = []
    ep_watch: dict[tuple[int, int], dict[str, bool]] = {}
    if jf_series_id:
        try:
            users = await jf.get_users()
            for user in users:
                ewd = await jf.get_episode_watch_data(user.id, jf_series_id)
                for key, played in ewd.items():
                    ep_watch.setdefault(key, {})[user.id] = played
        except Exception:
            pass

    build_ws = make_watch_status_builder(users)
    user_ids = [u.id for u in users]
    file_size_by_id = {f["id"]: f.get("size") for f in episode_files}

    episodes = []
    for ep in episodes_raw:
        if ep.get("seasonNumber") != season_number:
            continue
        key = (ep["seasonNumber"], ep["episodeNumber"])
        per_user = ep_watch.get(key, {})
        ws = build_ws(per_user) if users and per_user else None
        episodes.append(
            EpisodeItem(
                sonarr_id=ep["id"],
                episode_file_id=ep.get("episodeFileId") or None,
                title=ep.get("title", "Unknown"),
                season_number=ep["seasonNumber"],
                episode_number=ep["episodeNumber"],
                has_file=ep.get("hasFile", False),
                file_size_bytes=file_size_by_id.get(ep.get("episodeFileId") or 0) or None,
                air_date=ep.get("airDate"),
                watch_status=ws,
            )
        )

    if sort_by == "size":
        episodes.sort(key=lambda e: e.file_size_bytes or 0, reverse=(sort_dir != "asc"))
    else:
        episodes.sort(key=lambda e: e.episode_number)

    return templates.TemplateResponse(
        request,
        "partials/episodes_list.html",
        {
            "episodes": episodes,
            "users": users,
            "sonarr_id": sonarr_id,
            "season_number": season_number,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.post("/confirm", response_class=HTMLResponse)
async def series_confirm(
    request: Request,
    action: Annotated[str, Form()],
    sonarr_id: Annotated[int, Form()],
    season_number: Annotated[Optional[int], Form()] = None,
    season_numbers: Annotated[list[int], Form()] = [],
    episode_file_ids: Annotated[list[int], Form()] = [],
):
    """HTMX partial: deletion confirmation."""
    config = get_config()
    sonarr = SonarrService(config.sonarr.url, config.sonarr.api_key)

    try:
        all_series = await sonarr.get_series()
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Sonarr", exc)))

    series = next((s for s in all_series if s["id"] == sonarr_id), None)
    series_title = series["title"] if series else f"ID {sonarr_id}"

    effective_seasons = season_numbers if season_numbers else (
        [season_number] if season_number is not None else []
    )

    if action == "season" and effective_seasons:
        items = [f"{series_title} – Season {sn}" for sn in effective_seasons]
    elif action == "episode":
        items = [f"{series_title} – {len(episode_file_ids)} episode(s)"]
    elif action == "mixed":
        items = [f"{series_title} – Season {sn} (all)" for sn in effective_seasons]
        if episode_file_ids:
            items.append(f"{series_title} – {len(episode_file_ids)} individual episode(s)")
    else:
        items = [series_title]

    freed_bytes = 0
    if action == "series" and series:
        freed_bytes = series.get("statistics", {}).get("sizeOnDisk", 0)
    elif action in ("season", "episode", "mixed"):
        try:
            ep_files = await sonarr.get_episode_files(sonarr_id)
            file_size = {f["id"]: f.get("size", 0) for f in ep_files}
            season_files: dict[int, list] = {}
            for f in ep_files:
                season_files.setdefault(f.get("seasonNumber", 0), []).append(f)
            if action == "season":
                for sn in effective_seasons:
                    freed_bytes += sum(f.get("size", 0) for f in season_files.get(sn, []))
            elif action == "episode":
                freed_bytes = sum(file_size.get(fid, 0) for fid in episode_file_ids)
            elif action == "mixed":
                for sn in effective_seasons:
                    freed_bytes += sum(f.get("size", 0) for f in season_files.get(sn, []))
                freed_bytes += sum(file_size.get(fid, 0) for fid in episode_file_ids)
        except Exception:
            pass

    return templates.TemplateResponse(
        request,
        "partials/confirm_series.html",
        {
            "items": items,
            "action": action,
            "sonarr_id": sonarr_id,
            "season_numbers": effective_seasons,
            "episode_file_ids": episode_file_ids,
            "freed_bytes": freed_bytes,
            "dry_run": config.dry_run,
        },
    )


@router.post("/delete", response_class=HTMLResponse)
async def series_delete(
    request: Request,
    background_tasks: BackgroundTasks,
    action: Annotated[str, Form()],
    sonarr_id: Annotated[int, Form()],
    season_number: Annotated[Optional[int], Form()] = None,
    season_numbers: Annotated[list[int], Form()] = [],
    episode_file_ids: Annotated[list[int], Form()] = [],
):
    """Execute series/season/episode deletion."""
    config = get_config()
    sonarr = SonarrService(config.sonarr.url, config.sonarr.api_key)

    try:
        all_series = await sonarr.get_series()
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Sonarr", exc)))

    series = next((s for s in all_series if s["id"] == sonarr_id), None)
    series_title = series["title"] if series else f"ID {sonarr_id}"

    effective_seasons = season_numbers if season_numbers else (
        [season_number] if season_number is not None else []
    )

    results: list[DeleteResultItem] = []
    any_success = False

    if config.dry_run:
        if action == "series":
            results.append(DeleteResultItem(title=series_title, level="series", success=True, message="[dry-run] Would delete"))
            await log_action("series", series_title, "series", dry_run=True, success=True, details="dry-run")
        elif action == "season" and effective_seasons:
            for sn in effective_seasons:
                t = f"{series_title} – Season {sn}"
                results.append(DeleteResultItem(title=t, level="season", success=True, message="[dry-run] Would delete"))
                await log_action("series", t, "season", dry_run=True, success=True, details="dry-run")
        elif action == "episode":
            t = f"{series_title} – {len(episode_file_ids)} episode(s)"
            results.append(DeleteResultItem(title=t, level="episode", success=True, message="[dry-run] Would delete"))
            await log_action("series", t, "episode", dry_run=True, success=True, details="dry-run")
        elif action == "mixed":
            for sn in effective_seasons:
                t = f"{series_title} – Season {sn}"
                results.append(DeleteResultItem(title=t, level="season", success=True, message="[dry-run] Would delete"))
                await log_action("series", t, "season", dry_run=True, success=True, details="dry-run")
            if episode_file_ids:
                t = f"{series_title} – {len(episode_file_ids)} individual episode(s)"
                results.append(DeleteResultItem(title=t, level="episode", success=True, message="[dry-run] Would delete"))
                await log_action("series", t, "episode", dry_run=True, success=True, details="dry-run")
    else:
        if action == "series":
            try:
                await sonarr.delete_series(sonarr_id, delete_files=True, add_import_exclusion=config.add_import_exclusion)
                results.append(DeleteResultItem(title=series_title, level="series", success=True, message="Deleted"))
                await log_action("series", series_title, "series", dry_run=False, success=True)
                any_success = True
            except httpx.HTTPError as exc:
                msg = classify_error("Sonarr", exc)
                results.append(DeleteResultItem(title=series_title, level="series", success=False, message=msg))
                await log_action("series", series_title, "series", dry_run=False, success=False, details=msg)
        elif action == "season" and effective_seasons:
            for sn in effective_seasons:
                t = f"{series_title} – Season {sn}"
                try:
                    file_ids = await sonarr.get_season_episode_file_ids(sonarr_id, sn)
                    await sonarr.delete_episode_files(file_ids)
                    results.append(DeleteResultItem(title=t, level="season", success=True, message="Deleted"))
                    await log_action("series", t, "season", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Sonarr", exc)
                    results.append(DeleteResultItem(title=t, level="season", success=False, message=msg))
                    await log_action("series", t, "season", dry_run=False, success=False, details=msg)
        elif action == "episode":
            t = f"{series_title} – {len(episode_file_ids)} episode(s)"
            try:
                await sonarr.delete_episode_files(episode_file_ids)
                results.append(DeleteResultItem(title=t, level="episode", success=True, message="Deleted"))
                await log_action("series", t, "episode", dry_run=False, success=True)
                any_success = True
            except httpx.HTTPError as exc:
                msg = classify_error("Sonarr", exc)
                results.append(DeleteResultItem(title=t, level="episode", success=False, message=msg))
                await log_action("series", t, "episode", dry_run=False, success=False, details=msg)
        elif action == "mixed":
            for sn in effective_seasons:
                t = f"{series_title} – Season {sn}"
                try:
                    file_ids = await sonarr.get_season_episode_file_ids(sonarr_id, sn)
                    await sonarr.delete_episode_files(file_ids)
                    results.append(DeleteResultItem(title=t, level="season", success=True, message="Deleted"))
                    await log_action("series", t, "season", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Sonarr", exc)
                    results.append(DeleteResultItem(title=t, level="season", success=False, message=msg))
                    await log_action("series", t, "season", dry_run=False, success=False, details=msg)
            if episode_file_ids:
                t = f"{series_title} – {len(episode_file_ids)} individual episode(s)"
                try:
                    await sonarr.delete_episode_files(episode_file_ids)
                    results.append(DeleteResultItem(title=t, level="episode", success=True, message="Deleted"))
                    await log_action("series", t, "episode", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Sonarr", exc)
                    results.append(DeleteResultItem(title=t, level="episode", success=False, message=msg))
                    await log_action("series", t, "episode", dry_run=False, success=False, details=msg)

        if any_success:
            background_tasks.add_task(_refresh_after_series_delete, config, sonarr_id, series_title)

    delete_result = DeleteResult(
        dry_run=config.dry_run,
        items=results,
        total_success=sum(1 for r in results if r.success),
        total_error=sum(1 for r in results if not r.success),
    )
    return templates.TemplateResponse(
        request, "partials/delete_result.html", {"result": delete_result}
    )


@router.get("/api", summary="List all series with watch status")
async def api_list_series(
    filter: str = "all",
    user_id: Optional[str] = None,
) -> list[SeriesItem]:
    """Return series from Sonarr enriched with Jellyfin watch status."""
    series, _, _, _ = await _build_series_list(filter, user_id)
    return series
