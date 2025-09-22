from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class AvailabilityRequest(BaseModel):
    check_in: str
    check_out: str
    adults: int = Field(ge=1, le=8)
    children: int = Field(ge=0, le=8)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    @field_validator("check_in", "check_out")
    @classmethod
    def validate_date(cls, value: str) -> str:
        from datetime import date

        date.fromisoformat(value)
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total: Optional[float]
    currency: str
    nights: int
    price_currency: str
    availability: Dict[str, Dict[str, int]]
    prices: Dict[str, Dict[str, float]]
    raw: Dict[str, Any]
