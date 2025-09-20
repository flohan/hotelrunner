import json, os
from app import app

def test_healthz():
    c = app.test_client()
    r = c.get("/healthz")
    assert r.status_code == 200

def test_routes():
    c = app.test_client()
    r = c.get("/__routes")
    assert r.status_code == 200

def test_compose_offer_demo():
    c = app.test_client()
    os.environ["TOOL_SECRET"] = "CHANGE_ME"
    payload = {
        "availability_result": {"total": 43400, "currency": "TRY", "nights": 10},
        "display_currency": "EUR"
    }
    r = c.post("/retell/tool/compose_offer", data=json.dumps(payload), headers={
        "Content-Type":"application/json",
        "X-Tool-Secret":"CHANGE_ME"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["display_currency"] == "EUR"
