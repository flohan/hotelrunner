"""
HotelRunner Availability Client + Validation (Render-ready)
"""
from __future__ import annotations
import os, datetime as dt
from typing import Optional, Dict, Any
import requests
from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

HOTELRUNNER_BASE_URL = os.getenv("HOTELRUNNER_BASE_URL", "https://api2.hotelrunner.com/api/v1")
HOTELRUNNER_TOKEN = os.getenv("HOTELRUNNER_TOKEN")
HR_ID = os.getenv("HR_ID")

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
    if not HOTELRUNNER_TOKEN:
        raise RuntimeError("Missing HOTELRUNNER_TOKEN")
    return {
        "Authorization": f"Bearer {HOTELRUNNER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0"
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.5, max=2.0))
def get_availability(payload: AvailabilityRequest) -> Dict[str, Any]:
    if not HR_ID:
        raise RuntimeError("Missing HR_ID")

    url = f"{HOTELRUNNER_BASE_URL}/availability/search"
    params = {"hr_id": HR_ID}
    body = {
        "check_in": payload.check_in,
        "check_out": payload.check_out,
        "adults": payload.adults,
        "children": payload.children,
    }
    if payload.currency:
        body["currency"] = payload.currency

    resp = requests.post(url, params=params, headers=_headers(), json=body, timeout=5)
    if resp.status_code >= 400:
        raise RuntimeError(f"HotelRunner error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    total = data.get("total")
    currency = data.get("currency", body.get("currency", "TRY"))
    nights = (dt.date.fromisoformat(payload.check_out) - dt.date.fromisoformat(payload.check_in)).days
    return {"total": total, "currency": currency, "nights": nights, "raw": data}
