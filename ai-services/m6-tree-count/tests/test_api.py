"""API contract: status codes and response schema (with the model if present, else mock mode)."""

import base64
import json

import cv2
import numpy as np
import pytest

from app.main import MAX_UPLOAD_BYTES


def _png(w: int = 400, h: int = 300) -> bytes:
    img = np.full((h, w, 3), (80, 110, 120), dtype=np.uint8)
    return cv2.imencode(".png", img)[1].tobytes()


def _post(client, data: dict | None = None, image: bytes | None = None, content_type: str = "image/png"):
    files = {"image": ("parcel.png", _png() if image is None else image, content_type)}
    return client.post("/count-trees", files=files, data=data or {})


@pytest.fixture
def mock_mode(client):
    """Force the mock detector (regular grid of trees), even when the real model is loaded."""
    saved, client.app.state.counter = client.app.state.counter, None
    yield client
    client.app.state.counter = saved


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and isinstance(body["modelLoaded"], bool)


def test_rejects_wrong_file_type(client):
    assert _post(client, image=b"hello", content_type="text/plain").status_code == 415


def test_rejects_too_big_image(client):
    assert _post(client, image=b"0" * (MAX_UPLOAD_BYTES + 1)).status_code == 413


def test_rejects_unreadable_image_and_bad_polygon(client):
    assert _post(client, image=b"not really a png").status_code == 422
    assert _post(client, {"polygon": "[[0, 0], [1, 1]]"}).status_code == 422
    assert _post(client, {"gsdM": "-1"}).status_code == 422


def test_response_schema(client):
    res = _post(client, {"gsdM": "0.1"})
    assert res.status_code == 200
    body = res.json()
    expected = {"count", "boxes", "zoomUsed", "zoomTrials", "densityPerHa", "densityEstimated", "areaHa",
                "gsdM", "meanCrownM2", "imageSize", "warnings", "annotatedImage", "processingMs", "modelVersion",
                "mock"}  # fmt: skip
    assert set(body) == expected
    assert body["count"] == len(body["boxes"])
    assert body["imageSize"] == {"width": 400, "height": 300}
    assert body["areaHa"] == 0.12  # 400 x 300 px at 0.1 m/px
    assert body["annotatedImage"] is None
    for box in body["boxes"]:
        assert set(box) == {"id", "x1", "y1", "x2", "y2", "score"} and box["x1"] < box["x2"]


def test_polygon_counts_only_trees_inside(mock_mode):
    whole = _post(mock_mode).json()
    half = _post(mock_mode, {"polygon": json.dumps([[0, 0], [200, 0], [200, 300], [0, 300]])}).json()
    assert 0 < half["count"] < whole["count"]
    assert all((b["x1"] + b["x2"]) / 2 <= 200 for b in half["boxes"])


def test_density_estimated_without_gsd_or_area(mock_mode):
    body = _post(mock_mode).json()
    assert body["densityEstimated"] is True and body["densityPerHa"] > 0
    assert "densité estimée (taille de couronne supposée)" in body["warnings"]
    by_area = _post(mock_mode, {"areaHa": "2"}).json()
    assert by_area["densityEstimated"] is False and by_area["densityPerHa"] == by_area["count"] / 2


def test_annotated_image_is_a_png(mock_mode):
    body = _post(mock_mode, {"annotated": "true"}).json()
    assert base64.b64decode(body["annotatedImage"]).startswith(b"\x89PNG")


def test_small_image_and_no_tree_warnings(mock_mode):
    body = _post(mock_mode, image=_png(150, 120)).json()
    assert any("image très petite" in w for w in body["warnings"])
    empty = _post(mock_mode, {"polygon": "[[0, 0], [5, 0], [5, 5]]"}).json()
    assert empty["count"] == 0 and any("aucun arbre" in w for w in empty["warnings"])
