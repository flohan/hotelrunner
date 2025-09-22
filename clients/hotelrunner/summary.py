from __future__ import annotations

import requests

from .common import HR_ID, build_url, headers

API_PATH = "/api/v1/availability/search.json"


def fetch_summary(body: dict) -> dict:
    payload = {"hr_id": HR_ID, **body}
    url = build_url(API_PATH)
    response = requests.post(url, headers=headers(), json=payload, timeout=15)
    if response.status_code >= 400:
        snippet = (response.text or "")[:180]
        raise RuntimeError(f"HotelRunner summary error {response.status_code}: {snippet}")
    return response.json()
