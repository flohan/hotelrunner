from __future__ import annotations

import datetime as dt
import json
from datetime import timezone
from decimal import Decimal

from flask import Flask, jsonify, request
from pydantic import ValidationError

from compose_offer import OfferInput, compose_offer
from currency_resolver import decide_currency
from hotelrunner_availability import AvailabilityRequest, get_availability
from settings import configure_logging, get_settings

configure_logging()
settings = get_settings()
PORT = settings.port
TOOL_SECRET = settings.require("TOOL_SECRET", settings.tool_secret)
PROPERTY_BASE_CURRENCY = settings.property_base_currency

app = Flask(__name__)


@app.get("/healthz")
def healthz() -> tuple[str, int]:
    return "ok", 200


@app.get("/__routes")
def routes():
    return jsonify(sorted([str(rule) for rule in app.url_map.iter_rules()]))


@app.post("/retell/public/check_availability")
def public_check_availability():
    try:
        data = request.get_json(force=True, silent=False)
        payload = AvailabilityRequest(**data)
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": json.loads(exc.json())}), 400
    except Exception as exc:
        return jsonify({"error": "bad_request", "details": str(exc)}), 400

    try:
        result = get_availability(payload)
        return jsonify(
            {
                "total": result.get("total"),
                "currency": result.get("currency"),
                "nights": result.get("nights"),
                "price_currency": result.get("price_currency"),
                "availability": result.get("availability"),
                "prices": result.get("prices"),
                "raw": result.get("raw"),
            }
        )
    except Exception as exc:
        return (
            jsonify({"error": "upstream_error", "message": "Availability service unavailable"}),
            502,
        )


@app.post("/retell/tool/compose_offer")
def tool_compose_offer():
    if request.headers.get("X-Tool-Secret") != TOOL_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    try:
        body = request.get_json(force=True)
        availability_result = body["availability_result"]
        display_currency = body.get("display_currency") or decide_currency(
            user_choice=body.get("user_choice"),
            channel_default=body.get("channel_default"),
            phone_country=body.get("phone_country"),
            ip_country=body.get("ip_country"),
            property_base_currency=PROPERTY_BASE_CURRENCY,
        )
        base_currency = availability_result.get("currency", PROPERTY_BASE_CURRENCY).upper()
        fx_rate = settings.get_fx_default(base_currency, display_currency)

        offer = compose_offer(
            OfferInput(
                availability_result=availability_result,
                display_currency=display_currency,
                fx_rate=fx_rate,
                fx_timestamp=dt.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
        )
        return jsonify(offer)
    except Exception as exc:
        return jsonify({"error": "compose_failed", "message": str(exc)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
