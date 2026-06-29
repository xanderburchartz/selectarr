"""Music routes: browsing artists/albums/tracks, confirmation, and deletion."""
from __future__ import annotations

import asyncio
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Form, Request
from fastapi.responses import HTMLResponse

from app.config import get_config
from app.database import log_action
from app.models import (
    AlbumItem,
    ArtistItem,
    DeleteResult,
    DeleteResultItem,
    TrackItem,
)
from app.services.errors import ServiceError, classify_error, error_html
from app.services.jellyfin import JellyfinService, make_watch_status_builder
from app.services.lidarr import LidarrService

router = APIRouter(prefix="/music", tags=["music"])
from app.templates_env import templates


async def _refresh_after_music_delete(
    config,
    artist_id: Optional[int],
    title: str,
) -> None:
    if artist_id is not None:
        lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key)
        try:
            await lidarr.rescan_artist(artist_id)
            await log_action("music", title, "refresh", dry_run=False, success=True, details="Lidarr: RescanArtist")
        except Exception as exc:
            await log_action("music", title, "refresh", dry_run=False, success=False, details=f"Lidarr: {exc}")

    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    try:
        await jf.refresh_library()
        await log_action("music", "Jellyfin library", "refresh", dry_run=False, success=True, details="Jellyfin: library refresh")
    except Exception as exc:
        await log_action("music", "Jellyfin library", "refresh", dry_run=False, success=False, details=f"Jellyfin: {exc}")

FILTER_OPTIONS = [
    ("all", "filter.all"),
    ("watched_all", "filter.listened_all"),
    ("watched_any", "filter.listened_any"),
    ("unwatched", "filter.not_listened"),
    ("watched_by_user", "filter.listened_by_user"),
]


def _get_services(config=None):
    if config is None:
        config = get_config()
    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key) if config.lidarr else None
    return jf, lidarr


async def _build_artists_list(
    filter_type: str,
    filter_user_id: Optional[str],
    config=None,
) -> tuple[list[ArtistItem], list, list, Optional[str]]:
    """Fetch and filter artists.

    Returns (artists, users, filter_options, jellyfin_warning).
    Jellyfin failures degrade gracefully. Lidarr failures raise ServiceError.
    """
    if config is None:
        config = get_config()

    jf, lidarr = _get_services(config)

    jellyfin_warning: Optional[str] = None
    try:
        users = await jf.get_users()
        watch_map = await jf.build_music_watch_map(users)
    except httpx.HTTPError as exc:
        users = []
        watch_map = {}
        jellyfin_warning = classify_error("Jellyfin", exc)

    build_ws = make_watch_status_builder(users)
    user_ids = [u.id for u in users]

    try:
        raw_artists = await lidarr.get_artists() if lidarr else []
    except httpx.HTTPError as exc:
        raise ServiceError(classify_error("Lidarr", exc)) from exc

    result = []
    for a in raw_artists:
        mb_id = a.get("foreignArtistId")
        per_user = watch_map.get(mb_id, {}) if mb_id else {}
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

        stats = a.get("statistics", {})
        if not stats.get("trackFileCount", 0):
            continue
        result.append(
            ArtistItem(
                lidarr_id=a["id"],
                name=a["artistName"],
                mb_id=mb_id,
                album_count=stats.get("albumCount", 0),
                total_size_bytes=stats.get("sizeOnDisk", 0),
                watch_status=build_ws(per_user) if per_user else None,
            )
        )

    result.sort(key=lambda a: a.name.lower())
    return result, users, FILTER_OPTIONS, jellyfin_warning


def _apply_user_defaults(request: Request, filter: Optional[str], user_id: Optional[str]):
    return filter or "all", user_id


