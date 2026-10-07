from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_forecast_horizon_and_recommendation():
    res = client.post("/predict", json={"horizonWeeks": 6, "quantityKg": 500})
    assert res.status_code == 200
    body = res.json()
    assert len(body["forecast"]) == 6
    assert body["recommendation"] in {"SELL_NOW", "STORE"}
    assert body["currency"] == "TND"
    assert all(p["low"] <= p["price"] <= p["high"] for p in body["forecast"])


def test_defaults_without_body_fields():
    assert len(client.post("/predict", json={}).json()["forecast"]) == 8
