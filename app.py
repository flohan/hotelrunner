from __future__ import annotations
import os, json, datetime as dt
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pydantic import ValidationError
from decimal import Decimal

from hotelrunner_availability import AvailabilityRequest, get_availability
from currency_resolver import decide_currency
from compose_offer import compose_offer, OfferInput

load_dotenv()  # Render ignoriert .env; Env kommt aus Dashboard, aber lokal hilfreich.
PORT = int(os.getenv("PORT", "10000"))
TOOL_SECRET = os.getenv("TOOL_SECRET", "CHANGE_ME")
PROPERTY_BASE_CURRENCY = os.getenv("PROPERTY_BASE_CURRENCY", "TRY")

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
            "raw": result.get("raw")
        }), 200
    except Exception:
        return jsonify({"error": "upstream_error", "message": "Availability service unavailable"}), 502

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
        if base_currency == display_currency.upper():
            fx_rate = Decimal("1.0")
        else:
            fx_env_key = f"FX_DEFAULT_{base_currency}_{display_currency}".upper().replace("-", "_")
            fx_rate = Decimal(os.getenv(fx_env_key, os.getenv("FX_DEFAULT_TRY_EUR", "0.02857")))

        offer = compose_offer(OfferInput(
            availability_result=availability_result,
            display_currency=display_currency,
            fx_rate=fx_rate,
            fx_timestamp=dt.datetime.utcnow().isoformat() + "Z",
            include_breakfast=True
        ))
        return jsonify(offer), 200
    except Exception as e:
        return jsonify({"error": "compose_failed", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
