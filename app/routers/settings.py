"""Settings page: configure all service connections via the web UI."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import load_raw_config, save_config
from app.services.discovery import discover_all
from app.services.jellyfin import JellyfinService
from app.services.radarr import RadarrService
from app.services.sonarr import SonarrService
from app.services.lidarr import LidarrService

router = APIRouter(prefix="/settings", tags=["settings"])
from app.templates_env import templates


def _raw_to_form(raw: dict) -> dict:
    """Flatten raw config dict into template-friendly keys."""
    jf = raw.get("jellyfin") or {}
    ra = raw.get("radarr") or {}
    so = raw.get("sonarr") or {}
    li = raw.get("lidarr") or {}
    return {
        "jellyfin_url": jf.get("url", ""),
        "jellyfin_api_key": jf.get("api_key", ""),
        "radarr_url": ra.get("url", ""),
        "radarr_api_key": ra.get("api_key", ""),
        "sonarr_url": so.get("url", ""),
        "sonarr_api_key": so.get("api_key", ""),
        "lidarr_url": li.get("url", ""),
        "lidarr_api_key": li.get("api_key", ""),
        "dry_run": raw.get("dry_run", True),
        "add_import_exclusion": raw.get("add_import_exclusion", True),
    }


def _require_admin(request: Request) -> bool:
    """Return True if the logged-in user is an admin (or config is not yet complete)."""
    from app.config import is_config_complete
    if not is_config_complete():
        return True  # setup mode — allow anyone
    user = getattr(request.state, "user", None)
    return bool(user and user.get("is_admin"))


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, saved: bool = False, error: str = ""):
    """Render the settings form, pre-populated from config and auto-discovery."""
    if not _require_admin(request):
        return templates.TemplateResponse(
            request, "error.html",
            {"message": "Settings are only accessible to Jellyfin administrators."},
            status_code=403,
        )
    from app.config import is_config_complete
    raw = load_raw_config()
    form_values = _raw_to_form(raw)

    # Auto-discover *arr credentials from mounted config.xml files when not yet configured.
    discovery: dict = {}
    if not is_config_complete():
        discovered = discover_all()
        for name, result in discovered.items():
            discovery[name] = {"status": result.status, "url": result.url, "api_key": result.api_key}
            if result.status == "discovered":
                if not form_values.get(f"{name}_url"):
                    form_values[f"{name}_url"] = result.url
                if not form_values.get(f"{name}_api_key"):
                    form_values[f"{name}_api_key"] = result.api_key

    return templates.TemplateResponse(
        request,
        "settings.html",
        {"saved": saved, "error": error, "discovery": discovery, **form_values},
    )


@router.post("", response_class=RedirectResponse)
async def settings_save(  # noqa: PLR0913
    request: Request,
    jellyfin_url: Annotated[str, Form()] = "",
    jellyfin_api_key: Annotated[str, Form()] = "",
    radarr_url: Annotated[str, Form()] = "",
    radarr_api_key: Annotated[str, Form()] = "",
    sonarr_url: Annotated[str, Form()] = "",
    sonarr_api_key: Annotated[str, Form()] = "",
    lidarr_url: Annotated[str, Form()] = "",
    lidarr_api_key: Annotated[str, Form()] = "",
):
    """Save the settings form to config.yaml."""
    if not _require_admin(request):
        return RedirectResponse("/", status_code=303)
    # Checkboxes are absent from form data when unchecked — read the raw form body
    form = await request.form()
    dry_run = "dry_run" in form
    add_import_exclusion = "add_import_exclusion" in form

    jellyfin_url = jellyfin_url.strip()
    jellyfin_api_key = jellyfin_api_key.strip()

    if not jellyfin_url or not jellyfin_api_key:
        return RedirectResponse(
            "/settings?error=Jellyfin+URL+and+API+key+are+required",
            status_code=303,
        )

    config_data: dict = {
        "jellyfin": {"url": jellyfin_url, "api_key": jellyfin_api_key},
        "dry_run": dry_run,
        "add_import_exclusion": add_import_exclusion,
    }

    if radarr_url.strip() and radarr_api_key.strip():
        config_data["radarr"] = {"url": radarr_url.strip(), "api_key": radarr_api_key.strip()}

    if sonarr_url.strip() and sonarr_api_key.strip():
        config_data["sonarr"] = {"url": sonarr_url.strip(), "api_key": sonarr_api_key.strip()}

    if lidarr_url.strip() and lidarr_api_key.strip():
        config_data["lidarr"] = {"url": lidarr_url.strip(), "api_key": lidarr_api_key.strip()}

    try:
        save_config(config_data)
    except OSError as exc:
        return RedirectResponse(
            f"/settings?error=Could+not+write+config:+{exc}",
            status_code=303,
        )

    return RedirectResponse("/settings?saved=1", status_code=303)


@router.post("/language")
async def set_language(language: Annotated[str, Form()]):
    """Set the UI language cookie and redirect back to /settings."""
    from fastapi.responses import RedirectResponse
    resp = RedirectResponse("/settings", status_code=303)
    from app.i18n import SUPPORTED_LANGUAGES
    if language in SUPPORTED_LANGUAGES:
        resp.set_cookie("selectarr_lang", language, max_age=60*60*24*365, httponly=False, samesite="lax")
    return resp


@router.post("/test/{service}", response_class=HTMLResponse)
async def test_connection(service: str, request: Request):
    """HTMX endpoint: test connectivity to a service and return a status badge.

    Reads {service}_url and {service}_api_key from the form, matching the field
    names used in settings.html so the current typed values are used directly.
    """
    form = await request.form()
    url = str(form.get(f"{service}_url", "") or form.get("url", "")).strip()
    api_key = str(form.get(f"{service}_api_key", "") or form.get("api_key", "")).strip()

    if not url or not api_key:
        return HTMLResponse(_badge("warning", "Enter URL and API key first"))

    try:
        if service == "jellyfin":
            jf = JellyfinService(url, api_key)
            users = await jf.get_users()
            return HTMLResponse(_badge("ok", f"Connected &mdash; {len(users)} user(s)"))

        elif service == "radarr":
            ok = await RadarrService(url, api_key).health_check()
            return HTMLResponse(_badge("ok" if ok else "error", "Connected" if ok else "Unreachable"))

        elif service == "sonarr":
            ok = await SonarrService(url, api_key).health_check()
            return HTMLResponse(_badge("ok" if ok else "error", "Connected" if ok else "Unreachable"))

        elif service == "lidarr":
            ok = await LidarrService(url, api_key).health_check()
            return HTMLResponse(_badge("ok" if ok else "error", "Connected" if ok else "Unreachable"))

        else:
            return HTMLResponse(_badge("error", "Unknown service"))

    except Exception as exc:
        short = str(exc)[:120]
        return HTMLResponse(_badge("error", f"Error: {short}"))


def _badge(kind: str, text: str) -> str:
    tone = {"ok": "success", "error": "danger", "warning": "warning"}.get(kind, "muted")
    return f'<span class="pill pill-{tone}"><span class="pill-dot"></span>{text}</span>'
