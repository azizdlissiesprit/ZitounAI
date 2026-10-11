"""Olive tree detection by 640 px tiles with automatic zoom: the logic validated in the M6 notebook.

DO NOT change the formulas or the thresholds: they were validated on the test images (counting error
of a few %). Only the global constants of the notebook became attributes read from config.json
(TILE -> self.tile, OVERLAP -> self.overlap, CONF -> self.conf, IOU -> self.iou, AUTO_ZOOMS ->
self.auto_zooms, MAX_SIDE -> self.max_side) and the global `model` became `self.model`.
"""

import cv2
import numpy as np


def starts(length, tile, step):
    if length <= tile:
        return [0]
    s = list(range(0, length - tile, step))
    s.append(length - tile)
    return sorted(set(s))


def nms_merge(boxes, scores, iou_thr=0.5, contain_thr=0.6):
    # 1) NMS classique par score ; 2) les morceaux de couronne (coupés au bord d'une tuile) contenus
    #    dans une boîte plus grande sont supprimés : on parcourt les boîtes de la plus grande à la plus petite
    area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

    def inter(i, others):
        xx1 = np.maximum(boxes[i, 0], boxes[others, 0])
        yy1 = np.maximum(boxes[i, 1], boxes[others, 1])
        xx2 = np.minimum(boxes[i, 2], boxes[others, 2])
        yy2 = np.minimum(boxes[i, 3], boxes[others, 3])
        return (xx2 - xx1).clip(0) * (yy2 - yy1).clip(0)

    order, keep = scores.argsort()[::-1], []
    while len(order):
        i, rest = order[0], order[1:]
        keep.append(i)
        it = inter(i, rest)
        order = rest[it / (area[i] + area[rest] - it + 1e-9) < iou_thr]
    final = []
    for i in sorted(keep, key=lambda k: -area[k]):
        if not final or (inter(i, np.array(final)) / (area[i] + 1e-9)).max() < contain_thr:
            final.append(i)
    return np.array(final, dtype=int)


def oblique_warning(boxes, img_h):
    # photo inclinée : les couronnes sont nettement plus petites d'un côté de l'image que de l'autre
    if len(boxes) < 15:
        return None
    cy = (boxes[:, 1] + boxes[:, 3]) / 2
    side = np.sqrt((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1]))
    top, bottom = side[cy < img_h / 3], side[cy > 2 * img_h / 3]
    if len(top) >= 5 and len(bottom) >= 5:
        a, b = np.median(top), np.median(bottom)
        ratio = min(a, b) / max(a, b)
        if ratio < 0.7:
            return (
                f"photo probablement inclinée (couronnes {1 / ratio:.1f}x plus petites d'un côté) : "
                "comptage approximatif"
            )
    return None


