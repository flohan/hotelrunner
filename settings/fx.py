from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Tuple

import requests

_FX_CACHE: Dict[Tuple[str, str], Tuple[datetime, Decimal]] = {}


def get_rate(base: str, target: str) -> Decimal:
    base = base.upper()
    target = target.upper()

    cache_minutes = int(os.getenv("FX_CACHE_MINUTES", "30"))
    ttl = timedelta(minutes=cache_minutes)
    key = (base, target)
    now = datetime.now(timezone.utc)

    cached = _FX_CACHE.get(key)
    if cached and now < cached[0]:
        return cached[1]

    rate = _fetch_live_rate(base, target)
    _FX_CACHE[key] = (now + ttl, rate)
    return rate


def _fetch_live_rate(base: str, target: str) -> Decimal:
    endpoint = os.getenv("FX_API_URL", "https://api.exchangerate.host/latest")
    response = requests.get(endpoint, params={"base": base, "symbols": target}, timeout=5)
    response.raise_for_status()
    data = response.json()
    rates = data.get("rates") or {}
    if target not in rates:
        raise RuntimeError(f"FX API response missing rate for {target}")
    return Decimal(str(rates[target]))
