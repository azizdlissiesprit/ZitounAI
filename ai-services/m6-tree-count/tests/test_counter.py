"""Detection logic without the YOLO weights: tiling, box merging, zoom rule, polygon, density."""

import numpy as np
import pytest

from app import postprocess as pp
from app.counter import TreeCounter, nms_merge, oblique_warning, starts

CONFIG = {"tile": 640, "overlap": 0.2, "conf": 0.25, "iou": 0.5, "contain_thr": 0.6,
          "auto_zooms": [0.5, 1.0, 2.0, 3.0], "max_side": 4000}  # fmt: skip


def test_starts():
    assert starts(1000, 640, 512) == [0, 360]
    assert starts(500, 640, 512) == [0]


def test_nms_merge_keeps_whole_crowns():
    # two halves of a crown cut at a tile edge + a duplicate are absorbed by the whole crown
    boxes = np.array([[100, 100, 180, 300], [220, 100, 300, 300], [100, 100, 300, 300],
                      [400, 100, 600, 300], [105, 102, 302, 298]], dtype=float)  # fmt: skip
    scores = np.array([0.9, 0.9, 0.9, 0.8, 0.7])
    keep = nms_merge(boxes, scores)
    assert len(keep) == 2
    assert sorted(boxes[keep][:, 0].tolist()) == [100, 400]


def test_oblique_warning_when_crowns_shrink_towards_one_side():
    small_top = [[x, 10, x + 10, 20] for x in range(0, 300, 30)]  # 10 px crowns at the top
    big_bottom = [[x, 900, x + 30, 930] for x in range(0, 300, 30)]  # 30 px crowns at the bottom
    assert "inclinée" in oblique_warning(np.array(small_top + big_bottom, dtype=float), img_h=1000)
    assert oblique_warning(np.array(big_bottom, dtype=float), img_h=1000) is None  # < 15 boxes


# ---- zoom rule, with a fake _trial (no model) ----


def counter_with_trials(monkeypatch, scores: dict[float, tuple[float, int]]) -> tuple[TreeCounter, list]:
    """scores: zoom -> (score, n). Records the zooms tried."""
    counter = TreeCounter(model=None, config=CONFIG)
    tried = []

    def fake_trial(img, z, conf):
        tried.append(z)
        score, n = scores[z]
        return {"zoom": z, "n": n, "score": score, "couronne_px": 20.0, "_im": img}

    monkeypatch.setattr(counter, "_trial", fake_trial)
    monkeypatch.setattr(counter, "predict_tiled", lambda im, conf=None, tile=None, crown_px=None: (
        np.array([[10.0, 10.0, 30.0, 30.0]]), np.array([0.9])))  # fmt: skip
    return counter, tried


IMG = np.zeros((1000, 1000, 3), dtype=np.uint8)


def test_x1_reliable_on_its_own_exits_early(monkeypatch):
    counter, tried = counter_with_trials(monkeypatch, {0.5: (0.9, 40), 1.0: (0.85, 50), 2.0: (0.95, 60),
                                                       3.0: (0.9, 70)})  # fmt: skip
    boxes, _, info = counter.predict_auto(IMG)
    assert info["zoom"] == 1 and tried == [1]  # _trial called only once
    assert [t["zoom"] for t in info["trials"]] == [1]
    assert boxes.tolist() == [[10.0, 10.0, 30.0, 30.0]]


def test_x1_kept_when_close_enough_to_the_best(monkeypatch):
    # 0.6 >= 0.8 * 0.7 = 0.56
    counter, tried = counter_with_trials(monkeypatch, {0.5: (0.5, 40), 1.0: (0.6, 50), 2.0: (0.7, 60),
                                                       3.0: (0.65, 70)})  # fmt: skip
    _, _, info = counter.predict_auto(IMG)
    assert info["zoom"] == 1
    assert sorted(tried) == [0.5, 1.0, 2.0, 3.0]


