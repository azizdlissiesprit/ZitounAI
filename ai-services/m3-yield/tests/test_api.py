from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_parcel_estimate_with_tree_count():
    res = client.post("/predict", json={"governorate": "Sfax", "season": 2026, "treeCount": 200})
    assert res.status_code == 200
    body = res.json()
    assert body["parcelLowKg"] <= body["parcelEstimateKg"] <= body["parcelHighKg"]
    assert body["regionalProductionTonnes"] > 0


def test_regional_only_without_tree_count():
    body = client.post("/predict", json={"governorate": "Sousse", "season": 2025}).json()
    assert body["parcelEstimateKg"] is None
