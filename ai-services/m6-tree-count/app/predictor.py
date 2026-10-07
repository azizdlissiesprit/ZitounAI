"""Model loading and inference for M6. This is the file the module owner edits.

Until a trained detector exists in MODEL_DIR, the service runs in mock mode: it places
boxes on a regular grid (like an orchard) and draws them, so the full pipeline works.
"""

import base64
import hashlib
import io
import os
from pathlib import Path

from PIL import Image, ImageDraw, UnidentifiedImageError

from app.schemas import Box, TreeCountResponse

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m6"))
MODEL_FILE = MODEL_DIR / "best.pt"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")
MAX_SIDE = 1280  # downscale big satellite captures before inference


class InvalidImageError(ValueError):
    pass


def load():
    """Return the trained detector, or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M6): from ultralytics import YOLO; return YOLO(MODEL_FILE)
    return None


def predict(model, image_bytes: bytes) -> TreeCountResponse:
    image = _open_image(image_bytes)
    if model is None:
        boxes = _mock_boxes(image, image_bytes)
    else:
        # TODO(M6): results = model.predict(image, conf=0.25)[0]
        #   boxes = [Box(x=x1, y=y1, width=x2-x1, height=y2-y1, confidence=c) for each detection]
        raise NotImplementedError

    return TreeCountResponse(
        tree_count=len(boxes),
        boxes=boxes,
        annotated_image_base64=_draw(image, boxes),
        model_version="mock" if model is None else MODEL_VERSION,
        mock=model is None,
    )


def _mock_boxes(image: Image.Image, image_bytes: bytes) -> list[Box]:
    w, h = image.size
    spacing = 40 + hashlib.sha256(image_bytes).digest()[0] % 40  # 40-80 px between trees
    crown = spacing * 0.6
    return [
        Box(x=x, y=y, width=crown, height=crown, confidence=0.9)
        for y in range(spacing // 2, int(h - crown), spacing)
        for x in range(spacing // 2, int(w - crown), spacing)
    ]


def _draw(image: Image.Image, boxes: list[Box]) -> str:
    annotated = image.copy()
    pen = ImageDraw.Draw(annotated)
    for b in boxes:
        pen.rectangle([b.x, b.y, b.x + b.width, b.y + b.height], outline=(255, 210, 0), width=2)
    buf = io.BytesIO()
    annotated.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _open_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as e:
        raise InvalidImageError("The uploaded file is not a readable image") from e
    image = image.convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    return image
