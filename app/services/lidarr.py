"""Lidarr API client (v1)."""
from __future__ import annotations

import httpx


def _client(url: str, api_key: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=url.rstrip("/"),
        headers={"X-Api-Key": api_key},
        timeout=30.0,
    )


class LidarrService:
    """Async client for the Lidarr v1 API."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url.rstrip("/")
        self.api_key = api_key

    async def get_artists(self) -> list[dict]:
        """Return all artists from Lidarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/artist")
            resp.raise_for_status()
            return resp.json()

    async def get_disk_space(self) -> list[dict]:
        """Return disk space info [{path, label, freeSpace, totalSpace}, ...]."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/diskspace")
            resp.raise_for_status()
            return resp.json()

    async def get_root_folders(self) -> list[dict]:
        """Return configured root folders [{path, freeSpace, ...}, ...] (media library paths)."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/rootfolder")
            resp.raise_for_status()
            return resp.json()

    async def get_all_albums(self) -> list[dict]:
        """Return all albums across all artists."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/album")
            resp.raise_for_status()
            return resp.json()

    async def get_albums(self, artist_id: int) -> list[dict]:
        """Return all albums for an artist."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/album", params={"artistId": artist_id})
            resp.raise_for_status()
            return resp.json()

    async def get_tracks(self, album_id: int) -> list[dict]:
        """Return all tracks for an album."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/track", params={"albumId": album_id})
            resp.raise_for_status()
            return resp.json()

    async def get_track_files(self, artist_id: int) -> list[dict]:
        """Return all track files for an artist."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get(
                "/api/v1/trackfile", params={"artistId": artist_id}
            )
            resp.raise_for_status()
            return resp.json()

    async def get_album_title(self, album_id: int) -> str:
        """Return the title of a single album by its ID."""
        info = await self.get_album_info(album_id)
        return info["title"]

    async def get_album_info(self, album_id: int) -> dict:
        """Return title and sizeOnDisk for a single album."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/album", params={"albumId": album_id})
            resp.raise_for_status()
            data = resp.json()
            if data:
                a = data[0]
                return {
                    "title": a.get("title", f"Album {album_id}"),
                    "size": a.get("statistics", {}).get("sizeOnDisk", 0),
                }
            return {"title": f"Album {album_id}", "size": 0}

    async def get_track_files_by_ids(self, track_file_ids: list[int]) -> list[dict]:
        """Return track file objects for the given IDs."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get(
                "/api/v1/trackfile",
                params=[("trackFileIds", fid) for fid in track_file_ids],
            )
            resp.raise_for_status()
            return resp.json()

    async def get_album_track_files(self, album_id: int) -> list[dict]:
        """Return all track file objects for a specific album (includes size)."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get("/api/v1/trackfile", params={"albumId": album_id})
            resp.raise_for_status()
            return resp.json()

    async def get_album_track_file_ids(self, album_id: int) -> list[int]:
        """Return track file IDs for a specific album."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.get(
                "/api/v1/trackfile", params={"albumId": album_id}
            )
            resp.raise_for_status()
            return [f["id"] for f in resp.json()]

    async def delete_artist(
        self,
        artist_id: int,
        delete_files: bool = True,
        add_import_exclusion: bool = True,
    ) -> None:
        """Delete an artist and optionally their files from Lidarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(
                f"/api/v1/artist/{artist_id}",
                params={
                    "deleteFiles": str(delete_files).lower(),
                    "addImportExclusion": str(add_import_exclusion).lower(),
                },
            )
            resp.raise_for_status()

    async def delete_album(
        self,
        album_id: int,
        delete_files: bool = True,
        add_import_exclusion: bool = True,
    ) -> None:
        """Delete an album and optionally its files from Lidarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.delete(
                f"/api/v1/album/{album_id}",
                params={
                    "deleteFiles": str(delete_files).lower(),
                    "addImportExclusion": str(add_import_exclusion).lower(),
                },
            )
            resp.raise_for_status()

    async def delete_track_files(self, track_file_ids: list[int]) -> None:
        """Bulk-delete track files."""
        if not track_file_ids:
            return
        async with _client(self.url, self.api_key) as client:
            resp = await client.request(
                "DELETE",
                "/api/v1/trackfile/bulk",
                json={"trackFileIds": track_file_ids},
            )
            resp.raise_for_status()

    async def rescan_artist(self, artist_id: int) -> None:
        """Trigger a RescanArtist command in Lidarr."""
        async with _client(self.url, self.api_key) as client:
            resp = await client.post(
                "/api/v1/command",
                json={"name": "RescanArtist", "artistId": artist_id},
            )
            resp.raise_for_status()

    async def health_check(self) -> bool:
        """Return True if Lidarr is reachable."""
        try:
            async with _client(self.url, self.api_key) as client:
                resp = await client.get("/api/v1/system/status")
                return resp.status_code == 200
        except Exception:
            return False
