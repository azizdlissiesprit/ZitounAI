"""Model loading and the counting pipeline for M6.

Without models/m6/best.pt the service runs in mock mode: boxes on a regular grid (like an orchard),
so the backend and the app work before the model is downloaded (and in CI).
"""

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path

import numpy as np

from app import postprocess as pp
from app.counter import TreeCounter, oblique_warning
from app.schemas import ImageSize, TreeBox, TreeCountResponse, ZoomTrial

log = logging.getLogger("m6")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m6"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "m6-yolo11n")
MOCK_MAX_SIDE = 4000

# One YOLO model shared by the request threads: inference is serialized (and already uses
# TORCH_THREADS cores).
_lock = threading.Lock()


def load(model_dir: Path = MODEL_DIR) -> TreeCounter | None:
    """TreeCounter with the YOLO weights and config.json, or None (mock mode) if the files are missing."""
    weights, config_file = model_dir / "best.pt", model_dir / "config.json"
    if not weights.exists() or not config_file.exists():
        log.warning("no model in %s: mock mode", model_dir)
        return None
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(int(os.getenv("TORCH_THREADS", str(min(4, os.cpu_count() or 1)))))
    config = json.loads(config_file.read_text(encoding="utf-8", errors="replace"))
    return TreeCounter(YOLO(str(weights)), config)


def warm_up(counter: TreeCounter | None) -> None:
    """First YOLO call is slow (model fusing, allocations): do it at startup, not for the first farmer."""
    if counter is not None:
        counter.predict_tiled(np.zeros((counter.tile, counter.tile, 3), dtype=np.uint8))


def count(
    counter: TreeCounter | None,
    image_bytes: bytes,
    polygon_json: str | None = None,
    gsd_m: float | None = None,
    area_ha: float | None = None,
    zoom: float | None = None,
    annotated: bool = False,
) -> TreeCountResponse:
    started = time.perf_counter()
    img = pp.decode_image(image_bytes)
    polygon = pp.parse_polygon(polygon_json)
    h, w = img.shape[:2]
    warnings: list[str] = []

    # 1. Detection, on an image reduced to max_side if needed; boxes back in pixels of the upload.
    small, scale = pp.downscale(img, counter.max_side if counter else MOCK_MAX_SIDE)
    if counter is None:
        boxes, scores, info = _mock_detect(small, image_bytes)
    else:
        with _lock:
            if not counter.auto_zoom:
                boxes, scores, info = counter.predict_fixed(small, zoom=zoom or 1.0)
            elif zoom:
                boxes, scores, info = counter.predict_auto(small, zooms=[zoom])
            else:
                boxes, scores, info = counter.predict_auto(small)
        if zoom and counter.auto_zoom and not info["trials"]:
            warnings.append(f"zoom x{zoom:g} impossible pour cette image (côté maximal {counter.max_side} px)")
    boxes = boxes / scale

    # 2. Parcel polygon: only the trees whose center is inside.
    inside = pp.centers_inside(boxes, polygon)
    kept, kept_scores = boxes[inside], scores[inside]

    # 3. Surfaces and density.
    dens = pp.density(kept, (w, h), polygon, gsd_m, area_ha)

    # 4. Warnings.
    if oblique := oblique_warning(boxes, h):
        warnings.append(oblique)
    if len(kept) == 0:
        warnings.append("aucun arbre trouvé : l'image doit être vue du dessus, et le contour doit entourer les arbres")
    if min(w, h) < pp.SMALL_IMAGE_PX:
        warnings.append(f"image très petite (< {pp.SMALL_IMAGE_PX} px) : comptage peu fiable")
    if dens.estimated:
        warnings.append("densité estimée (taille de couronne supposée)")

    return TreeCountResponse(
        count=len(kept),
        boxes=[
            TreeBox(
                id=i,
                x1=round(b[0], 1),
                y1=round(b[1], 1),
                x2=round(b[2], 1),
                y2=round(b[3], 1),
                score=round(float(s), 3),
            )  # fmt: skip
            for i, (b, s) in enumerate(zip(kept.tolist(), kept_scores, strict=True))
        ],
        zoom_used=info["zoom"],
        zoom_trials=[
            ZoomTrial(zoom=t["zoom"], n=t["n"], score=t["score"], crown_px=t["couronne_px"]) for t in info["trials"]
        ],  # fmt: skip
        density_per_ha=dens.density_per_ha,
        density_estimated=dens.estimated,
        area_ha=dens.area_ha,
        gsd_m=dens.gsd_m,
        mean_crown_m2=dens.mean_crown_m2,
        image_size=ImageSize(width=w, height=h),
        warnings=warnings,
        annotated_image=pp.annotate(img, kept, polygon) if annotated else None,
        processing_ms=round((time.perf_counter() - started) * 1000),
        model_version="mock" if counter is None else MODEL_VERSION,
        mock=counter is None,
    )


def _mock_detect(img: np.ndarray, image_bytes: bytes) -> tuple[np.ndarray, np.ndarray, dict]:
    """Regular grid of crowns, spacing derived from the image bytes (same image -> same result)."""
    h, w = img.shape[:2]
    spacing = 40 + hashlib.sha256(image_bytes).digest()[0] % 40  # 40-80 px between trees
    crown = spacing * 0.6
    boxes = np.array(
        [
            [x, y, x + crown, y + crown]
            for y in range(spacing // 2, int(h - crown), spacing)
            for x in range(spacing // 2, int(w - crown), spacing)
        ],  # fmt: skip
        dtype=float,
    ).reshape(-1, 4)
    return boxes, np.full(len(boxes), 0.9), {"zoom": 1.0, "trials": []}