@router.get("", response_class=HTMLResponse)
async def music_page(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Full music/artists page."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.lidarr:
        return templates.TemplateResponse(
            request, "error.html", {"message": "Lidarr is not configured."}
        )

    try:
        artists, users, filter_options, jellyfin_warning = await _build_artists_list(
            filter, user_id, config
        )
    except ServiceError as exc:
        return templates.TemplateResponse(
            request,
            "music.html",
            {
                "artists": [],
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
        "music.html",
        {
            "artists": artists,
            "users": users,
            "filter": filter,
            "filter_user_id": user_id,
            "filter_options": filter_options,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
        },
    )


@router.get("/list", response_class=HTMLResponse)
async def music_list(
    request: Request,
    filter: Optional[str] = None,
    user_id: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: filtered artists list."""
    filter, user_id = _apply_user_defaults(request, filter, user_id)
    config = get_config()
    if not config.lidarr:
        return HTMLResponse("<p>Lidarr is not configured.</p>")

    try:
        artists, users, _, jellyfin_warning = await _build_artists_list(filter, user_id, config)
    except ServiceError as exc:
        return HTMLResponse(error_html(str(exc)))

    if sort_by == "size":
        artists.sort(key=lambda a: a.total_size_bytes or 0, reverse=(sort_dir != "asc"))

    return templates.TemplateResponse(
        request,
        "partials/music_list.html",
        {
            "artists": artists,
            "users": users,
            "jellyfin_warning": jellyfin_warning,
            "dry_run": config.dry_run,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
        },
    )


@router.get("/artists/{lidarr_id}/albums", response_class=HTMLResponse)
async def albums_list(
    request: Request,
    lidarr_id: int,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: albums for an artist."""
    config = get_config()
    lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key)

    try:
        raw_albums = await lidarr.get_albums(lidarr_id)
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Lidarr", exc)))

    albums = [
        AlbumItem(
            lidarr_id=a["id"],
            title=a["title"],
            year=a.get("releaseDate", "")[:4] and int(a["releaseDate"][:4]) or None,
            mb_id=a.get("foreignAlbumId"),
            has_files=a.get("statistics", {}).get("trackFileCount", 0) > 0,
            track_count=a.get("statistics", {}).get("trackFileCount", 0),
            size_bytes=a.get("statistics", {}).get("sizeOnDisk", 0),
        )
        for a in raw_albums
        if a.get("statistics", {}).get("trackFileCount", 0) > 0
    ]
    if sort_by == "size":
        albums.sort(key=lambda a: a.size_bytes or 0, reverse=(sort_dir != "asc"))
    else:
        albums.sort(key=lambda a: a.year or 0)

    return templates.TemplateResponse(
        request,
        "partials/albums_list.html",
        {"albums": albums, "artist_id": lidarr_id, "sort_by": sort_by, "sort_dir": sort_dir},
    )


@router.get("/albums/{album_id}/tracks", response_class=HTMLResponse)
async def tracks_list(
    request: Request,
    album_id: int,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
):
    """HTMX partial: tracks for an album."""
    config = get_config()
    lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key)

    try:
        raw_tracks, track_files = await asyncio.gather(
            lidarr.get_tracks(album_id),
            lidarr.get_album_track_files(album_id),
        )
    except httpx.HTTPError as exc:
        return HTMLResponse(error_html(classify_error("Lidarr", exc)))

    file_size_by_id = {f["id"]: f.get("size") for f in track_files}

    tracks = [
        TrackItem(
            lidarr_id=t["id"],
            track_file_id=t.get("trackFileId") or None,
            title=t.get("title", "Unknown"),
            track_number=str(t["trackNumber"]) if t.get("trackNumber") is not None else None,
            duration_ms=t.get("duration"),
            has_file=True,
            file_size_bytes=file_size_by_id.get(t.get("trackFileId") or 0) or None,
        )
        for t in raw_tracks
        if t.get("trackFileId")
    ]
    import re as _re
    def _track_key(tn):
        if not tn:
            return ('', 9999)
        m = _re.match(r'^([A-Za-z]*)(\d+)', tn)
        return (m.group(1).upper(), int(m.group(2))) if m else (tn, 0)
    if sort_by == "size":
        tracks.sort(key=lambda t: t.file_size_bytes or 0, reverse=(sort_dir != "asc"))
    else:
        tracks.sort(key=lambda t: _track_key(t.track_number))

    return templates.TemplateResponse(
        request,
        "partials/tracks_list.html",
        {"tracks": tracks, "album_id": album_id, "sort_by": sort_by, "sort_dir": sort_dir},
    )


@router.post("/confirm", response_class=HTMLResponse)
async def music_confirm(
    request: Request,
    action: Annotated[str, Form()],
    artist_id: Annotated[Optional[int], Form()] = None,
    artist_ids: Annotated[list[int], Form()] = [],
    album_id: Annotated[Optional[int], Form()] = None,
    album_ids: Annotated[list[int], Form()] = [],
    track_file_ids: Annotated[list[int], Form()] = [],
):
    """HTMX partial: deletion confirmation for music."""
    config = get_config()
    lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key)

    effective_artists = artist_ids if artist_ids else ([artist_id] if artist_id else [])
    effective_albums = album_ids if album_ids else ([album_id] if album_id else [])

    freed_bytes = 0

    if action == "artist" and effective_artists:
        try:
            raw = await lidarr.get_artists()
        except httpx.HTTPError as exc:
            return HTMLResponse(error_html(classify_error("Lidarr", exc)))
        name_map = {a["id"]: a["artistName"] for a in raw}
        size_map = {a["id"]: a.get("statistics", {}).get("sizeOnDisk", 0) for a in raw}
        items = [name_map.get(aid, f"Artist ID {aid}") for aid in effective_artists]
        freed_bytes = sum(size_map.get(aid, 0) for aid in effective_artists)
    elif action == "album" and effective_albums:
        album_results = await asyncio.gather(
            *[lidarr.get_album_info(aid) for aid in effective_albums],
            return_exceptions=True,
        )
        items = []
        for aid, result in zip(effective_albums, album_results):
            if isinstance(result, Exception):
                items.append(f"Album {aid}")
            else:
                items.append(result["title"])
                freed_bytes += result["size"]
    elif action == "mixed":
        artist_items: list[str] = []
        if effective_artists:
            try:
                raw = await lidarr.get_artists()
                name_map = {a["id"]: a["artistName"] for a in raw}
                size_map = {a["id"]: a.get("statistics", {}).get("sizeOnDisk", 0) for a in raw}
                artist_items = [name_map.get(aid, f"Artist ID {aid}") for aid in effective_artists]
                freed_bytes += sum(size_map.get(aid, 0) for aid in effective_artists)
            except httpx.HTTPError:
                artist_items = [f"Artist ID {aid}" for aid in effective_artists]
        album_items: list[str] = []
        if effective_albums:
            album_results = await asyncio.gather(
                *[lidarr.get_album_info(aid) for aid in effective_albums],
                return_exceptions=True,
            )
            for aid, result in zip(effective_albums, album_results):
                if isinstance(result, Exception):
                    album_items.append(f"Album {aid}")
                else:
                    album_items.append(result["title"])
                    freed_bytes += result["size"]
        if track_file_ids:
            try:
                track_files = await lidarr.get_track_files_by_ids(track_file_ids)
                freed_bytes += sum(f.get("size", 0) for f in track_files)
            except Exception:
                pass
        track_items = [f"{len(track_file_ids)} individual track(s)"] if track_file_ids else []
        items = artist_items + album_items + track_items
    else:
        if track_file_ids:
            try:
                track_files = await lidarr.get_track_files_by_ids(track_file_ids)
                freed_bytes += sum(f.get("size", 0) for f in track_files)
            except Exception:
                pass
        items = [f"{len(track_file_ids)} track file(s)"]

    return templates.TemplateResponse(
        request,
        "partials/confirm_music.html",
        {
            "items": items,
            "action": action,
            "artist_ids": effective_artists,
            "album_ids": effective_albums,
            "track_file_ids": track_file_ids,
            "dry_run": config.dry_run,
            "freed_bytes": freed_bytes,
        },
    )


