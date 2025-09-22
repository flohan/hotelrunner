from __future__ import annotations

from urllib.parse import urljoin

from settings import get_settings

_settings = get_settings()
APPS_BASE_URL = _settings.hotelrunner_apps_base_url.rstrip("/")
BASE_URL = _settings.hotelrunner_base_url.rstrip("/")
PROPERTY_CURRENCY = _settings.property_base_currency


def clean_token(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[len("bearer ") :]
    return token


def headers() -> dict[str, str]:
    token = clean_token(get_token())
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0",
    }


def apps_params(extra: dict | None = None) -> dict:
    params = {"token": get_token(), "hr_id": get_hr_id()}
    if extra:
        params.update(extra)
    return params


def build_url(path: str) -> str:
    return urljoin(f"{BASE_URL}/", path.lstrip("/"))


def get_token() -> str:
    return _settings.require("HOTELRUNNER_TOKEN", _settings.hotelrunner_token)


def get_hr_id() -> str:
    return _settings.require("HR_ID", _settings.hotelrunner_hr_id)
