"""UI internationalisation helpers."""
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache

_LOCALE_DIR = Path(__file__).parent

@lru_cache(maxsize=16)
def _load(lang: str) -> dict:
    path = _LOCALE_DIR / f"{lang}.json"
    fallback = _LOCALE_DIR / "en.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        with open(fallback, encoding="utf-8") as f:
            data = json.load(f)
    # Always merge with English so missing keys degrade gracefully
    if lang != "en":
        with open(fallback, encoding="utf-8") as f:
            en = json.load(f)
        return {**en, **data}
    return data

def get_translator(lang: str = "en"):
    """Return a t(key) callable for the given language."""
    strings = _load(lang)
    def t(key: str, **kwargs) -> str:
        val = strings.get(key, key)
        return val.format(**kwargs) if kwargs else val
    return t

SUPPORTED_LANGUAGES = {
    "en": "English",
    "nl": "Nederlands",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "fr": "Français",
    "zh": "中文",
    "ar": "العربية",
}
