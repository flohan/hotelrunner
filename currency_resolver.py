"""
Currency resolution & FX helpers (Render-ready)
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

COUNTRY_TO_CURRENCY = {
    "DE": "EUR", "AT": "EUR", "NL": "EUR", "FR": "EUR", "ES": "EUR", "IT": "EUR",
    "TR": "TRY", "GB": "GBP", "US": "USD", "CH": "CHF", "SE": "SEK"
}

CURRENCY_MINOR_UNITS = {
    "EUR": 2, "TRY": 2, "USD": 2, "GBP": 2, "JPY": 0, "CHF": 2, "SEK": 2
}

def decide_currency(
    user_choice: Optional[str],
    channel_default: Optional[str],
    phone_country: Optional[str],
    ip_country: Optional[str],
    property_base_currency: str
) -> str:
    if user_choice: return user_choice.upper()
    if channel_default: return channel_default.upper()
    for country in (phone_country, ip_country):
        if country and country.upper() in COUNTRY_TO_CURRENCY:
            return COUNTRY_TO_CURRENCY[country.upper()]
    return property_base_currency.upper()

def round_money(amount: Decimal, currency: str) -> Decimal:
    digits = CURRENCY_MINOR_UNITS.get(currency.upper(), 2)
    q = Decimal(10) ** -digits
    return amount.quantize(q, rounding=ROUND_HALF_UP)

def apply_fx(base_amount_minor: int, base_currency: str, display_currency: str, rate: Decimal) -> Tuple[int, Decimal]:
    base_digits = CURRENCY_MINOR_UNITS.get(base_currency.upper(), 2)
    display_digits = CURRENCY_MINOR_UNITS.get(display_currency.upper(), 2)

    base_amount = (Decimal(base_amount_minor) / (Decimal(10) ** base_digits))
    display_amount = round_money(base_amount * rate, display_currency)
    display_minor = int(display_amount * (Decimal(10) ** display_digits))
    return display_minor, rate.quantize(Decimal("0.00001"))
