import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (40, 120, 40)).save(buf, format="PNG")
    return buf.getvalue()


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_predict_returns_contract_fields():
    res = client.post("/predict", files={"image": ("leaf.png", _png(), "image/png")})
    assert res.status_code == 200
    body = res.json()
    assert body["label"] in {"healthy", "peacock_spot", "aculus_olearius", "olive_knot"}
    assert {"labelFr", "confidence", "probabilities", "advice", "modelVersion", "mock"} <= body.keys()
    assert abs(sum(body["probabilities"].values()) - 1) < 1e-3


def test_rejects_non_image():
    res = client.post("/predict", files={"image": ("notes.txt", b"hello", "text/plain")})
    assert res.status_code == 422
