"""Radarr API client (v3)."""
from __future__ import annotations

from typing import Optional

import httpx


def _client(url: str, api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=url.rstrip("/"),
        headers={"X-Api-Key": api_key},
        timeout=30.0,
    )


class RadarrService:
    """Async client for the Radarr v3 API."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key

    async def get_movies(self) -> list[dict]:
        """Return all movies from Radarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v3/movie")
            resp.raise_for_status()
            return resp.json()

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = True,
        add_import_exclusion: bool = True,
    ) -> None:
        """Delete a movie from Radarr, optionally removing its files."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(
                f"/api/v3/movie/{movie_id}",
                params={
                    "deleteFiles": str(delete_files).lower(),
                    "addImportExclusion": str(add_import_exclusion).lower(),
                },
            )
            resp.raise_for_status()

    async def rescan_movie(self, movie_id: int) -> None:
        """Trigger a RescanMovie command in Radarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.post(
                "/api/v3/command",
                json={"name": "RescanMovie", "movieId": movie_id},
            )
            resp.raise_for_status()

    async def health_check(self) -> bool:
        """Return True if Radarr is reachable."""
        try:
            async with _client(self.url, self.api_key) as client:
                resp = await client.get("/api/v3/system/status")
                return resp.status_code == 200
        except Exception:
            return False
