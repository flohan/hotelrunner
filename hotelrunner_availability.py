"""HotelRunner Availability Client + Validation (Render-ready)."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional
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
    token = HOTELRUNNER_TOKEN.strip()
    if token.lower().startswith("bearer "):
        token = token[len("bearer ") :]

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "retell-booking-service/1.0",
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.5, max=2.0))
def get_availability(payload: AvailabilityRequest) -> Dict[str, Any]:
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
        LOGGER.warning("HR upstream: status=%s url=%s snippet=%s", resp.status_code, url, snippet)
        raise RuntimeError(f"HotelRunner error {resp.status_code}: {snippet}")

    data = resp.json()
    total = data.get("total")
    currency = (data.get("currency") or body.get("currency") or _settings.PROPERTY_BASE_CURRENCY).upper()
    nights = (dt.date.fromisoformat(payload.check_out) - dt.date.fromisoformat(payload.check_in)).days
    return {"total": total, "currency": currency, "nights": nights, "raw": data}
