"""Authentication routes: login and logout."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import get_config
from app.services.auth import _COOKIE, create_session, delete_session, get_session
from app.services.jellyfin import JellyfinService

router = APIRouter(tags=["auth"])
from app.templates_env import templates


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_session(request.cookies.get(_COOKIE)):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    config = get_config()
    jf = JellyfinService(config.jellyfin.url, config.jellyfin.api_key)
    result = await jf.authenticate_user(username, password)
    if not result:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Incorrect username or password."},
            status_code=401,
        )
    token = create_session(
        result["user_id"], result["username"], result["is_admin"], result["token"]
    )
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(_COOKIE, token, httponly=True, samesite="lax", max_age=7 * 24 * 3600)
    return response


@router.post("/logout")
async def logout(request: Request):
    token = request.cookies.get(_COOKIE)
    if token:
        delete_session(token)
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(_COOKIE)
    return response
