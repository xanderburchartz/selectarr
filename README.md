# Selectarr

A manual media management tool that integrates **Jellyfin**, **Radarr**, **Sonarr**, and **Lidarr**. Browse your library filtered by watch status and selectively delete media at any level of granularity — with a mandatory confirmation step and optional dry-run mode.

## Features

- **Movie management** — browse and delete movies via Radarr
- **Series management** — delete at series, season, or individual episode level via Sonarr
- **Music management** — delete artists, albums, or individual tracks via Lidarr
- **Watch-status filtering** — filter by: watched by all, watched by any, watched by a specific Jellyfin user, or not watched by anyone
- **Dry-run mode** — enabled by default; preview what would be deleted without touching any files
- **Activity log** — every action is logged with timestamp, type, title, level, and result
- **REST API** — full OpenAPI/Swagger documentation at `/docs`
- **HTMX UI** — responsive web interface with no JavaScript framework

## Stack

- Python 3.11+ · FastAPI · Uvicorn · HTMX · Jinja2 · Pico CSS · SQLite

## Installation

### Docker (recommended)

1. Copy the example configuration:
   ```bash
   mkdir config
   cp config.yaml.example config/config.yaml
   ```

2. Edit `config/config.yaml` with your service URLs and API keys.

3. Start the container:
   ```bash
   docker compose up -d
   ```

4. Open **http://localhost:8889** in your browser.

### Local development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Place your config.yaml in the project root or config/ directory
cp config.yaml.example config.yaml

uvicorn app.main:app --reload --port 8889
```

## Configuration

All configuration lives in a single `config.yaml` file mounted at `/config/config.yaml` inside the container (or found at `./config/config.yaml` / `./config.yaml` locally).

```yaml
jellyfin:
  url: "http://jellyfin:8096"
  api_key: "your-jellyfin-api-key"

radarr:
  url: "http://radarr:7878"
  api_key: "your-radarr-api-key"

sonarr:
  url: "http://sonarr:8989"
  api_key: "your-sonarr-api-key"

lidarr:
  url: "http://lidarr:8686"
  api_key: "your-lidarr-api-key"

# Simulate deletions without touching files (default: true)
dry_run: true

# Prevent re-downloading deleted content (default: true)
add_import_exclusion: true
```

Services are optional — omit any *arr block to disable that tab.

### Finding API keys

- **Jellyfin**: Dashboard → API Keys → Add API Key
- **Radarr/Sonarr/Lidarr**: Settings → General → API Key

## Usage

1. Navigate to **Movies**, **Series**, or **Music**.
2. Use the filter dropdown to narrow the list by watch status.
3. Select items using the checkboxes (or use "Select all").
4. Click **Preview deletion** — a confirmation summary appears.
5. Review the list, then click **Confirm — Delete now** (or **Simulate** in dry-run mode).
6. Check the **Logs** tab to review past actions.

### Turning off dry-run

Once you are confident in the configuration, set `dry_run: false` in `config.yaml` and restart the container.

## API

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8889/docs
- **ReDoc**: http://localhost:8889/redoc
- **Health/status**: http://localhost:8889/status

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/movies/api` | List movies with watch status |
| POST | `/movies/delete` | Delete selected movies |
| GET | `/series/api` | List series with watch status |
| POST | `/series/delete` | Delete series/season/episodes |
| GET | `/music/api` | List artists |
| POST | `/music/delete` | Delete artist/album/tracks |
| GET | `/logs/api` | Activity log entries |
| GET | `/status` | Service health check |

## Architecture

```
app/
├── main.py            # FastAPI app, lifespan, top-level routes
├── config.py          # config.yaml loader
├── models.py          # Pydantic models for all entities
├── database.py        # SQLite activity log (aiosqlite)
├── services/
│   ├── jellyfin.py    # Jellyfin API client + watch-status helpers
│   ├── radarr.py      # Radarr v3 API client
│   ├── sonarr.py      # Sonarr v3 API client
│   └── lidarr.py      # Lidarr v1 API client
├── routers/
│   ├── movies.py      # Movie routes (browse, confirm, delete)
│   ├── series.py      # Series/season/episode routes
│   ├── music.py       # Artist/album/track routes
│   └── logs.py        # Activity log routes
└── templates/
    ├── base.html       # Shared layout with nav
    ├── movies.html     # Movies page
    ├── series.html     # Series page
    ├── music.html      # Music page
    ├── logs.html       # Activity log page
    └── partials/       # HTMX-swapped fragments
```

## Platform support

The Docker image is built on `python:3.11-slim` which supports both **ARM64** (Raspberry Pi 4) and **AMD64**. Use `docker buildx build --platform linux/arm64,linux/amd64` for multi-arch images.

## About the port

Port 8889 isn't arbitrary. `X` has ASCII value 88 and `Y` has ASCII value 89 — so 8889 is a small nod to **Xander and Yvonne**, who built Selectarr to manage the media library aboard their sailing boat. Somewhere between anchorages, with a Jellyfin server humming below deck, the need for a tool like this became obvious.

If 8889 conflicts with something else on your system, change the port mapping in `docker-compose.yml` and you're good to go.

## Notes

- Jellyfin watch status is cached in memory for 5 minutes to reduce API load on large libraries.
- Series, season, and episode watch status is computed by aggregating episode-level `Played` flags from Jellyfin. Series and seasons show a per-user "partial" state when some but not all episodes have been watched. Jellyfin's own series/season `PlayedPercentage` field is not used as it may not update promptly.
- Music play-status correlation requires a MusicBrainz artist ID to be present in both Jellyfin and Lidarr.
- Deleting at season or episode level removes only the files, not the series/season metadata from Sonarr.
