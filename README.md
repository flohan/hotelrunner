# retell-agent-optimized

Optimiertes, modular aufgebautes Backend (Express) für Retell AI + HotelRunner.

## Quickstart

```bash
cp .env.example .env
# .env bearbeiten (Token/ID eintragen)

npm install
npm run dev   # lokal
# oder
npm start     # production
```

### Health
- `GET /healthz` → `{ ok: true }`
- `GET /__routes` → listet registrierte Routen

### Availability (öffentlich)
- `POST /hotelrunner/public/availability`
```json
{
  "check_in": "2025-10-01",
  "check_out": "2025-10-11",
  "adults": 2,
  "children": 0,
  "currency": "EUR"
}
```

## API-Doku (OpenAPI)
- **Swagger UI:** `GET /docs`
- **JSON:** `GET /openapi.json`

## Alias (Kompatibilität)
- `POST /retell/public/check_availability` → identisch zu `/hotelrunner/public/availability`

## Render
- Start command: `node src/index.js` (oder `npm start`)
- Node 20+

### Troubleshooting HotelRunner 404/400
Setze in `.env`:
```
HOTELRUNNER_DEBUG_LOG_REQUEST=true
HOTELRUNNER_USE_BODY_HR_ID=true
HOTELRUNNER_SMART_STRATEGY=true
HOTELRUNNER_ALT_PATHS=/availability/search,/api/availability/search
# Optional zusätzlicher Host:
# HOTELRUNNER_BASE_ALT=https://api.hotelrunner.com
```
Die Service-Schicht versucht dann mehrere **Payload-Varianten** und **Pfad-Alternativen** automatisch.

## RAW-Mode (ohne /availability/search)
Setze in `.env`:
```
HOTELRUNNER_USE_RAW=true
HOTELRUNNER_AVAILABILITY_RAW_PATH=/api/v1/availability
HOTELRUNNER_RAW_DATE_KEYS=check_in,check_out;checkin,checkout;start_date,end_date
```
Die API ruft dann den **Raw-Availability**-Endpunkt auf (GET/POST, mehrere Schlüsselvarianten) und berechnet eine einfache Inventar-Übersicht (pro Datum/Zimmertyp). 
