from __future__ import annotations

import requests

import logging

from .common import apps_params, build_url, get_hr_id, headers

LOGGER = logging.getLogger(__name__)

API_PATH = "/api/v1/availability/search.json"


def fetch_summary(body: dict) -> dict:
    payload = {"hr_id": get_hr_id(), **body}
    url = build_url(API_PATH)
    response = requests.post(
        url,
        params=apps_params(),
        headers=headers(),
        json=payload,
        timeout=15,
    )
    if response.status_code >= 400:
        snippet = (response.text or "")[:180]
        LOGGER.warning(
            "HotelRunner summary error status=%s url=%s snippet=%s",
            response.status_code,
            response.url,
            snippet,
        )
        raise RuntimeError(f"HotelRunner summary error {response.status_code}: {snippet}")
    return response.json()
