import json
import os

os.environ.setdefault("HOTELRUNNER_TOKEN", "dummy-token")
os.environ.setdefault("HR_ID", "dummy-hr")
os.environ.setdefault("TOOL_SECRET", "CHANGE_ME")

from app import app  # noqa: E402  pylint: disable=wrong-import-position


def test_healthz():
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200


def test_routes():
    client = app.test_client()
    response = client.get("/__routes")
    assert response.status_code == 200


def test_compose_offer_demo():
    client = app.test_client()
    payload = {
        "availability_result": {"total": 43400, "currency": "TRY", "nights": 10},
        "display_currency": "EUR",
    }
    response = client.post(
        "/retell/tool/compose_offer",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json", "X-Tool-Secret": "CHANGE_ME"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["display_currency"] == "EUR"
