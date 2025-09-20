"""HotelRunner Availability Client + Validation (Render-ready)."""
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
_settings = get_settings()
HOTELRUNNER_TOKEN = _settings.require("HOTELRUNNER_TOKEN")
HR_ID = _settings.require("HR_ID")
API_PATH = "/api/v1/availability/search.json"
APPS_BASE_URL = _settings.HOTELRUNNER_APPS_BASE_URL.rstrip("/")
CURRENCY_URL = _settings.HOTELRUNNER_CURRENCY_URL

class AvailabilityRequest(BaseModel):
    check_in: str
    check_out: str
    adults: int = Field(ge=1, le=8)
    children: int = Field(ge=0, le=8)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    @field_validator("check_in", "check_out")
    @classmethod
    def validate_date(cls, v: str) -> str:
        dt.date.fromisoformat(v)  # raises on error
        return v

    @field_validator("currency")
    @classmethod
    def upper_iso4217(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

def _hr_url(path: str) -> str:
    base = _settings.HOTELRUNNER_BASE_URL.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _headers() -> Dict[str, str]:
    token = _clean_token(HOTELRUNNER_TOKEN)

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0",
    }

def _apps_params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    params = {"token": HOTELRUNNER_TOKEN, "hr_id": HR_ID}
    if extra:
        params.update(extra)
    return params


def _clean_token(token: str) -> str:
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[len("bearer ") :]
    return token


def _fetch_rooms() -> list[dict[str, Any]]:
    url = f"{APPS_BASE_URL}/rooms"
    resp = requests.get(url, params=_apps_params(), timeout=15)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:180]
        LOGGER.warning("HR rooms upstream: status=%s url=%s snippet=%s", resp.status_code, url, snippet)
        raise RuntimeError(f"HotelRunner rooms error {resp.status_code}: {snippet}")
    payload = resp.json() or {}
    return payload.get("rooms", [])


def _fetch_currencies() -> list[dict[str, Any]]:
    resp = requests.get(CURRENCY_URL, params=_apps_params(), timeout=15)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:180]
        LOGGER.warning("HR currencies upstream: status=%s url=%s snippet=%s", resp.status_code, CURRENCY_URL, snippet)
        raise RuntimeError(f"HotelRunner currencies error {resp.status_code}: {snippet}")
    payload = resp.json() or {}
    currencies = payload.get("currencies")
    if isinstance(currencies, list):
        return currencies
    return payload if isinstance(payload, list) else []


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
        url = f"{APPS_BASE_URL}/reservations"
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code >= 400:
            snippet = (resp.text or "")[:180]
            LOGGER.warning("HR reservations upstream: status=%s url=%s snippet=%s", resp.status_code, resp.url, snippet)
            raise RuntimeError(f"HotelRunner reservations error {resp.status_code}: {snippet}")
        payload = resp.json() or {}
        batch = payload.get("reservations", [])
        reservations.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return reservations


def _parse_room_metadata(rooms: Iterable[dict[str, Any]]) -> tuple[dict[str, int], dict[str, float], str]:
    totals: dict[str, int] = {}
    price_map: dict[str, float] = {}
    currency = _settings.PROPERTY_BASE_CURRENCY

    for room in rooms:
        room_type = room.get("name") or room.get("room_type_name") or room.get("room_type")
        if not room_type:
            continue
        try:
            totals[room_type] = int(room.get("total_count") or room.get("total") or room.get("count") or 0)
        except (TypeError, ValueError):
            totals[room_type] = 0

        sales_currency = room.get("sales_currency") or room.get("currency")
        if isinstance(sales_currency, str) and sales_currency.strip():
            currency = sales_currency.strip().upper()

        price_value = room.get("price") or room.get("default_price") or room.get("base_price")
        try:
            price_map[room_type] = float(price_value)
        except (TypeError, ValueError):
            price_map[room_type] = 0.0

    return totals, price_map, currency


def _build_availability_matrix(
    payload: AvailabilityRequest,
    rooms: Iterable[dict[str, Any]],
    reservations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    totals, price_map, currency = _parse_room_metadata(rooms)

    start_date = dt.date.fromisoformat(payload.check_in)
    end_date = dt.date.fromisoformat(payload.check_out)

    booked: dict[str, dict[str, int]] = {}
    for res in reservations:
        check_in = res.get("check_in")
        check_out = res.get("check_out")
        room_type = res.get("room_type") or res.get("room_type_name")
        if not (check_in and check_out and room_type):
            continue
        try:
            res_start = dt.date.fromisoformat(check_in)
            res_end = dt.date.fromisoformat(check_out)
        except ValueError:
            continue

        current = max(res_start, start_date)
        while current < min(res_end, end_date):
            day_key = current.isoformat()
            booked.setdefault(day_key, {}).setdefault(room_type, 0)
            booked[day_key][room_type] += 1
            current += dt.timedelta(days=1)

    availability: dict[str, dict[str, int]] = {}
    prices: dict[str, dict[str, float]] = {}
    current = start_date
    while current < end_date:
        day_key = current.isoformat()
        availability[day_key] = {}
        prices[day_key] = {}
        for room_type, total in totals.items():
            booked_count = booked.get(day_key, {}).get(room_type, 0)
            availability[day_key][room_type] = max(total - booked_count, 0)
            prices[day_key][room_type] = price_map.get(room_type, 0.0)
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
        "currency": payload.currency or _settings.PROPERTY_BASE_CURRENCY,
    }

    resp = requests.post(url, headers=_headers(), json=body, timeout=15)
    if resp.status_code >= 400:
        snippet = (resp.text or "")[:180]
        LOGGER.warning("HR summary upstream: status=%s url=%s snippet=%s", resp.status_code, url, snippet)
        raise RuntimeError(f"HotelRunner error {resp.status_code}: {snippet}")

    data = resp.json()
    currency = (data.get("currency") or body.get("currency") or _settings.PROPERTY_BASE_CURRENCY).upper()
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
    currencies = _fetch_currencies()
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
            "currencies": currencies,
        },
    }
