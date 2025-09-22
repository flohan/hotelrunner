from __future__ import annotations

import requests

from .common import apps_params

CURRENCY_ENDPOINT = "https://app.hotelrunner.com/api/currency/currencies.json"


def fetch_currencies() -> list[dict]:
    response = requests.get(CURRENCY_ENDPOINT, params=apps_params(), timeout=15)
    if response.status_code >= 400:
        snippet = (response.text or "")[:180]
        raise RuntimeError(f"HotelRunner currencies error {response.status_code}: {snippet}")
    payload = response.json() or {}
    currencies = payload.get("currencies")
    if isinstance(currencies, list):
        return currencies
    return payload if isinstance(payload, list) else []
