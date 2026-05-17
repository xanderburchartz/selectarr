"""Configuration loading, saving, and management for Selectarr."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

_CONFIG_PATHS = [
    Path("/config/config.yaml"),
    Path("./config/config.yaml"),
    Path("./config.yaml"),
]

_cached_config: Optional[AppConfig] = None


class ServiceConfig(BaseModel):
    """Connection settings for an external service."""

    url: str
    api_key: str


class AppConfig(BaseModel):
    """Root application configuration."""

    jellyfin: ServiceConfig
    radarr: Optional[ServiceConfig] = None
    sonarr: Optional[ServiceConfig] = None
    lidarr: Optional[ServiceConfig] = None
    dry_run: bool = True
    add_import_exclusion: bool = True
    # Explicitly set to True only when the user saves via the settings UI or
    # manually adds `configured: true` to config.yaml.  Prevents placeholder
    # values from a copied example file from being treated as real config.
    configured: bool = False


def _active_config_path() -> Optional[Path]:
    """Return the path of the first existing config file, or None."""
    for path in _CONFIG_PATHS:
        if path.exists():
            return path
    return None


def _write_config_path() -> Path:
    """Return the best path for writing a new config file."""
    existing = _active_config_path()
    if existing:
        return existing
    for path in _CONFIG_PATHS:
        if path.parent.exists():
            return path
    # Last resort: create ./config/ directory and write there
    fallback = _CONFIG_PATHS[1]
    fallback.parent.mkdir(parents=True, exist_ok=True)
    return fallback


def load_config() -> AppConfig:
    """Load and cache configuration from the first available config file."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    path = _active_config_path()
    if path is None:
        raise FileNotFoundError(
            f"No config file found. Searched: {[str(p) for p in _CONFIG_PATHS]}"
        )

    with open(path) as f:
        data = yaml.safe_load(f) or {}
    _cached_config = AppConfig(**data)
    return _cached_config


def get_config() -> AppConfig:
    """Return the cached application configuration."""
    return load_config()


def reload_config() -> AppConfig:
    """Force-reload configuration from disk."""
    global _cached_config
    _cached_config = None
    return load_config()


def load_raw_config() -> dict:
    """Load config as a plain dict without Pydantic validation (safe for partial configs)."""
    path = _active_config_path()
    if path is None:
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_config(data: dict) -> None:
    """Write config data to disk and invalidate the in-memory cache.

    Always stamps `configured: true` so the middleware knows the user has
    intentionally saved real credentials (not just a copied example file).
    """
    global _cached_config
    data = {**data, "configured": True}
    path = _write_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _cached_config = None


def is_config_complete() -> bool:
    """Return True only when the user has explicitly saved real credentials.

    A config.yaml copied from the example has `configured: false` (the default),
    so placeholder values never pass this check.
    """
    try:
        cfg = load_config()
        return (
            cfg.configured
            and bool(cfg.jellyfin.url.strip())
            and bool(cfg.jellyfin.api_key.strip())
        )
    except Exception:
        return False
