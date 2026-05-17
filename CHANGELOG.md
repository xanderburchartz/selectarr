# Changelog

All notable changes to Selectarr are documented here.

## [0.1.0] — 2026-05-17

Initial release.

### Features

**Authentication**
- Jellyfin-based login with server-side sessions (7-day TTL)
- Secure `httponly` session cookie, logout support
- Settings page restricted to Jellyfin administrators
- Unauthenticated access to `/settings` during initial setup

**Overview**
- Library statistics dashboard: downloaded counts, total size, last added/deleted per service
- Movies count filters to `hasFile=true`; seasons count filters to `episodeFileCount > 0`; music counts filter to artists/albums/tracks with downloaded files
- 15-minute server-side cache with force-refresh endpoint

**Movies (Radarr)**
- Browse all downloaded movies with title, year, file size, and per-user watch status
- Filter by: all, watched by all, watched by any, unwatched, watched by specific user
- Multi-select with select-all checkbox
- Dry-run preview and live deletion with automatic Radarr rescan + Jellyfin library refresh
- Import exclusion support

**Series (Sonarr)**
- Browse all series with expandable seasons and episodes
- Season-level and episode-level granular deletion
- Mixed-mode deletion (some full seasons, some individual episodes)
- Per-user watch status at series level
- Filter by watch status
- Sortable Size column at series, season, and episode levels

**Music (Lidarr)**
- Browse all artists with downloaded content; expandable albums and tracks
- Artist-level, album-level, and track-level deletion
- Mixed-mode deletion across artists/albums/tracks
- Per-user listen status at artist level
- Filter by listen status
- Sortable Size column at artist, album, and track levels

**Sorting**
- Click Size column header to sort descending; click again for ascending
- Sorting via HTMX — no full page reload
- Independent sort state per expanded section

**Navigation**
- Collapsible left sidebar with icon-only mode (persisted via `localStorage`)
- Mobile bottom navigation bar (< 768 px)
- Active route highlighting

**Settings**
- Configure Jellyfin, Radarr, Sonarr, and Lidarr connections via the web UI
- Live connection test for each service (HTMX badge)
- Dry-run toggle and import exclusion toggle
- Config persisted to `config/config.yaml`

**Activity Log**
- Persistent SQLite log of all delete actions (dry-run and live)
- Timestamped entries with media type, title, level, and success/failure

**Infrastructure**
- FastAPI + Uvicorn, Jinja2 templates, HTMX 1.9.10
- Docker and Docker Compose support
- Default port 8889 (ASCII X=88, Y=89 — a nod to the creators)
- Single-source version number in `app/version.py`
- Config-gate middleware: redirects to `/settings` when not yet configured
