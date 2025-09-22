from __future__ import annotations

import datetime as dt
from typing import Iterable

import requests

from .common import APPS_BASE_URL, apps_params


def fetch_reservations(
    start_date: dt.date,
    end_date: dt.date,
    per_page: int = 100,
) -> list[dict]:
    reservations: list[dict] = []
    page = 1
    while True:
        params = apps_params(
            {
                "from_date": start_date.strftime("%Y-%m-%d"),
                "to_date": end_date.strftime("%Y-%m-%d"),
                "page": page,
                "per_page": per_page,
                "undelivered": "false",
                "modified": "false",
                "booked": "false",
            }
        )
        url = f"{APPS_BASE_URL}/reservations"
        response = requests.get(url, params=params, timeout=20)
        if response.status_code >= 400:
            snippet = (response.text or "")[:180]
            raise RuntimeError(f"HotelRunner reservations error {response.status_code}: {snippet}")
        batch = (response.json() or {}).get("reservations", [])
        reservations.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return reservations
