# Changelog

All notable changes to Selectarr are documented here.

## [0.2.4.1] — 2026-06-30

### Added

- **Free disk space on the Overview** — the summary banner now shows the
  current free space (and total) of the media drive(s), queried live from the
  `diskspace` endpoint of the configured Radarr/Sonarr/Lidarr services. Mount
  points shared across services are de-duplicated so a drive is counted once.

### Fixed

- **Overview showed stale library size after a deletion** — the Overview
  statistics are cached for 15 minutes, but the cache was not cleared after a
  delete, so freed space only appeared after the cache expired or a manual
  refresh. The cache is now invalidated on every successful movie, series, or
  music deletion, so the library size and free space update immediately.

## [0.2.4] — 2026-06-29

### Fixed

- **Whole-series deletion was unreachable** — the backend, confirmation
  drawer and "Will free" calculation for series-level deletes already
  existed (and the page subtitle advertised series-level deletion), but no
  selection ever produced the `series` action, so it could never run. The
  single "Delete selected" button is now context-aware: selecting **every**
  season of a series deletes the entire series from Sonarr (including its
  files, honouring the import-exclusion setting) and the confirmation shows
  the full series size from `statistics.sizeOnDisk`. Selecting individual
  seasons or episodes behaves exactly as before.

---

## [0.2.3] — 2026-05-19

### Fixed

- **Series delete confirmation — disk space** — "Will free" now shows the
  actual size of the selected content: full-series size comes from Sonarr's
  `statistics.sizeOnDisk`, season and episode sizes are computed by summing
  the matching episode file sizes. Previously always showed "—".
- **Series delete confirmation — button feedback** — the "Delete now" /
  "Run simulation" button now disables itself and shows "Deleting…" /
  "Running…" while the request is in flight, preventing double-submits.

---

## [0.2.2] — 2026-05-18

### Added

- **Favicon** — browser tab now shows the Selectarr icon (SVG + ICO).
- **Watch status on seasons and episodes** — expanding a series shows a
  Watched column at season and episode level with per-user granularity.
  Status is computed by aggregating episode-level `Played` flags from
  Jellyfin rather than the unreliably-updated series/season
  `PlayedPercentage`.
- **Partial watch status** — series and seasons show `Name (partial)` per
  user when some but not all episodes have been watched.
- **Disk space in music deletion confirmation** — "Will free" now shows the
  actual size of the selected artists, albums, or tracks instead of "—".
- **Loading feedback on delete buttons** — "Delete selected" shows
  "Loading…" while the confirmation request is in flight, preventing
  double-submits.

### Changed

- **Unified watch status display** — movies, series, seasons, and episodes
  now all use the same format: "Watched by all" / "Name, Name" /
  "Name (partial)" / "Unwatched". The old "Watched by: Name" label on the
  movies page is removed.
- **Simplified delete UI on the series page** — removed per-row "Delete
  series" and "Delete season" buttons; multi-select + "Delete selected" is
  now the only delete path (consistent with the music page).
- **Simplified delete UI on the music page** — removed the per-row "Delete
  artist" button and the nested album-level "Delete selected" button.

### Fixed

- **Lidarr 500 error after artist deletion** — the background refresh task
  no longer calls `RescanArtist` on a just-deleted artist. Jellyfin library
  refresh still runs.

---

## [0.2.1] — 2026-05-18

### Fixed

- **500 error on settings page** — upgraded FastAPI from 0.104.1 to 0.115.12, pulling in Starlette 0.40+ which supports the `request`-as-first-argument `TemplateResponse` API used throughout the app. The pinned 0.104.1 shipped Starlette 0.27 which still required `"request"` in the context dict, causing a `ValueError` on every page render in the Docker image.

---

## [0.2.0] — 2026-05-18

### Added

- **Auto-discovery** — on first run, Selectarr reads `/arr/{radarr,sonarr,lidarr}/config.xml` and pre-populates the Settings form with the discovered URL and API key. Each service card shows an *Auto-discovered*, *Config file not found*, or *Could not parse config* badge. Jellyfin must still be entered manually.
- **HTML status page** — `/status` now returns a styled dark-theme page when opened in a browser, showing configuration state and per-service connectivity. API clients receive the existing JSON response unchanged. `?format=json` forces JSON regardless of `Accept` header.
- **GitHub Actions workflow** — multi-arch Docker image (`linux/amd64`, `linux/arm64`) is built and published to `ghcr.io/xanderburchartz/selectarr` on every push to `main` and on version tags.
- **`docker-compose.yml` volume mounts** — three commented-out mount lines for `/arr/{radarr,sonarr,lidarr}` to support auto-discovery.
- **Community files** — `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and GitHub issue templates for bug reports and feature requests.
- **`INSTALL.md`** — full installation guide covering Docker (pull from `ghcr.io`) and local Python, Settings-page configuration, auto-discovery, config field reference, Docker networking, and troubleshooting.

### Changed

- `docker-compose.yml` now pulls the pre-built image from `ghcr.io/xanderburchartz/selectarr:latest` instead of building locally.

---

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
