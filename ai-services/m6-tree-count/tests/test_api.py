import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def _png(w: int = 400, h: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (120, 110, 80)).save(buf, format="PNG")
    return buf.getvalue()


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_count_matches_boxes_and_returns_annotated_image():
    res = client.post("/predict", files={"image": ("parcel.png", _png(), "image/png")})
    assert res.status_code == 200
    body = res.json()
    assert body["treeCount"] == len(body["boxes"]) > 0
    assert body["annotatedImageBase64"]


def test_rejects_non_image():
    res = client.post("/predict", files={"image": ("x.txt", b"nope", "text/plain")})
    assert res.status_code == 422
