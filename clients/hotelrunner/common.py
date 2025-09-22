from __future__ import annotations

from urllib.parse import urljoin

from settings import get_settings

_settings = get_settings()
TOKEN = _settings.require("HOTELRUNNER_TOKEN", _settings.hotelrunner_token)
HR_ID = _settings.require("HR_ID", _settings.hotelrunner_hr_id)
APPS_BASE_URL = _settings.hotelrunner_apps_base_url.rstrip("/")
BASE_URL = _settings.hotelrunner_base_url.rstrip("/")
PROPERTY_CURRENCY = _settings.property_base_currency


def clean_token(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[len("bearer ") :]
    return token


def headers() -> dict[str, str]:
    token = clean_token(TOKEN)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0",
    }


def apps_params(extra: dict | None = None) -> dict:
    params = {"token": TOKEN, "hr_id": HR_ID}
    if extra:
        params.update(extra)
    return params


def build_url(path: str) -> str:
    return urljoin(f"{BASE_URL}/", path.lstrip("/"))
