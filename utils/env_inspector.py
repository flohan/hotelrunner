from __future__ import annotations

import os
from typing import Dict

from settings import get_settings

SENSITIVE_PREVIEW = 4

DEFAULT_KEYS = [
    "HOTELRUNNER_TOKEN",
    "HR_ID",
    "HOTELRUNNER_HR_ID",
    "HOTELRUNNER_BASE_URL",
    "HOTELRUNNER_APPS_BASE_URL",
    "HOTELRUNNER_CURRENCY_URL",
    "PROPERTY_BASE_CURRENCY",
    "TOOL_SECRET",
    "FX_CACHE_MINUTES",
    "FX_API_URL",
    "FX_DEFAULT_TRY_EUR",
]


def inspect_environment(keys: list[str] | None = None) -> Dict[str, Dict[str, object]]:
    keys = keys or DEFAULT_KEYS
    snapshot: Dict[str, Dict[str, object]] = {}
    for key in keys:
        value = os.getenv(key)
        present = bool(value)
        preview = None
        if present and value:
            preview = value[-SENSITIVE_PREVIEW:] if len(value) > SENSITIVE_PREVIEW else value
        snapshot[key] = {"present": present, "preview": preview}
    return snapshot


def inspect_settings() -> Dict[str, object]:
    settings = get_settings()
    return {
        "port": settings.port,
        "hotelrunner_base_url": settings.hotelrunner_base_url,
        "hotelrunner_apps_base_url": settings.hotelrunner_apps_base_url,
        "property_base_currency": settings.property_base_currency,
        "tool_secret_loaded": bool(settings.tool_secret),
        "token_loaded": bool(settings.hotelrunner_token),
        "hr_id_loaded": bool(settings.hotelrunner_hr_id),
    }
