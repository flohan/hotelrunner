"""
Offer composition based on availability and FX (Render-ready)
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any
from currency_resolver import apply_fx

@dataclass
class OfferInput:
    availability_result: Dict[str, Any]  # expects { total, currency, nights, raw }
    display_currency: str
    fx_rate: Decimal
    fx_timestamp: str  # ISO8601
    include_breakfast: bool = True

def compose_offer(inp: OfferInput) -> Dict[str, Any]:
    base_currency = str(inp.availability_result.get("currency", "TRY")).upper()
    base_total = Decimal(str(inp.availability_result.get("total", 0)))
    nights = int(inp.availability_result.get("nights", 1))

    # Minor units (vereinfachend pauschal 2, ausreichend für EUR/TRY/USD/GBP)
    base_minor_digits = 2
    base_minor = int(base_total * (10 ** base_minor_digits))

    display_minor, fx_rate_used = apply_fx(
        base_amount_minor=base_minor,
        base_currency=base_currency,
        display_currency=inp.display_currency.upper(),
        rate=inp.fx_rate
    )

    display_total = (Decimal(display_minor) / (10 ** 2))

    return {
        "base_currency": base_currency,
        "base_total": float(base_total),
        "display_currency": inp.display_currency.upper(),
        "display_total": float(display_total),
        "fx_rate_used": float(fx_rate_used),
        "fx_timestamp": inp.fx_timestamp,
        "nights": nights,
        "conditions": {
            "breakfast_included": bool(inp.include_breakfast),
            "cancellation_policy": "Free cancellation up to 7 days before check-in."
        }
    }
