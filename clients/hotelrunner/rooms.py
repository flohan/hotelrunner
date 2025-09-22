from __future__ import annotations

import requests

from .common import APPS_BASE_URL, apps_params


def fetch_rooms() -> list[dict]:
    url = f"{APPS_BASE_URL}/rooms"
    response = requests.get(url, params=apps_params(), timeout=15)
    if response.status_code >= 400:
        snippet = (response.text or "")[:180]
        raise RuntimeError(f"HotelRunner rooms error {response.status_code}: {snippet}")
    payload = response.json() or {}
    return payload.get("rooms", [])
