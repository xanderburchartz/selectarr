"""Movie routes: browsing, filtering, confirmation, and deletion."""
from __future__ import annotations

from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse

from app.config import get_config
from app.database import log_action
from app.models import DeleteResult, DeleteResultItem, MovieItem
from app.services.errors import ServiceError, classify_error, error_html
from app.services.jellyfin import JellyfinService, make_watch_status_builder
from app.services.radarr import RadarrService

router = APIRouter(prefix="/movies", tags=["movies"])
from app.templates_env import templates


async def _refresh_after_movies_delete(
    config,
    deleted: list[tuple[int, str]],
) -> None:
    radarr = RadarrService(config.radarr.url, config.radarr.api_key)
    for movie_id, title in deleted:
        try:
            await radarr.rescan_movie(movie_id)
            await log_action("movie", title, "refresh", dry_run=False, success=True, details="Radarr: RescanMovie")
        except Exception as exc:
            await log_action("movie", title, "refresh", dry_run=False, success=False, details=f"Radarr: {exc}")

    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    try:
        await jf.refresh_library()
        await log_action("movie", "Jellyfin library", "refresh", dry_run=False, success=True, details="Jellyfin: library refresh")
    except Exception as exc:
        await log_action("movie", "Jellyfin library", "refresh", dry_run=False, success=False, details=f"Jellyfin: {exc}")

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
    radarr = RadarrService(config.radarr.url, config.radarr.api_key) if config.radarr else None
    return jf, radarr


async def _build_movie_items(
    filter_type: str,
    filter_user_id: Optional[str],
    config=None,
) -> tuple[list[MovieItem], list, list, Optional[str]]:
    """Fetch and filter movies.

    Returns (movies, users, filter_options, jellyfin_warning).
    Jellyfin failures degrade gracefully — watch status becomes unavailable.
    Radarr failures raise ServiceError.
    """
    if config is None:
        config = get_config()

    jf, radarr = _get_services(config)

    jellyfin_warning: Optional[str] = None
    try:
        users = await jf.get_users()
        watch_map = await jf.build_movie_watch_map(users)
    except httpx.HTTPError as exc:
        users = []
        watch_map = {}
        jellyfin_warning = classify_error("Jellyfin", exc)

    build_ws = make_watch_status_builder(users)
    user_ids = [u.id for u in users]

    try:
        raw_movies = await radarr.get_movies() if radarr else []
    except httpx.HTTPError as exc:
        raise ServiceError(classify_error("Radarr", exc)) from exc

    movies = []
    for rm in raw_movies:
        if not rm.get("hasFile"):
            continue

        tmdb_id = str(rm.get("tmdbId", "")) or None
        per_user = watch_map.get(tmdb_id, {}) if tmdb_id else {}
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

        size = rm.get("sizeOnDisk", 0) or 0
        movies.append(
            MovieItem(
                radarr_id=rm["id"],
                title=rm["title"],
                year=rm.get("year", 0),
                tmdb_id=rm.get("tmdbId"),
                imdb_id=rm.get("imdbId"),
                has_file=rm.get("hasFile", False),
                file_size_bytes=size if size > 0 else None,
                watch_status=build_ws(per_user) if tmdb_id else None,
            )
        )

    movies.sort(key=lambda m: m.title.lower())
    return movies, users, FILTER_OPTIONS, jellyfin_warning


def _apply_user_defaults(request: Request, filter: Optional[str], user_id: Optional[str]):
    return filter or "all", user_id


