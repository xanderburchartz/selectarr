"""Jellyfin API client."""
from __future__ import annotations

import time
from typing import Optional

import httpx

from app.models import UserInfo

_CACHE_TTL = 300  # seconds
_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, value: object | None = None, ttl: int = _CACHE_TTL):
    """Simple TTL cache helper. Pass value to store, omit to retrieve."""
    if value is not None:
        _cache[key] = (time.monotonic(), value)
        return value
    entry = _cache.get(key)
    if entry and time.monotonic() - entry[0] < ttl:
        return entry[1]
    return None


def _client(url: str, api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=url.rstrip("/"),
        headers={"X-Emby-Token": api_key},
        timeout=30.0,
    )


class JellyfinService:
    """Async client for the Jellyfin API."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key

    async def get_users(self) -> list[UserInfo]:
        """Return all Jellyfin users."""
        cached = _cached("jf_users")
        if cached is not None:
            return cached

        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/Users")
            resp.raise_for_status()
            data = resp.json()

        users = [UserInfo(id=u["Id"], name=u["Name"]) for u in data]
        _cached("jf_users", users)
        return users

    async def _get_items(
        self,
        user_id: str,
        item_types: str,
        *,
        parent_id: Optional[str] = None,
        season_id: Optional[str] = None,
        extra_params: Optional[dict] = None,
    ) -> list[dict]:
        """Fetch Jellyfin items for a user with UserData and ProviderIds fields."""
        params: dict = {
            "IncludeItemTypes": item_types,
            "Recursive": "true",
            "Fields": "ProviderIds,UserData,MediaSources",
        }
        if parent_id:
            params["ParentId"] = parent_id
        if season_id:
            params["SeasonId"] = season_id
        if extra_params:
            params.update(extra_params)

        async with _client(self.url, self.api_key) as client:
            resp = await client.get(f"/Users/{user_id}/Items", params=params)
            resp.raise_for_status()
            return resp.json().get("Items", [])

    async def get_watched_movies(self, user_id: str) -> dict[str, bool]:
        """Return {tmdb_id: watched} for all movies visible to user_id."""
        cache_key = f"jf_movies_{user_id}"
        cached = _cached(cache_key)
        if cached is not None:
            return cached

        items = await self._get_items(user_id, "Movie")
        result = {}
        for item in items:
            tmdb_id = item.get("ProviderIds", {}).get("Tmdb")
            if tmdb_id:
                result[tmdb_id] = item.get("UserData", {}).get("Played", False)

        _cached(cache_key, result)
        return result

    async def get_watched_series(self, user_id: str) -> dict[str, bool]:
        """Return {tvdb_id: played_percentage_dict} for all series."""
        cache_key = f"jf_series_{user_id}"
        cached = _cached(cache_key)
        if cached is not None:
            return cached

        items = await self._get_items(user_id, "Series")
        result = {}
        for item in items:
            tvdb_id = item.get("ProviderIds", {}).get("Tvdb")
            if tvdb_id:
                user_data = item.get("UserData", {})
                played = user_data.get("Played", False)
                played_pct = user_data.get("PlayedPercentage", 0)
                # Consider fully watched if Played=True or >95% complete
                result[tvdb_id] = played or played_pct >= 95

        _cached(cache_key, result)
        return result

    async def get_watched_episodes(
        self, user_id: str, series_tvdb_id: Optional[str] = None
    ) -> dict[tuple[int, int], bool]:
        """Return {(season, episode): watched} for episodes.

        Optionally scoped to a specific series by TVDB id.
        """
        items = await self._get_items(
            user_id,
            "Episode",
            extra_params={"Fields": "ProviderIds,UserData,ParentIndexNumber,IndexNumber"},
        )
        result = {}
        for item in items:
            s = item.get("ParentIndexNumber")
            e = item.get("IndexNumber")
            if s is not None and e is not None:
                result[(s, e)] = item.get("UserData", {}).get("Played", False)
        return result

    async def get_watched_music(self, user_id: str) -> dict[str, bool]:
        """Return {musicbrainz_artist_id: any_played} for music artists."""
        cache_key = f"jf_music_{user_id}"
        cached = _cached(cache_key)
        if cached is not None:
            return cached

        items = await self._get_items(user_id, "MusicArtist")
        result = {}
        for item in items:
            mb_id = item.get("ProviderIds", {}).get("MusicBrainzArtist")
            if mb_id:
                result[mb_id] = item.get("UserData", {}).get("Played", False)

        _cached(cache_key, result)
        return result

    async def build_movie_watch_map(
        self, users: list[UserInfo]
    ) -> dict[str, dict[str, bool]]:
        """Return {tmdb_id: {user_id: watched}} for all users."""
        result: dict[str, dict[str, bool]] = {}
        for user in users:
            watched = await self.get_watched_movies(user.id)
            for tmdb_id, played in watched.items():
                result.setdefault(tmdb_id, {})[user.id] = played
        return result

    async def build_series_watch_map(
        self, users: list[UserInfo]
    ) -> dict[str, dict[str, bool]]:
        """Return {tvdb_id: {user_id: watched}} for all users."""
        result: dict[str, dict[str, bool]] = {}
        for user in users:
            watched = await self.get_watched_series(user.id)
            for tvdb_id, played in watched.items():
                result.setdefault(tvdb_id, {})[user.id] = played
        return result

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Validate credentials against Jellyfin. Returns session dict or None."""
        auth_header = (
            'MediaBrowser Client="Selectarr", Device="Selectarr",'
            ' DeviceId="selectarr-server", Version="1.0.0"'
        )
        try:
            async with httpx.AsyncClient(base_url=self.url, timeout=10.0) as client:
                resp = await client.post(
                    "/Users/AuthenticateByName",
                    json={"Username": username, "Pw": password},
                    headers={"Authorization": auth_header, "Content-Type": "application/json"},
                )
            if resp.status_code != 200:
                return None
            data = resp.json()
            user = data.get("User", {})
            return {
                "user_id": user.get("Id", ""),
                "username": user.get("Name", username),
                "is_admin": user.get("Policy", {}).get("IsAdministrator", False),
                "token": data.get("AccessToken", ""),
            }
        except Exception:
            return None

    async def refresh_library(self) -> None:
        """Trigger a full Jellyfin library refresh."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.post("/Library/Refresh")
            resp.raise_for_status()

    async def build_music_watch_map(
        self, users: list[UserInfo]
    ) -> dict[str, dict[str, bool]]:
        """Return {mb_artist_id: {user_id: watched}} for all users."""
        result: dict[str, dict[str, bool]] = {}
        for user in users:
            watched = await self.get_watched_music(user.id)
            for mb_id, played in watched.items():
                result.setdefault(mb_id, {})[user.id] = played
        return result


def make_watch_status_builder(users: list[UserInfo]):
    """Return a helper that builds a WatchStatus from a per-user dict."""
    from app.models import WatchStatus

    user_ids = [u.id for u in users]

    def build(per_user: dict[str, bool]) -> WatchStatus:
        watched = [per_user.get(uid, False) for uid in user_ids]
        return WatchStatus(
            watched_by_all=all(watched) if watched else False,
            watched_by_any=any(watched),
            watched_by_none=not any(watched),
            per_user=per_user,
        )

    return build
