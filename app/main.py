"""Selectarr — main FastAPI application entry point."""
from __future__ import annotations

import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_config, is_config_complete
from app.database import init_db
from app.version import __version__
from app.routers import home, logs, movies, music, series
from app.routers import settings as settings_router
from app.routers import auth as auth_router
from app.services.auth import _COOKIE, get_session

# Paths exempt from config gate
_SETTINGS_EXEMPT = ("/settings", "/docs", "/redoc", "/openapi", "/status", "/static")
# Paths exempt from auth gate
_AUTH_EXEMPT = ("/login", "/logout", "/static", "/docs", "/redoc", "/openapi", "/status")


class LangMiddleware(BaseHTTPMiddleware):
    """Read selectarr_lang cookie → request.state.lang."""
    async def dispatch(self, request: Request, call_next):
        lang = request.cookies.get("selectarr_lang", "en")
        if lang not in ("en", "nl", "de", "es", "pt", "fr", "zh", "ar"):
            lang = "en"
        request.state.lang = lang
        return await call_next(request)


class ConfigGateMiddleware(BaseHTTPMiddleware):
    """Redirect to /settings when config is missing or incomplete."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in _SETTINGS_EXEMPT):
            return await call_next(request)
        if not is_config_complete():
            return RedirectResponse("/settings", status_code=302)
        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):
    """Require a valid session for all non-exempt routes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Always stamp state so templates can safely read request.state.user
        request.state.user = None
        if any(path.startswith(p) for p in _AUTH_EXEMPT):
            return await call_next(request)
        # /settings is accessible without login when config is still being set up
        if path.startswith("/settings") and not is_config_complete():
            return await call_next(request)
        session = get_session(request.cookies.get(_COOKIE))
        request.state.user = session
        if session is None:
            return RedirectResponse("/login", status_code=302)
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Selectarr",
    description=(
        "Manual media management tool integrating Jellyfin, Radarr, Sonarr, and Lidarr. "
        "Selectively delete media at any granularity with watched-status filtering."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Middleware is applied inside-out: last added = outermost = runs first.
# Desired order: ConfigGate → AuthMiddleware → LangMiddleware → app
# So add LangMiddleware first (innermost), then AuthMiddleware, then ConfigGate (outermost).
app.add_middleware(LangMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(ConfigGateMiddleware)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_version"] = __version__

app.include_router(auth_router.router)
app.include_router(home.router)
app.include_router(settings_router.router)
app.include_router(movies.router)
app.include_router(series.router)
app.include_router(music.router)
app.include_router(logs.router)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> HTMLResponse:
    """Render a full traceback page for any unhandled server error."""
    tb = traceback.format_exc()
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": f"{type(exc).__name__}: {exc}", "traceback": tb},
        status_code=500,
    )




@app.get("/status", summary="Health check and configuration status")
async def status(request: Request, format: str = ""):
    """Return service connectivity status as HTML (browser) or JSON (API clients)."""
    from app.services.radarr import RadarrService
    from app.services.sonarr import SonarrService
    from app.services.lidarr import LidarrService
    from app.services.jellyfin import JellyfinService

    if not is_config_complete():
        data: dict = {"configured": False}
        if _wants_html(request, format):
            return templates.TemplateResponse(
                request, "status.html",
                {"version": __version__, "configured": False, "dry_run": False, "services": {
                    "jellyfin": {"status": "not configured"},
                    "radarr":   {"status": "not configured"},
                    "sonarr":   {"status": "not configured"},
                    "lidarr":   {"status": "not configured"},
                }},
            )
        return data

    config = get_config()
    services: dict = {}

    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    try:
        users = await jf.get_users()
        services["jellyfin"] = {"status": "ok", "users": len(users)}
    except Exception as exc:
        services["jellyfin"] = {"status": "error", "message": str(exc)}

    for name, svc_cfg, Svc in [
        ("radarr",  config.radarr,  RadarrService),
        ("sonarr",  config.sonarr,  SonarrService),
        ("lidarr",  config.lidarr,  LidarrService),
    ]:
        if svc_cfg:
            ok = await Svc(svc_cfg.url, svc_cfg.api_key).health_check()
            services[name] = {"status": "ok" if ok else "error"}
        else:
            services[name] = {"status": "not configured"}

    if _wants_html(request, format):
        return templates.TemplateResponse(
            request, "status.html",
            {"version": __version__, "configured": True, "dry_run": config.dry_run, "services": services},
        )

    return {"configured": True, "dry_run": config.dry_run, **services}


def _wants_html(request: Request, format: str) -> bool:
    if format == "json":
        return False
    accept = request.headers.get("accept", "")
    return "text/html" in accept
