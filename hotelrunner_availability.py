"""HotelRunner Availability client returning availability and prices."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import get_settings

LOGGER = logging.getLogger(__name__)
SETTINGS = get_settings()
API_PATH = "/api/v1/availability/search.json"
TOKEN = SETTINGS.require("HOTELRUNNER_TOKEN", SETTINGS.hotelrunner_token)
HR_ID = SETTINGS.require("HR_ID", SETTINGS.hotelrunner_hr_id)


class AvailabilityRequest(BaseModel):
    check_in: str
    check_out: str
    adults: int = Field(ge=1, le=8)
    children: int = Field(ge=0, le=8)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    @field_validator("check_in", "check_out")
    @classmethod
    def validate_date(cls, value: str) -> str:
        dt.date.fromisoformat(value)
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value


def _clean_token(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[len("bearer ") :]
    return token


def _hr_url(path: str) -> str:
    base = SETTINGS.hotelrunner_base_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _headers() -> Dict[str, str]:
    token = _clean_token(TOKEN)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0",
    }


def _apps_params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = {"token": TOKEN, "hr_id": HR_ID}
    if extra:
        params.update(extra)
    return params


def _fetch_rooms() -> list[dict[str, Any]]:
    url = f"{SETTINGS.hotelrunner_apps_base_url.rstrip('/')}/rooms"
    resp = requests.get(url, params=_apps_params(), timeout=15)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:180]
        LOGGER.warning("HR rooms upstream: status=%s url=%s snippet=%s", resp.status_code, url, snippet)
        raise RuntimeError(f"HotelRunner rooms error {resp.status_code}: {snippet}")
    return (resp.json() or {}).get("rooms", [])


def _fetch_reservations(from_date: dt.date, to_date: dt.date, per_page: int = 100) -> list[dict[str, Any]]:
    reservations: list[dict[str, Any]] = []
    page = 1
    while True:
        params = _apps_params(
            {
                "from_date": from_date.strftime("%Y-%m-%d"),
                "to_date": to_date.strftime("%Y-%m-%d"),
                "page": page,
                "per_page": per_page,
                "undelivered": "false",
                "modified": "false",
                "booked": "false",
            }
        )
        url = f"{SETTINGS.hotelrunner_apps_base_url.rstrip('/')}/reservations"
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code >= 400:
            snippet = (resp.text or "")[:180]
            LOGGER.warning(
                "HR reservations upstream: status=%s url=%s snippet=%s",
                resp.status_code,
                resp.url,
                snippet,
            )
            raise RuntimeError(f"HotelRunner reservations error {resp.status_code}: {snippet}")
        batch = (resp.json() or {}).get("reservations", [])
        reservations.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return reservations


def _parse_room_metadata(rooms: Iterable[dict[str, Any]]) -> tuple[dict[str, int], dict[str, float], str]:
    totals: dict[str, int] = {}
    prices: dict[str, float] = {}
    currency = SETTINGS.property_base_currency

    for room in rooms:
        room_type = room.get("name") or room.get("room_type_name") or room.get("room_type")
        if not room_type:
            continue
        try:
            totals[room_type] = int(
                room.get("total_count") or room.get("total") or room.get("count") or 0
            )
        except (TypeError, ValueError):
            totals[room_type] = 0
        sales_currency = room.get("sales_currency") or room.get("currency")
        if isinstance(sales_currency, str) and sales_currency.strip():
            currency = sales_currency.strip().upper()
        price_value = room.get("price") or room.get("default_price") or room.get("base_price")
        try:
            prices[room_type] = float(price_value)
        except (TypeError, ValueError):
            prices[room_type] = 0.0

    return totals, prices, currency


def _build_availability_matrix(
    payload: AvailabilityRequest,
    rooms: Iterable[dict[str, Any]],
    reservations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    totals, price_map, currency = _parse_room_metadata(rooms)

    start = dt.date.fromisoformat(payload.check_in)
    end = dt.date.fromisoformat(payload.check_out)

    booked: dict[str, dict[str, int]] = {}
    for res in reservations:
        room_type = res.get("room_type") or res.get("room_type_name")
        check_in = res.get("check_in")
        check_out = res.get("check_out")
        if not (room_type and check_in and check_out):
            continue
        try:
            res_start = dt.date.fromisoformat(check_in)
            res_end = dt.date.fromisoformat(check_out)
        except ValueError:
            continue
        current = max(res_start, start)
        while current < min(res_end, end):
            key = current.isoformat()
            booked.setdefault(key, {}).setdefault(room_type, 0)
            booked[key][room_type] += 1
            current += dt.timedelta(days=1)

    availability: dict[str, dict[str, int]] = {}
    prices: dict[str, dict[str, float]] = {}
    current = start
    while current < end:
        key = current.isoformat()
        availability[key] = {}
        prices[key] = {}
        for room_type, total in totals.items():
            count = booked.get(key, {}).get(room_type, 0)
            availability[key][room_type] = max(total - count, 0)
            prices[key][room_type] = price_map.get(room_type, 0.0)
        current += dt.timedelta(days=1)

    return {"price_currency": currency, "availability": availability, "prices": prices}


def _fetch_summary(payload: AvailabilityRequest) -> dict[str, Any]:
    url = _hr_url(API_PATH)
    body = {
        "hr_id": HR_ID,
        "check_in": payload.check_in,
        "check_out": payload.check_out,
        "adults": payload.adults,
        "children": payload.children or 0,
        "currency": payload.currency or SETTINGS.property_base_currency,
    }
    resp = requests.post(url, headers=_headers(), json=body, timeout=15)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:180]
        LOGGER.warning("HR summary upstream: status=%s url=%s snippet=%s", resp.status_code, url, snippet)
        raise RuntimeError(f"HotelRunner error {resp.status_code}: {snippet}")
    data = resp.json()
    currency = (data.get("currency") or body.get("currency") or SETTINGS.property_base_currency).upper()
    nights = (dt.date.fromisoformat(payload.check_out) - dt.date.fromisoformat(payload.check_in)).days
    return {
        "total": data.get("total"),
        "currency": currency,
        "nights": nights,
        "raw_summary": data,
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.5, max=2.0))
def get_availability(payload: AvailabilityRequest) -> Dict[str, Any]:
    summary = _fetch_summary(payload)
    raw_summary = summary.pop("raw_summary", None)
    rooms = _fetch_rooms()
    reservations = _fetch_reservations(
        dt.date.fromisoformat(payload.check_in) - dt.timedelta(days=30),
        dt.date.fromisoformat(payload.check_out) + dt.timedelta(days=1),
    )
    matrices = _build_availability_matrix(payload, rooms, reservations)

    return {
        **summary,
        **matrices,
        "raw": {
            "summary": raw_summary,
            "rooms": rooms,
            "reservations": reservations,
        },
    }
