from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_predict_accepts_camel_case_and_returns_7_days():
    res = client.post("/predict", json={"latitude": 34.74, "longitude": 10.76, "treeCount": 250, "areaHa": 2.5})
    assert res.status_code == 200
    body = res.json()
    assert len(body["days"]) == 7
    assert {"date", "et0Mm", "rainMm", "waterNeedMm", "litersPerTree", "irrigate"} <= body["days"][0].keys()
    assert body["days"][0]["litersPerTree"] is not None
    assert isinstance(body["alerts"], list)


def test_rejects_invalid_latitude():
    assert client.post("/predict", json={"latitude": 120, "longitude": 10}).status_code == 422
