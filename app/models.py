"""Shared Pydantic models for API requests and responses."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class UserInfo(BaseModel):
    """A Jellyfin user."""

    id: str
    name: str


class WatchStatus(BaseModel):
    """Aggregated watch status across all Jellyfin users."""

    watched_by_all: bool
    watched_by_any: bool
    watched_by_none: bool
    per_user: dict[str, bool]  # user_id -> fully watched
    partial_per_user: dict[str, bool] = {}  # user_id -> partially watched (not fully)


class MovieItem(BaseModel):
    """A movie tracked in Radarr, enriched with Jellyfin watch data."""

    radarr_id: int
    title: str
    year: int
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    has_file: bool
    file_size_bytes: Optional[int] = None
    watch_status: Optional[WatchStatus] = None
    language: Optional[str] = None


class EpisodeItem(BaseModel):
    """A single episode tracked in Sonarr."""

    sonarr_id: int
    episode_file_id: Optional[int] = None
    title: str
    season_number: int
    episode_number: int
    has_file: bool
    file_size_bytes: Optional[int] = None
    air_date: Optional[str] = None
    watch_status: Optional[WatchStatus] = None


class SeasonItem(BaseModel):
    """A season within a series."""

    number: int
    episode_count: int
    episode_file_count: int
    size_bytes: int = 0
    watch_status: Optional[WatchStatus] = None
    episodes: list[EpisodeItem] = []


class SeriesItem(BaseModel):
    """A TV series tracked in Sonarr, enriched with Jellyfin watch data."""

    sonarr_id: int
    title: str
    year: int
    tvdb_id: Optional[int] = None
    has_files: bool
    total_size_bytes: int
    watch_status: Optional[WatchStatus] = None
    seasons: list[SeasonItem] = []
    language: Optional[str] = None


class TrackItem(BaseModel):
    """A music track tracked in Lidarr."""

    lidarr_id: int
    track_file_id: Optional[int] = None
    title: str
    track_number: Optional[str] = None
    duration_ms: Optional[int] = None
    has_file: bool
    file_size_bytes: Optional[int] = None


class AlbumItem(BaseModel):
    """A music album tracked in Lidarr."""

    lidarr_id: int
    title: str
    year: Optional[int] = None
    mb_id: Optional[str] = None
    has_files: bool
    track_count: int
    size_bytes: int = 0
    tracks: list[TrackItem] = []


class ArtistItem(BaseModel):
    """A music artist tracked in Lidarr."""

    lidarr_id: int
    name: str
    mb_id: Optional[str] = None
    album_count: int
    total_size_bytes: int = 0
    watch_status: Optional[WatchStatus] = None
    albums: list[AlbumItem] = []


# --- Delete API models ---


class DeleteMovieRequest(BaseModel):
    radarr_ids: list[int]


class DeleteSeriesRequest(BaseModel):
    sonarr_id: int
    level: str  # "series", "season", "episode"
    season_number: Optional[int] = None
    episode_file_ids: Optional[list[int]] = None


class DeleteMusicRequest(BaseModel):
    level: str  # "artist", "album", "track"
    artist_id: Optional[int] = None
    album_id: Optional[int] = None
    track_file_ids: Optional[list[int]] = None


class DeleteResultItem(BaseModel):
    title: str
    level: str
    success: bool
    message: str
    count: int = 1  # number of underlying units this row represents (e.g. episodes)


class DeleteResult(BaseModel):
    dry_run: bool
    items: list[DeleteResultItem]
    total_success: int
    total_error: int


# --- Activity log models ---


class LogEntry(BaseModel):
    id: int
    timestamp: str
    media_type: str  # "movie", "series", "music"
    title: str
    level: str  # "movie", "series", "season", "episode", "artist", "album", "track"
    dry_run: bool
    success: bool
    details: Optional[str] = None
