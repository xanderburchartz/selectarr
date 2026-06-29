"""Sonarr API client (v3)."""
from __future__ import annotations

import httpx


def _client(url: str, api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=url.rstrip("/"),
        headers={"X-Api-Key": api_key},
        timeout=30.0,
    )


class SonarrService:
    """Async client for the Sonarr v3 API."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key

    async def get_series(self) -> list[dict]:
        """Return all series from Sonarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v3/series")
            resp.raise_for_status()
            return resp.json()

    async def get_episodes(self, series_id: int) -> list[dict]:
        """Return all episodes for a series."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v3/episode", params={"seriesId": series_id})
            resp.raise_for_status()
            return resp.json()

    async def get_episode_files(self, series_id: int) -> list[dict]:
        """Return all episode files for a series."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get(
                "/api/v3/episodefile", params={"seriesId": series_id}
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_series(
        self,
        series_id: int,
        delete_files: bool = True,
        add_import_exclusion: bool = True,
    ) -> None:
        """Delete an entire series from Sonarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(
                f"/api/v3/series/{series_id}",
                params={
                    "deleteFiles": str(delete_files).lower(),
                    "addImportExclusion": str(add_import_exclusion).lower(),
                },
            )
            resp.raise_for_status()

    async def delete_episode_files(self, episode_file_ids: list[int]) -> None:
        """Bulk-delete episode files by their file IDs."""
        if not episode_file_ids:
            return
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(
                "/api/v3/episodefile/bulk",
                json={"episodeFileIds": episode_file_ids},
            )
            resp.raise_for_status()

    async def delete_episode_file(self, episode_file_id: int) -> None:
        """Delete a single episode file."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(f"/api/v3/episodefile/{episode_file_id}")
            resp.raise_for_status()

    async def get_season_episode_file_ids(
        self, series_id: int, season_number: int
    ) -> list[int]:
        """Return all episode file IDs for a specific season."""
        files = await self.get_episode_files(series_id)
        return [
            f["id"]
            for f in files
            if f.get("seasonNumber") == season_number
        ]

    async def rescan_series(self, series_id: int) -> None:
        """Trigger a RescanSeries command in Sonarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.post(
                "/api/v3/command",
                json={"name": "RescanSeries", "seriesId": series_id},
            )
            resp.raise_for_status()

    async def get_language_profiles(self) -> dict[int, str]:
        """Return {id: name} for Sonarr language profiles (v3). Returns {} on v4 or error."""
        try:
            async with _client(self.url, self.api_key) as client:
                resp = await client.get("/api/v3/languageprofile")
                if resp.status_code == 200:
                    return {p["id"]: p["name"] for p in resp.json()}
        except Exception:
            pass
        return {}

    async def health_check(self) -> bool:
        """Return True if Sonarr is reachable."""
        try:
            async with _client(self.url, self.api_key) as client:
                resp = await client.get("/api/v3/system/status")
                return resp.status_code == 200
        except Exception:
            return False
