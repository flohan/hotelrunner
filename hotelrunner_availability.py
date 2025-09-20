"""HotelRunner Availability Client + Validation (Render-ready)"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from settings import get_settings

_s = get_settings()
HOTELRUNNER_BASE_URL = _s.HOTELRUNNER_BASE_URL.rstrip("/")
HOTELRUNNER_TOKEN = _s.require("HOTELRUNNER_TOKEN")
HR_ID = _s.require("HR_ID")

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

def _headers() -> Dict[str, str]:
    token = HOTELRUNNER_TOKEN.strip()
    if token.lower().startswith("bearer "):
        auth_value = token
    else:
        auth_value = f"Bearer {token}"

    return {
        "Authorization": auth_value,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0"
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.5, max=2.0))
def get_availability(payload: AvailabilityRequest) -> Dict[str, Any]:
    url = f"{HOTELRUNNER_BASE_URL}/availability/search"
    params = {
        "hr_id": HR_ID,
        "token": HOTELRUNNER_TOKEN,
    }
    body = {
        "check_in": payload.check_in,
        "check_out": payload.check_out,
        "adults": payload.adults,
        "children": payload.children,
    }
    if payload.currency:
        body["currency"] = payload.currency

    resp = requests.post(url, params=params, headers=_headers(), json=body, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"HotelRunner error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    total = data.get("total")
    currency = (data.get("currency") or body.get("currency") or _s.PROPERTY_BASE_CURRENCY).upper()
    nights = (dt.date.fromisoformat(payload.check_out) - dt.date.fromisoformat(payload.check_in)).days
    return {"total": total, "currency": currency, "nights": nights, "raw": data}
