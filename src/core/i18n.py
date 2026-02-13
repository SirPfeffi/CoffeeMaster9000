import json
from functools import lru_cache
from pathlib import Path


I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
SUPPORTED_LANGS = {"de", "en"}
DEFAULT_LANG = "de"


@lru_cache(maxsize=8)
def _load_messages(lang: str):
    code = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    file_path = I18N_DIR / f"messages_{code}.json"
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def translate(key: str, lang: str, fallback: str = None):
    messages = _load_messages(lang)
    if key in messages:
        return messages[key]
    default_messages = _load_messages(DEFAULT_LANG)
    if key in default_messages:
        return default_messages[key]
    return fallback or key
