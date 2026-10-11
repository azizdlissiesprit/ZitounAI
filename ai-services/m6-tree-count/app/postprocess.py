"""Everything around the detection: image decoding, parcel polygon, surfaces and density, warnings.

Pure functions on numpy arrays (no model), so they are unit-tested without the YOLO weights.
Boxes are float arrays of shape (n, 4): x1, y1, x2, y2 in pixels.
"""

import base64
import json
from dataclasses import dataclass

import cv2
import numpy as np

TYPICAL_CROWN_M = 5.0  # crown side assumed when neither gsd_m nor area_ha is given
SMALL_IMAGE_PX = 200


class InvalidInputError(ValueError):
    pass


def decode_image(data: bytes) -> np.ndarray:
    """BGR image, read with OpenCV like in the notebook."""
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise InvalidInputError("Le fichier n'est pas une image lisible (JPEG ou PNG)")
    return img


def parse_polygon(text: str | None) -> np.ndarray | None:
    """'[[x, y], ...]' (pixels of the uploaded image, at least 3 points) -> float32 array (n, 2)."""
    if text is None or not text.strip():
        return None
    try:
        points = np.array(json.loads(text), dtype=np.float32)
    except (ValueError, TypeError) as e:
        raise InvalidInputError("polygon doit être une liste JSON de points [[x, y], ...]") from e
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
        raise InvalidInputError("polygon doit contenir au moins 3 points [x, y]")
    return points


def downscale(img: np.ndarray, max_side: int) -> tuple[np.ndarray, float]:
    """Reduce big images before the detection. Returns the image and the scale applied (<= 1)."""
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return img, 1.0
    scale = max_side / max(h, w)
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), scale


def centers_inside(boxes: np.ndarray, polygon: np.ndarray | None) -> np.ndarray:
    """Boolean mask: box center inside the polygon (on the edge counts as inside). No polygon: all True."""
    if polygon is None:
        return np.ones(len(boxes), dtype=bool)
    contour = polygon.reshape(-1, 1, 2)
    cx, cy = (boxes[:, 0] + boxes[:, 2]) / 2, (boxes[:, 1] + boxes[:, 3]) / 2
    return np.array(
        [cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0 for x, y in zip(cx, cy, strict=True)],
        dtype=bool,
    )


@dataclass
class Density:
    density_per_ha: float | None = None
    estimated: bool = False
    area_ha: float | None = None
    gsd_m: float | None = None
    mean_crown_m2: float | None = None


def density(
    boxes: np.ndarray,
    image_size: tuple[int, int],
    polygon: np.ndarray | None,
    gsd_m: float | None,
    area_ha: float | None,
) -> Density:
    """Trees per hectare over the polygon (or the whole image).

    gsd_m given -> exact surfaces; area_ha given -> count / area_ha; neither -> gsd estimated from the
    median crown size, assuming a typical 5 m crown (density_estimated = True).
    """
    w, h = image_size
    n = len(boxes)
    area_px = float(cv2.contourArea(polygon.reshape(-1, 1, 2))) if polygon is not None else float(w * h)
    box_area_px = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

    if gsd_m:
        surface_ha = area_px * gsd_m**2 / 10_000
        return Density(
            density_per_ha=_round(n / surface_ha, 1) if surface_ha > 0 else None,
            area_ha=_round(surface_ha, 3),
            gsd_m=gsd_m,
            mean_crown_m2=_round(float((box_area_px * 0.785 * gsd_m**2).mean()), 1) if n else None,
        )
    if area_ha:
        return Density(density_per_ha=_round(n / area_ha, 1), area_ha=area_ha)
    if n == 0:
        return Density()
    gsd_estimated = TYPICAL_CROWN_M / float(np.median(np.sqrt(box_area_px)))
    surface_ha = area_px * gsd_estimated**2 / 10_000
    return Density(
        density_per_ha=_round(n / surface_ha, 1) if surface_ha > 0 else None,
        estimated=True,
        area_ha=_round(surface_ha, 3),
        gsd_m=_round(gsd_estimated, 4),
    )


def annotate(img: np.ndarray, boxes: np.ndarray, polygon: np.ndarray | None) -> str:
    """PNG (base64) with the boxes in red and the polygon in blue."""
    out = img.copy()
    thickness = max(1, round(max(img.shape[:2]) / 800))
    if polygon is not None:
        cv2.polylines(out, [polygon.astype(np.int32).reshape(-1, 1, 2)], True, (255, 0, 0), thickness + 1)
    for x1, y1, x2, y2 in boxes.astype(int):
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), thickness)
    ok, png = cv2.imencode(".png", out)
    return base64.b64encode(png.tobytes()).decode("ascii") if ok else ""


def _round(value: float, digits: int) -> float:
    return round(float(value), digits)