class TreeCounter:
    """YOLO detector + tiling/zoom parameters from config.json."""

    def __init__(self, model, config: dict):
        self.model = model
        self.tile = int(config["tile"])
        self.overlap = float(config["overlap"])
        self.conf = float(config["conf"])
        self.iou = float(config["iou"])
        self.contain_thr = float(config.get("contain_thr", 0.6))
        self.auto_zooms = [float(z) for z in config["auto_zooms"]]
        self.max_side = int(config["max_side"])
        # max_det: no effect in practice (detection runs per 640 px tile, 300 and 1000 give the same
        # counts), kept as a safety margin for very dense tiles.
        self.max_det = int(config.get("max_det", 1000))
        self.auto_zoom = bool(config.get("auto_zoom", True))
        self.zoom_rule = config.get("zoom_rule", "x1_if_reliable")
        self.x1_ratio = float(config.get("x1_ratio", 0.8))

    def predict_tiled(self, img_bgr, conf=None, tile=None, crown_px=None):
        conf = self.conf if conf is None else conf
        tile = self.tile if tile is None else tile
        # le recouvrement doit dépasser la taille d'une couronne, sinon un arbre coupé entre deux tuiles compte double
        overlap = self.overlap if crown_px is None else min(0.5, max(self.overlap, 1.3 * crown_px / tile))
        h, w = img_bgr.shape[:2]
        step = int(tile * (1 - overlap))
        crops, offs = [], []
        for y in starts(h, tile, step):
            for x in starts(w, tile, step):
                crops.append(img_bgr[y : y + tile, x : x + tile])
                offs.append((x, y))
        all_b, all_s = [], []
        for k in range(0, len(crops), 16):
            results = self.model.predict(crops[k : k + 16], imgsz=tile, conf=conf, max_det=self.max_det, verbose=False)
            for r, (ox, oy) in zip(results, offs[k : k + 16], strict=True):
                b = r.boxes.xyxy.cpu().numpy().astype(float)
                s = r.boxes.conf.cpu().numpy().astype(float)
                b[:, [0, 2]] += ox
                b[:, [1, 3]] += oy
                all_b.append(b)
                all_s.append(s)
        if not all_b or sum(len(b) for b in all_b) == 0:
            return np.zeros((0, 4)), np.zeros(0)
        b, s = np.concatenate(all_b), np.concatenate(all_s)
        keep = nms_merge(b, s, iou_thr=self.iou, contain_thr=self.contain_thr)
        return b[keep], s[keep]

    def _trial(self, img_bgr, z, conf):
        # one zoom try: unchanged logic from the original predict_auto
        h, w = img_bgr.shape[:2]
        if max(h, w) * z > self.max_side or min(h, w) * z < 32:
            return None
        im = (
            img_bgr
            if z == 1
            else cv2.resize(img_bgr, None, fx=z, fy=z, interpolation=cv2.INTER_AREA if z < 1 else cv2.INTER_CUBIC)
        )
        b, sc = self.predict_tiled(im, conf=conf)

        def med(bb):
            return float(np.median(np.sqrt((bb[:, 2] - bb[:, 0]) * (bb[:, 3] - bb[:, 1]))))

        if len(sc) and 1.3 * med(b) > self.overlap * self.tile:
            # grandes couronnes : recompte avec un recouvrement adapté
            b2, sc2 = self.predict_tiled(im, conf=conf, crown_px=med(b))
            if len(sc2):
                b, sc = b2, sc2
        n, score, side = len(sc), 0.0, 0.0
        if n:
            side = med(b)
            giant = side > 0.25 * max(im.shape[:2])  # une seule "couronne" géante = échec typique
            too_big = side > 0.45 * self.tile  # couronne presque aussi grande qu'une tuile : peu fiable
            score = (
                float(np.sort(sc)[-min(n, 20) :].mean())
                * min(1.0, n / 5)
                * (0.2 if giant else 1.0)
                * (0.5 if too_big else 1.0)
            )
        return {"zoom": z, "n": n, "score": round(score, 3), "couronne_px": round(side, 1), "_im": im}

    def _finish(self, best, trials, conf):
        # final recount at the chosen zoom (unchanged)
        if best["n"]:
            b, sc = self.predict_tiled(best["_im"], conf=conf, crown_px=best["couronne_px"])
        else:
            b, sc = np.zeros((0, 4)), np.zeros(0)
        info = {"zoom": best["zoom"], "trials": [{k: v for k, v in t.items() if k != "_im"} for t in trials]}
        return b / best["zoom"], sc, info

    def predict_auto(self, img_bgr, zooms=None, conf=None, rule=None, x1_ratio=None):
        # échelle inconnue : essaie plusieurs zooms et garde le plus fiable (règle zoom_rule de config.json)
        zooms = zooms or self.auto_zooms
        conf = self.conf if conf is None else conf
        rule = self.zoom_rule if rule is None else rule
        x1_ratio = self.x1_ratio if x1_ratio is None else x1_ratio
        trials = []
        # early exit: the max score is 1.0, so score(x1) >= x1_ratio guarantees score(x1) >= x1_ratio * top
        if rule == "x1_if_reliable" and 1 in zooms:
            t1 = self._trial(img_bgr, 1, conf)
            if t1 is not None:
                trials.append(t1)
                if t1["score"] >= x1_ratio:
                    return self._finish(t1, trials, conf)
        for z in zooms:
            if any(t["zoom"] == z for t in trials):
                continue
            t = self._trial(img_bgr, z, conf)
            if t is not None:
                trials.append(t)
        if not trials:
            return np.zeros((0, 4)), np.zeros(0), {"zoom": 1, "trials": []}
        top = max(t["score"] for t in trials)
        x1 = next((t for t in trials if t["zoom"] == 1), None)
        if rule == "x1_if_reliable" and x1 is not None and top > 0 and x1["score"] >= x1_ratio * top:
            return self._finish(x1, trials, conf)
        # median rule (unchanged): zooms scoring >= 90% of the best, keep the median count
        cands = [t for t in trials if t["score"] >= 0.9 * top]
        target = sorted(t["n"] for t in cands)[len(cands) // 2]
        best = min(cands, key=lambda t: (abs(t["n"] - target), -t["score"]))
        return self._finish(best, trials, conf)

    def predict_fixed(self, img_bgr, zoom=1.0, conf=None):
        """auto_zoom = false in config.json: one predict_tiled at zoom 1 (or the zoom the user sent)."""
        im = (
            img_bgr
            if zoom == 1
            else cv2.resize(
                img_bgr, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_AREA if zoom < 1 else cv2.INTER_CUBIC
            )
        )
        b, sc = self.predict_tiled(im, conf=conf)
        return b / zoom, sc, {"zoom": zoom, "trials": []}
