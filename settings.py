from __future__ import annotations
import os
import logging
from functools import lru_cache
from decimal import Decimal

class Settings:
    # Render setzt PORT automatisch – hier nur Fallback
    PORT: int = int(os.getenv("PORT", "10000"))

    # HotelRunner
    HOTELRUNNER_BASE_URL: str = os.getenv("HOTELRUNNER_BASE_URL", "https://api2.hotelrunner.com")
    HOTELRUNNER_APPS_BASE_URL: str = os.getenv(
        "HOTELRUNNER_APPS_BASE_URL", "https://app.hotelrunner.com/api/v2/apps"
    )
    HOTELRUNNER_CURRENCY_URL: str = os.getenv(
        "HOTELRUNNER_CURRENCY_URL", "https://app.hotelrunner.com/api/currency/currencies.json"
    )
    HOTELRUNNER_TOKEN: str | None = os.getenv("HOTELRUNNER_TOKEN")
    # Aliase: HR_ID oder HOTELRUNNER_HR_ID
    HR_ID: str | None = (
        os.getenv("HR_ID")
        or os.getenv("HOTELRUNNER_HR_ID")
        or os.getenv("HOTELRUNNER_ID")
    )

    # App
    PROPERTY_BASE_CURRENCY: str = os.getenv("PROPERTY_BASE_CURRENCY", "TRY")
    TOOL_SECRET: str | None = os.getenv("TOOL_SECRET")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def require(self, key: str) -> str:
        val = getattr(self, key, None)
        if not val:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return val

    def get_fx_default(self, base_currency: str, display_currency: str) -> Decimal:
        """
        Liest FX-Overrides wie FX_DEFAULT_TRY_EUR, sonst fallback 1.0
        """
        if base_currency.upper() == display_currency.upper():
            return Decimal("1.0")
        env_key = f"FX_DEFAULT_{base_currency.upper()}_{display_currency.upper()}".replace("-", "_")
        val = os.getenv(env_key)
        if val is not None:
            return Decimal(val)
        # bekannter Demo-Fallback (TRY->EUR), sonst 1.0
        if base_currency.upper() == "TRY" and display_currency.upper() == "EUR":
            return Decimal(os.getenv("FX_DEFAULT_TRY_EUR", "0.02857"))
        return Decimal("1.0")

def _configure_logging(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    _configure_logging(s.LOG_LEVEL)
    return s