@router.get("", response_class=HTMLResponse)
async def movies_page(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Full movies page."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.radarr:
        return templates.TemplateResponse(
            request, "error.html", {"message": "Radarr is not configured."}
        )

    try:
        movies, users, filter_options, jellyfin_warning = await _build_movie_items(
            filter, user_id, config
        )
    except ServiceError as exc:
        return templates.TemplateResponse(
            request,
            "movies.html",
            {
                "movies": [],
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
        "movies.html",
        {
            "movies": movies,
            "users": users,
            "filter": filter,
            "filter_user_id": user_id,
            "filter_options": filter_options,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
        },
    )


@router.get("/list", response_class=HTMLResponse)
async def movies_list(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: filtered movie list."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.radarr:
        return HTMLResponse("<p>Radarr is not configured.</p>")

    try:
        movies, users, _, jellyfin_warning = await _build_movie_items(filter, user_id, config)
    except ServiceError as exc:
        return HTMLResponse(error_html(str(exc)))

    if sort_by == "size":
        movies.sort(key=lambda m: m.file_size_bytes or 0, reverse=(sort_dir != "asc"))

    return templates.TemplateResponse(
        request,
        "partials/movies_list.html",
        {
            "movies": movies,
            "users": users,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.post("/confirm", response_class=HTMLResponse)
async def movies_confirm(
    request: Request,
    radarr_ids: Annotated[list[int], Form()] = [],
):
    """HTMX partial: deletion confirmation for selected movies."""
    config = get_config()
    if not radarr_ids:
        return HTMLResponse("<p class='error'>No movies selected.</p>")

    radarr = RadarrService(config.radarr.url, config.radarr.api_key)
    try:
        raw_movies = await radarr.get_movies()
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Radarr", exc)))

    id_map = {m["id"]: m for m in raw_movies}
    selected = [id_map[rid] for rid in radarr_ids if rid in id_map]
    return templates.TemplateResponse(
        request,
        "partials/confirm_movies.html",
        {"selected": selected, "radarr_ids": radarr_ids, "dry_run": config.dry_run},
    )


@router.post("/delete", response_class=HTMLResponse)
async def movies_delete(
    request: Request,
    background_tasks: BackgroundTasks,
    radarr_ids: Annotated[list[int], Form()] = [],
):
    """Execute movie deletion (or dry-run preview)."""
    config = get_config()
    if not radarr_ids:
        return HTMLResponse("<p class='error'>No movies selected.</p>")

    radarr = RadarrService(config.radarr.url, config.radarr.api_key)
    try:
        raw_movies = await radarr.get_movies()
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Radarr", exc)))

    id_map = {m["id"]: m for m in raw_movies}
    results: list[DeleteResultItem] = []
    deleted: list[tuple[int, str]] = []

    for rid in radarr_ids:
        movie = id_map.get(rid)
        if not movie:
            results.append(
                DeleteResultItem(
                    title=f"ID {rid}", level="movie", success=False, message="Not found in Radarr"
                )
            )
            continue

        title = f"{movie['title']} ({movie.get('year', '?')})"
        if config.dry_run:
            results.append(
                DeleteResultItem(title=title, level="movie", success=True, message="[dry-run] Would delete")
            )
            await log_action("movie", title, "movie", dry_run=True, success=True, details="dry-run")
        else:
            try:
                await radarr.delete_movie(
                    rid,
                    delete_files=True,
                    add_import_exclusion=config.add_import_exclusion,
                )
                results.append(DeleteResultItem(title=title, level="movie", success=True, message="Deleted"))
                await log_action("movie", title, "movie", dry_run=False, success=True)
                deleted.append((rid, title))
            except httpx.HTTPError as exc:
                msg = classify_error("Radarr", exc)
                results.append(DeleteResultItem(title=title, level="movie", success=False, message=msg))
                await log_action("movie", title, "movie", dry_run=False, success=False, details=msg)

    if deleted:
        background_tasks.add_task(_refresh_after_movies_delete, config, deleted)

    delete_result = DeleteResult(
        dry_run=config.dry_run,
        items=results,
        total_success=sum(1 for r in results if r.success),
        total_error=sum(1 for r in results if not r.success),
    )
    return templates.TemplateResponse(
        request, "partials/delete_result.html", {"result": delete_result}
    )


@router.get("/api", summary="List all movies with watch status")
async def api_list_movies(
    filter: str = "all",
    user_id: Optional[str] = None,
) -> list[MovieItem]:
    """Return movies from Radarr enriched with Jellyfin watch status."""
    movies, _, _, _ = await _build_movie_items(filter, user_id)
    return movies
