# Retell Booking Service — Render.com Starter (Python/Flask)

Produktionsnahes Starterpaket für **Render.com** (kein lokaler Betrieb nötig).
- Endpunkte: 
  - `POST /retell/public/check_availability` → HotelRunner `/availability/search`
  - `POST /retell/tool/compose_offer` → Angebot (Währungslogik + FX-Fixierung)
  - `GET /healthz`, `GET /__routes`
- Bereit für **Render Web Service** (Procfile + `render.yaml`), Gunicorn, Healthcheck.
- Logging ohne PII (keine Geheimnisse im Log).

## Deploy auf Render (empfohlen)
1. Forke/Push dieses Repo nach GitHub.
2. In Render „**New +**“ → **Web Service** → GitHub Repo auswählen.
3. **Environment**: `Python 3` (Auto).  
4. **Build Command**: `pip install -r requirements.txt`  
   **Start Command**: *wird vom Procfile automatisch gesetzt* (`gunicorn ...`).
5. **Health Check Path**: `/healthz`
6. **Environment Variables** (Dashboard → *Environment*):
   - `HOTELRUNNER_TOKEN` = *Bearer Token*
   - `HR_ID` (Alias: `HOTELRUNNER_HR_ID`) = *HotelRunner ID*
   - `HOTELRUNNER_BASE_URL` = `https://api2.hotelrunner.com/api/v1`
   - `PROPERTY_BASE_CURRENCY` = `TRY` (oder Basis deiner Property)
   - `TOOL_SECRET` = *geheimes Token für /retell/tool/*
   - `FX_DEFAULT_TRY_EUR` = `0.02857` (nur als Demo!)
   - Optionale Paare `FX_DEFAULT_<BASE>_<DISPLAY>` (z. B. `FX_DEFAULT_TL_USD`)
   - `LOG_LEVEL` = `INFO`

> Render setzt automatisch `PORT`. Nicht überschreiben.

### Test-Calls (nach Deploy)
```bash
# Availability (Public)
curl -s -X POST https://<your-render-url>/retell/public/check_availability   -H "Content-Type: application/json"   -d '{"check_in":"2025-10-01","check_out":"2025-10-11","adults":2,"children":0,"currency":"TRY"}' | jq .

# Offer Compose (Tool, Secret-Header)
curl -s -X POST https://<your-render-url>/retell/tool/compose_offer   -H "Content-Type: application/json" -H "X-Tool-Secret: $TOOL_SECRET"   -d '{"availability_result":{"total":43400,"currency":"TRY","nights":10}, "display_currency":"EUR"}' | jq .
```

---

## OpenAPI (Kurz)
Siehe `openapi.yaml` (Basis-Spezifikation für deine Endpunkte).

## Sicherheit
- Keine Secrets ins Log. Header `Authorization`, E-Mail etc. werden nicht geloggt.
- Tool-Endpunkte sind per `X-Tool-Secret` geschützt.
- Pydantic-Validation, Timeouts, Retries (Tenacity).

## CI (optional)
Füge später GitHub Actions hinzu (Lint/Tests/Smoke).
