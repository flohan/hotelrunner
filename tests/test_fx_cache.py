import os
from decimal import Decimal

import pytest

from settings.fx import _FX_CACHE, get_rate


@pytest.fixture(autouse=True)
def clear_cache(monkeypatch):
    _FX_CACHE.clear()
    monkeypatch.setenv("FX_API_URL", "https://api.exchangerate.host/latest")
    monkeypatch.setenv("FX_CACHE_MINUTES", "0")  # immediate refresh for tests


def test_get_rate_caches_after_first_call(monkeypatch):
    calls = []

    def fake_fetch(url, params, timeout):
        calls.append(params)
        class FakeResp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"rates": {"EUR": 0.02857}}
        return FakeResp()

    monkeypatch.setattr("settings.fx.requests.get", fake_fetch)

    first = get_rate("TRY", "EUR")
    second = get_rate("TRY", "EUR")

    assert first == Decimal("0.02857")
    assert second == Decimal("0.02857")
    assert len(calls) == 2  # cache TTL set to 0, so fetch twice


def test_get_rate_reuses_cache(monkeypatch):
    monkeypatch.setenv("FX_CACHE_MINUTES", "60")
    responses = []

    def fake_fetch(url, params, timeout):
        responses.append(params)
        class FakeResp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"rates": {"EUR": 0.03}}
        return FakeResp()

    monkeypatch.setattr("settings.fx.requests.get", fake_fetch)

    first = get_rate("TRY", "EUR")
    second = get_rate("TRY", "EUR")

    assert first == Decimal("0.03")
    assert second == Decimal("0.03")
    assert len(responses) == 1