def test_median_rule_when_x1_unreliable(monkeypatch):
    # 0.4 < 0.8 * 0.9; zooms >= 0.81: 0.5 (40 trees), 2 (60), 3 (80) -> median count 60 -> zoom 2
    counter, _ = counter_with_trials(monkeypatch, {0.5: (0.85, 40), 1.0: (0.4, 50), 2.0: (0.9, 60),
                                                   3.0: (0.82, 80)})  # fmt: skip
    boxes, _, info = counter.predict_auto(IMG)
    assert info["zoom"] == 2.0
    assert boxes.tolist() == [[5.0, 5.0, 15.0, 15.0]]  # boxes divided by the zoom


def test_median_rule_has_no_early_exit(monkeypatch):
    # x1 = 0.85 would exit early with x1_if_reliable; the original median rule picks zoom 2
    scores = {0.5: (0.95, 40), 1.0: (0.85, 50), 2.0: (0.99, 60), 3.0: (0.92, 70)}
    counter, tried = counter_with_trials(monkeypatch, scores)
    _, _, info = counter.predict_auto(IMG, rule="median")
    assert info["zoom"] == 2.0
    assert tried == [0.5, 1.0, 2.0, 3.0]


# ---- polygon, surfaces, density ----

SQUARE = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)


def test_polygon_keeps_only_boxes_centered_inside():
    boxes = np.array([[10, 10, 30, 30], [90, 90, 130, 130], [150, 10, 170, 30]], dtype=float)
    # centers: (20, 20) inside, (110, 110) outside although the box overlaps, (160, 20) outside
    assert pp.centers_inside(boxes, SQUARE).tolist() == [True, False, False]
    assert pp.centers_inside(boxes, None).tolist() == [True, True, True]


def test_parse_polygon():
    assert pp.parse_polygon("[[0,0],[10,0],[10,10]]").shape == (3, 2)
    assert pp.parse_polygon(None) is None and pp.parse_polygon("  ") is None
    for bad in ["[[0,0],[1,1]]", "not json", "[1, 2, 3]", '[["a", 0], [1, 1], [2, 2]]']:
        with pytest.raises(pp.InvalidInputError):
            pp.parse_polygon(bad)


def test_density_from_gsd():
    boxes = np.array([[0, 0, 10, 10], [20, 20, 30, 30]], dtype=float)
    d = pp.density(boxes, (1000, 1000), SQUARE, gsd_m=1.0, area_ha=None)
    # polygon 100 x 100 px at 1 m/px = 1 ha; crown 10 x 10 px * 0.785 = 78.5 m2
    assert (d.area_ha, d.density_per_ha, d.mean_crown_m2, d.estimated) == (1.0, 2.0, 78.5, False)


def test_density_from_area():
    boxes = np.zeros((6, 4))
    d = pp.density(boxes, (500, 500), None, gsd_m=None, area_ha=2.0)
    assert (d.density_per_ha, d.area_ha, d.estimated) == (3.0, 2.0, False)


def test_density_estimated_from_crown_size():
    boxes = np.array([[0, 0, 50, 50]] * 4, dtype=float)  # median crown 50 px -> 5 m / 50 px = 0.1 m/px
    d = pp.density(boxes, (1000, 1000), None, gsd_m=None, area_ha=None)
    # whole image 1000 x 1000 px at 0.1 m/px = 1 ha
    assert (d.gsd_m, d.area_ha, d.density_per_ha, d.estimated) == (0.1, 1.0, 4.0, True)
    assert pp.density(np.zeros((0, 4)), (100, 100), None, None, None).density_per_ha is None


def test_downscale_big_images():
    img = np.zeros((2000, 8000, 3), dtype=np.uint8)
    small, scale = pp.downscale(img, 4000)
    assert small.shape[:2] == (1000, 4000) and scale == 0.5
    assert pp.downscale(IMG, 4000)[1] == 1.0
