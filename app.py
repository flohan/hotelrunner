from __future__ import annotations

import json
import datetime as dt
from datetime import timezone
from decimal import Decimal

from flask import Flask, jsonify, request
from pydantic import ValidationError

from compose_offer import OfferInput, compose_offer
from currency_resolver import decide_currency
from hotelrunner_availability import AvailabilityRequest, get_availability
from settings import get_settings

settings = get_settings()
PORT = int(settings.PORT)
TOOL_SECRET = settings.require("TOOL_SECRET")
PROPERTY_BASE_CURRENCY = settings.PROPERTY_BASE_CURRENCY

app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/__routes")
def routes():
    return jsonify(sorted([str(r) for r in app.url_map.iter_rules()]))

@app.post("/retell/public/check_availability")
def public_check_availability():
    try:
        data = request.get_json(force=True, silent=False)
        payload = AvailabilityRequest(**data)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "details": json.loads(ve.json())}), 400
    except Exception as e:
        return jsonify({"error": "bad_request", "details": str(e)}), 400

    try:
        result = get_availability(payload)
        # Keine PII zurückgeben, nur fachliche Daten
        return jsonify({
            "total": result.get("total"),
            "currency": result.get("currency"),
            "nights": result.get("nights"),
            "price_currency": result.get("price_currency"),
            "availability": result.get("availability"),
            "prices": result.get("prices"),
            "raw": result.get("raw"),
        }), 200
    except Exception as err:
        return jsonify({
            "error": "upstream_error",
            "message": "Availability service unavailable",
        }), 502

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
            property_base_currency=PROPERTY_BASE_CURRENCY
        )

        base_currency = availability_result.get("currency", "TRY").upper()
        # Demo-FX (ersetzen durch echten Provider/Cache)
        fx_rate = settings.get_fx_default(base_currency, display_currency)

        offer = compose_offer(OfferInput(
            availability_result=availability_result,
            display_currency=display_currency,
            fx_rate=fx_rate,
            fx_timestamp=dt.datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            include_breakfast=True
        ))
        return jsonify(offer), 200
    except Exception as e:
        return jsonify({"error": "compose_failed", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
