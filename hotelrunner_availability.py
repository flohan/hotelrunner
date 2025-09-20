import json
import os
import sys
from datetime import datetime, timedelta

import requests

# Deine HotelRunner-Credentials (werden aus der Umgebung gelesen)
def _require_env(name: str) -> str:
    """Fetch a required environment variable or exit with a helpful message."""
    value = os.getenv(name)
    if value:
        return value
    print(f"[error] Missing environment variable: {name}", file=sys.stderr)
    print("        Export the variable before running the script.", file=sys.stderr)
    sys.exit(1)


TOKEN = _require_env("HOTELRUNNER_TOKEN")
HR_ID = _require_env("HOTELRUNNER_ID")

# Basis-URL für HotelRunner API
BASE_URL = "https://app.hotelrunner.com/api/v2/apps"

def get_reservations(from_date, to_date, page=1, per_page=50):
    """
    Holt Reservations von HotelRunner für einen Datumsbereich.
    Handhabt Paging, um alle Daten zu holen.
    """
    params = {
        "token": TOKEN,
        "hr_id": HR_ID,
        "from_date": from_date.strftime("%Y-%m-%d"),
        "to_date": to_date.strftime("%Y-%m-%d"),  # Ergänzt für besseren Filter
        "page": page,
        "per_page": per_page,
        "undelivered": "false",  # Alle holen, nicht nur ungelieferte
        "modified": "false",     # Nur neue, anpassen bei Bedarf
        "booked": "false"
    }
    try:
        response = requests.get(
            f"{BASE_URL}/reservations", params=params, timeout=15
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"HotelRunner request failed: {exc}") from exc

    return response.json()

def calculate_availability(start_date_str, end_date_str, total_rooms_per_type):
    """
    Berechnet Verfügbarkeit basierend auf Reservations.
    total_rooms_per_type: Dict wie {'Standard Room': 10, 'Deluxe Room': 5}
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # Hole alle Reservations (mit Paging)
    all_reservations = []
    page = 1
    per_page = 50
    while True:
        data = get_reservations(
            start_date - timedelta(days=30),
            end_date + timedelta(days=1),
            page=page,
            per_page=per_page,
        )
        reservations = data.get("reservations", [])
        all_reservations.extend(reservations)
        if len(reservations) < per_page:
            break
        page += 1
    
    # Gruppiere gebuchte Zimmer pro Tag und Typ
    booked_by_date_and_type = {}
    for res in all_reservations:
        if "check_in" not in res or "check_out" not in res or "room_type" not in res:
            continue  # Überspringe ungültige Reservations
        check_in = datetime.strptime(res["check_in"], "%Y-%m-%d")
        check_out = datetime.strptime(res["check_out"], "%Y-%m-%d")
        room_type = res["room_type"]  # Anpassen, falls Feldname anders (z.B. 'room_type_name')
        current_date = max(check_in, start_date)
        while current_date < min(check_out, end_date + timedelta(days=1)):
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str not in booked_by_date_and_type:
                booked_by_date_and_type[date_str] = {}
            if room_type not in booked_by_date_and_type[date_str]:
                booked_by_date_and_type[date_str][room_type] = 0
            booked_by_date_and_type[date_str][room_type] += 1  # Angenommen, eine Res pro Zimmer; bei Multi-Rooms anpassen
            current_date += timedelta(days=1)
    
    # Berechne Verfügbarkeit
    availability = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        availability[date_str] = {}
        for room_type, total in total_rooms_per_type.items():
            booked = booked_by_date_and_type.get(date_str, {}).get(room_type, 0)
            available = total - booked
            availability[date_str][room_type] = max(available, 0)  # Keine negativen Werte
        current_date += timedelta(days=1)
    
    return availability

if __name__ == "__main__":
    # Beispielaufruf (passe die Daten an)
    total_rooms = {
        "Standard Room": 20,
        "Deluxe Room": 10,
    }  # Vorab via GET /api/v2/apps/rooms abrufen und parsen

    try:
        availability = calculate_availability(
            "2025-09-25", "2025-09-30", total_rooms
        )
    except RuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(availability, indent=4))
