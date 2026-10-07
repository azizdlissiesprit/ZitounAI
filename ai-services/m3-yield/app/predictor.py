"""Model loading and inference for M3. This is the file the module owner edits.

Until a trained model exists in MODEL_DIR, the service runs in mock mode with rough
regional figures and the alternate-bearing effect (good year / bad year).
"""

import os
from pathlib import Path

from app.schemas import YieldRequest, YieldResponse

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m3"))
MODEL_FILE = MODEL_DIR / "model.joblib"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

INTERVAL = 0.25  # +/- 25 % until the model provides its own uncertainty

# Placeholder orders of magnitude (tonnes of olives). Replace with ONAGRI data.
MOCK_REGIONAL_TONNES = {
    "sfax": 420_000,
    "sidi bouzid": 260_000,
    "kairouan": 190_000,
    "mahdia": 160_000,
    "sousse": 120_000,
    "monastir": 90_000,
    "gafsa": 60_000,
    "kasserine": 55_000,
}
MOCK_KG_PER_TREE = 25.0


def load():
    """Return the trained model, or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M3): return joblib.load(MODEL_FILE)  (XGBoost / RandomForest pipeline)
    return None


def predict(model, req: YieldRequest) -> YieldResponse:
    if model is None:
        regional, kg_per_tree = _mock(req)
    else:
        # TODO(M3): build features for (governorate, season): winter rain, spring heat,
        #   previous season's production... then regional = model.predict(features).
        raise NotImplementedError

    estimate = req.tree_count * kg_per_tree if req.tree_count else None
    return YieldResponse(
        governorate=req.governorate,
        season=req.season,
        regional_production_tonnes=round(regional),
        kg_per_tree=round(kg_per_tree, 1),
        parcel_estimate_kg=_round(estimate),
        parcel_low_kg=_round(estimate and estimate * (1 - INTERVAL)),
        parcel_high_kg=_round(estimate and estimate * (1 + INTERVAL)),
        model_version="mock" if model is None else MODEL_VERSION,
        mock=model is None,
    )


def _mock(req: YieldRequest) -> tuple[float, float]:
    alternate = 1.2 if req.season % 2 == 0 else 0.8  # "on" year vs "off" year
    regional = MOCK_REGIONAL_TONNES.get(req.governorate.strip().lower(), 40_000) * alternate
    return regional, MOCK_KG_PER_TREE * alternate


def _round(value: float | None) -> float | None:
    return None if value is None else round(value)
