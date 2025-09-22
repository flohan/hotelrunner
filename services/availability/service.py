from __future__ import annotations

import datetime as dt
from typing import Dict

from clients.hotelrunner.currencies import fetch_currencies
from clients.hotelrunner.reservations import fetch_reservations
from clients.hotelrunner.rooms import fetch_rooms
from clients.hotelrunner.summary import fetch_summary
from clients.hotelrunner.common import PROPERTY_CURRENCY
from services.availability.models import AvailabilityRequest, AvailabilityResponse


def get_availability(payload: AvailabilityRequest) -> AvailabilityResponse:
    summary = fetch_summary(
        {
            "check_in": payload.check_in,
            "check_out": payload.check_out,
            "adults": payload.adults,
            "children": payload.children or 0,
            "currency": payload.currency or PROPERTY_CURRENCY,
        }
    )

    rooms = fetch_rooms()
    reservations = fetch_reservations(
        dt.date.fromisoformat(payload.check_in) - dt.timedelta(days=30),
        dt.date.fromisoformat(payload.check_out) + dt.timedelta(days=1),
    )
    availability_matrix = _build_availability_matrix(payload, rooms, reservations)
    raw = {
        "summary": summary,
        "rooms": rooms,
        "reservations": reservations,
        "currencies": fetch_currencies(),
    }

    return AvailabilityResponse(
        total=_safe_float(summary.get("total")),
        currency=(summary.get("currency") or PROPERTY_CURRENCY).upper(),
        nights=availability_matrix["nights"],
        price_currency=availability_matrix["price_currency"],
        availability=availability_matrix["availability"],
        prices=availability_matrix["prices"],
        raw=raw,
    )


def _build_availability_matrix(
    payload: AvailabilityRequest,
    rooms: list[dict],
    reservations: list[dict],
) -> Dict[str, object]:
    totals, price_map, currency = _parse_room_metadata(rooms)
    start = dt.date.fromisoformat(payload.check_in)
    end = dt.date.fromisoformat(payload.check_out)

    booked: Dict[str, Dict[str, int]] = {}
    for reservation in reservations:
        room_type = reservation.get("room_type") or reservation.get("room_type_name")
        check_in = reservation.get("check_in")
        check_out = reservation.get("check_out")
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

    availability: Dict[str, Dict[str, int]] = {}
    prices: Dict[str, Dict[str, float]] = {}
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

    nights = (end - start).days
    return {
        "price_currency": currency,
        "availability": availability,
        "prices": prices,
        "nights": nights,
    }


def _parse_room_metadata(rooms: list[dict]) -> tuple[Dict[str, int], Dict[str, float], str]:
    totals: Dict[str, int] = {}
    price_map: Dict[str, float] = {}
    currency = PROPERTY_CURRENCY

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
            price_map[room_type] = float(price_value)
        except (TypeError, ValueError):
            price_map[room_type] = 0.0

    return totals, price_map, currency


def _safe_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