@router.post("/delete", response_class=HTMLResponse)
async def music_delete(
    request: Request,
    background_tasks: BackgroundTasks,
    action: Annotated[str, Form()],
    artist_id: Annotated[Optional[int], Form()] = None,
    artist_ids: Annotated[list[int], Form()] = [],
    album_id: Annotated[Optional[int], Form()] = None,
    album_ids: Annotated[list[int], Form()] = [],
    track_file_ids: Annotated[list[int], Form()] = [],
):
    """Execute music deletion (artist, album, or tracks)."""
    config = get_config()
    lidarr = LidarrService(config.lidarr.url, config.lidarr.api_key)

    effective_artists = artist_ids if artist_ids else ([artist_id] if artist_id else [])
    effective_albums = album_ids if album_ids else ([album_id] if album_id else [])

    results: list[DeleteResultItem] = []
    any_success = False

    # Resolve artist names for logging / results
    artist_name_map: dict[int, str] = {}
    if effective_artists:
        try:
            raw_artists = await lidarr.get_artists()
            artist_name_map = {a["id"]: a["artistName"] for a in raw_artists}
        except httpx.HTTPError:
            pass

    def _artist_name(aid: int) -> str:
        return artist_name_map.get(aid, f"Artist ID {aid}")

    if config.dry_run:
        if action == "artist" and effective_artists:
            for aid in effective_artists:
                t = _artist_name(aid)
                results.append(DeleteResultItem(title=t, level="artist", success=True, message="[dry-run] Would delete"))
                await log_action("music", t, "artist", dry_run=True, success=True, details="dry-run")
        elif action == "album" and effective_albums:
            for aid in effective_albums:
                t = f"Album {aid}"
                results.append(DeleteResultItem(title=t, level="album", success=True, message="[dry-run] Would delete"))
                await log_action("music", t, "album", dry_run=True, success=True, details="dry-run")
        elif action in ("mixed", "track"):
            for aid in effective_artists:
                t = _artist_name(aid)
                results.append(DeleteResultItem(title=t, level="artist", success=True, message="[dry-run] Would delete"))
                await log_action("music", t, "artist", dry_run=True, success=True, details="dry-run")
            for aid in effective_albums:
                t = f"Album {aid}"
                results.append(DeleteResultItem(title=t, level="album", success=True, message="[dry-run] Would delete"))
                await log_action("music", t, "album", dry_run=True, success=True, details="dry-run")
            if track_file_ids:
                t = f"{len(track_file_ids)} track(s)"
                results.append(DeleteResultItem(title=t, level="track", success=True, message="[dry-run] Would delete"))
                await log_action("music", t, "track", dry_run=True, success=True, details="dry-run")
        else:
            t = f"{len(track_file_ids)} track(s)"
            results.append(DeleteResultItem(title=t, level="track", success=True, message="[dry-run] Would delete"))
            await log_action("music", t, "track", dry_run=True, success=True, details="dry-run")
    else:
        if action == "artist" and effective_artists:
            for aid in effective_artists:
                t = _artist_name(aid)
                try:
                    await lidarr.delete_artist(aid, delete_files=True, add_import_exclusion=config.add_import_exclusion)
                    results.append(DeleteResultItem(title=t, level="artist", success=True, message="Deleted"))
                    await log_action("music", t, "artist", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Lidarr", exc)
                    results.append(DeleteResultItem(title=t, level="artist", success=False, message=msg))
                    await log_action("music", t, "artist", dry_run=False, success=False, details=msg)
        elif action == "album" and effective_albums:
            for aid in effective_albums:
                t = f"Album {aid}"
                try:
                    await lidarr.delete_album(aid, delete_files=True, add_import_exclusion=config.add_import_exclusion)
                    results.append(DeleteResultItem(title=t, level="album", success=True, message="Deleted"))
                    await log_action("music", t, "album", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Lidarr", exc)
                    results.append(DeleteResultItem(title=t, level="album", success=False, message=msg))
                    await log_action("music", t, "album", dry_run=False, success=False, details=msg)
        elif action in ("mixed", "track"):
            for aid in effective_artists:
                t = _artist_name(aid)
                try:
                    await lidarr.delete_artist(aid, delete_files=True, add_import_exclusion=config.add_import_exclusion)
                    results.append(DeleteResultItem(title=t, level="artist", success=True, message="Deleted"))
                    await log_action("music", t, "artist", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Lidarr", exc)
                    results.append(DeleteResultItem(title=t, level="artist", success=False, message=msg))
                    await log_action("music", t, "artist", dry_run=False, success=False, details=msg)
            for aid in effective_albums:
                t = f"Album {aid}"
                try:
                    await lidarr.delete_album(aid, delete_files=True, add_import_exclusion=config.add_import_exclusion)
                    results.append(DeleteResultItem(title=t, level="album", success=True, message="Deleted"))
                    await log_action("music", t, "album", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Lidarr", exc)
                    results.append(DeleteResultItem(title=t, level="album", success=False, message=msg))
                    await log_action("music", t, "album", dry_run=False, success=False, details=msg)
            if track_file_ids:
                t = f"{len(track_file_ids)} individual track(s)"
                try:
                    await lidarr.delete_track_files(track_file_ids)
                    results.append(DeleteResultItem(title=t, level="track", success=True, message="Deleted"))
                    await log_action("music", t, "track", dry_run=False, success=True)
                    any_success = True
                except httpx.HTTPError as exc:
                    msg = classify_error("Lidarr", exc)
                    results.append(DeleteResultItem(title=t, level="track", success=False, message=msg))
                    await log_action("music", t, "track", dry_run=False, success=False, details=msg)
        else:
            t = f"{len(track_file_ids)} track(s)"
            try:
                await lidarr.delete_track_files(track_file_ids)
                results.append(DeleteResultItem(title=t, level="track", success=True, message="Deleted"))
                await log_action("music", t, "track", dry_run=False, success=True)
                any_success = True
            except httpx.HTTPError as exc:
                msg = classify_error("Lidarr", exc)
                results.append(DeleteResultItem(title=t, level="track", success=False, message=msg))
                await log_action("music", t, "track", dry_run=False, success=False, details=msg)

        if any_success:
            # Skip rescan when artists were fully deleted from Lidarr — they no longer exist.
            # RescanArtist on a deleted artist returns 500. Jellyfin refresh still runs.
            rescan_id = None if (action == "artist" or effective_artists) else artist_id
            background_tasks.add_task(_refresh_after_music_delete, config, rescan_id, results[0].title if results else "")

    delete_result = DeleteResult(
        dry_run=config.dry_run,
        items=results,
        total_success=sum(1 for r in results if r.success),
        total_error=sum(1 for r in results if not r.success),
    )
    return templates.TemplateResponse(
        request, "partials/delete_result.html", {"result": delete_result}
    )


@router.get("/api", summary="List all artists with metadata")
async def api_list_artists(
    filter: str = "all",
    user_id: Optional[str] = None,
) -> list[ArtistItem]:
    """Return artists from Lidarr enriched with Jellyfin play status."""
    artists, _, _, _ = await _build_artists_list(filter, user_id)
    return artists
