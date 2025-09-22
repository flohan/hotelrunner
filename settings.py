from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Settings:
    port: int
    hotelrunner_base_url: str
    hotelrunner_apps_base_url: str
    hotelrunner_currency_url: str
    hotelrunner_token: Optional[str]
    hotelrunner_hr_id: Optional[str]
    property_base_currency: str
    tool_secret: Optional[str]
    log_level: str

    def require(self, name: str, value: Optional[str]) -> str:
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    def get_fx_default(self, base_currency: str, display_currency: str) -> Decimal:
        if base_currency.upper() == display_currency.upper():
            return Decimal("1.0")
        env_key = f"FX_DEFAULT_{base_currency.upper()}_{display_currency.upper()}".replace("-", "_")
        value = os.getenv(env_key)
        if value:
            return Decimal(value)
        if base_currency.upper() == "TRY" and display_currency.upper() == "EUR":
            return Decimal(os.getenv("FX_DEFAULT_TRY_EUR", "0.02857"))
        return Decimal("1.0")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        port=int(os.getenv("PORT", "10000")),
        hotelrunner_base_url=os.getenv("HOTELRUNNER_BASE_URL", "https://api2.hotelrunner.com"),
        hotelrunner_apps_base_url=os.getenv(
            "HOTELRUNNER_APPS_BASE_URL", "https://app.hotelrunner.com/api/v2/apps"
        ),
        hotelrunner_currency_url=os.getenv(
            "HOTELRUNNER_CURRENCY_URL", "https://app.hotelrunner.com/api/currency/currencies.json"
        ),
        hotelrunner_token=os.getenv("HOTELRUNNER_TOKEN"),
        hotelrunner_hr_id=(
            os.getenv("HR_ID")
            or os.getenv("HOTELRUNNER_HR_ID")
            or os.getenv("HOTELRUNNER_ID")
        ),
        property_base_currency=os.getenv("PROPERTY_BASE_CURRENCY", "TRY"),
        tool_secret=os.getenv("TOOL_SECRET"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
