# Retell Booking Service — Python/Flask

Optimiertes, modular aufgebautes Backend für Retell AI + HotelRunner.

## Quickstart

```bash
cp .env.example .env
# .env mit HotelRunner-Token/ID und Tool-Secret füllen

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py  # lokal
```

### Health
- `GET /healthz` → `ok`
- `GET /__routes` → listet registrierte Routen
- `GET /retell/tool/whoami` → Status + Config (X-Tool-Secret optional)

### Availability (öffentlich)
- `POST /retell/public/check_availability`
```json
{
  "check_in": "2025-10-01",
  "check_out": "2025-10-11",
  "adults": 2,
  "children": 0,
  "currency": "TRY"
}
```
Antwort enthält `availability`, `prices`, `price_currency`, `total`, `raw`.

### Offer (Retell Tool)
- `POST /retell/tool/compose_offer`
  - Header: `X-Tool-Secret`
  - Body: `{ "availability_result": {...}, "display_currency": "EUR" }`
  - Antwort: Preis in Zielwährung + FX-Rate.

## Deployment auf Render
1. Repo zu GitHub pushen
2. Render → **New > Web Service**
3. **Environment**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
6. **Health Check**: `/healthz`
7. **Environment Variables** (Render Dashboard):
   - `HOTELRUNNER_TOKEN`
   - `HR_ID` / `HOTELRUNNER_HR_ID` / `HOTELRUNNER_ID`
   - `HOTELRUNNER_BASE_URL=https://api2.hotelrunner.com`
   - `HOTELRUNNER_APPS_BASE_URL=https://app.hotelrunner.com/api/v2/apps`
   - `HOTELRUNNER_CURRENCY_URL=https://app.hotelrunner.com/api/currency/currencies.json`
   - `PROPERTY_BASE_CURRENCY` (z. B. `TRY`)
   - `TOOL_SECRET`
   - `FX_DEFAULT_TRY_EUR` (Fallback optional)
   - `FX_CACHE_MINUTES` (Default 30, optional)
   - `FX_API_URL` (Default `https://api.exchangerate.host/latest`, optional)
   - `LOG_LEVEL` (z. B. `INFO`)

> Render setzt `PORT` automatisch; nicht überschreiben.

## Tests
```bash
python3 -m pytest -q
```

## Changelog (Kurz)
- Modularisierte Settings (core/logging/fx)
- HotelRunner-Client (rooms, reservations, summary, currencies)
- Availability-Service mit Pydantic-Responses
- FX-Rates via REST + Cache
- `/retell/tool/whoami` & Request-ID-Logging
