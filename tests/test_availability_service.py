import datetime as dt
from decimal import Decimal

import pytest

from services.availability.models import AvailabilityRequest
from services.availability.service import _build_availability_matrix, _parse_room_metadata


def test_parse_room_metadata_extracts_totals_prices_and_currency():
    rooms = [
        {"name": "Standard", "total_count": 10, "price": 150, "sales_currency": "EUR"},
        {"room_type_name": "Deluxe", "total": 5, "default_price": 220},
    ]

    totals, price_map, currency = _parse_room_metadata(rooms)

    assert totals == {"Standard": 10, "Deluxe": 5}
    assert price_map == {"Standard": 150.0, "Deluxe": 220.0}
    assert currency == "EUR"


def test_build_availability_matrix_counts_bookings():
    payload = AvailabilityRequest(
        check_in="2025-10-01",
        check_out="2025-10-04",
        adults=2,
        children=0,
    )
    rooms = [
        {"name": "Standard", "total_count": 2, "price": 150, "sales_currency": "EUR"},
        {"name": "Deluxe", "total_count": 1, "price": 220, "sales_currency": "EUR"},
    ]
    reservations = [
        {"room_type": "Standard", "check_in": "2025-10-01", "check_out": "2025-10-03"},
        {"room_type": "Standard", "check_in": "2025-10-02", "check_out": "2025-10-04"},
        {"room_type": "Deluxe", "check_in": "2025-10-01", "check_out": "2025-10-02"},
    ]

    matrix, _ = _build_availability_matrix(payload, rooms, reservations)

    assert matrix["price_currency"] == "EUR"
    assert matrix["nights"] == 3
    assert matrix["availability"] == {
        "2025-10-01": {"Standard": 1, "Deluxe": 0},
        "2025-10-02": {"Standard": 0, "Deluxe": 1},
        "2025-10-03": {"Standard": 1, "Deluxe": 1},
    }
    assert matrix["prices"]["2025-10-01"]["Standard"] == 150.0
