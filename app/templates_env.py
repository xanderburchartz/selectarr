"""Shared Jinja2Templates instance used by all routers."""
from fastapi.templating import Jinja2Templates
from app.version import __version__
from app.i18n import get_translator, SUPPORTED_LANGUAGES

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["app_version"] = __version__
templates.env.globals["SUPPORTED_LANGUAGES"] = SUPPORTED_LANGUAGES

_orig_tr = templates.TemplateResponse

def _i18n_response(request, name, context=None, **kwargs):
    ctx = dict(context or {})
    lang = getattr(getattr(request, "state", None), "lang", "en")
    ctx.setdefault("t", get_translator(lang))
    ctx.setdefault("current_lang", lang)
    return _orig_tr(request, name, ctx, **kwargs)

templates.TemplateResponse = _i18n_response
