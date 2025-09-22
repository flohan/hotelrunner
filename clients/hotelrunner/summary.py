from __future__ import annotations

import requests

from .common import build_url, get_hr_id, headers

API_PATH = "/api/v1/availability/search.json"


def fetch_summary(body: dict) -> dict:
    payload = {"hr_id": get_hr_id(), **body}
    url = build_url(API_PATH)
    response = requests.post(url, headers=headers(), json=payload, timeout=15)
    if response.status_code >= 400:
        snippet = (response.text or "")[:180]
        raise RuntimeError(f"HotelRunner summary error {response.status_code}: {snippet}")
    return response.json()
