"""Model loading and inference for M4. This is the file the module owner edits.

Until a trained model exists in MODEL_DIR, the service runs in mock mode with a synthetic
price curve. The sell/store rule below is the baseline signal and can stay with the real model.
"""

import math
import os
from datetime import date, timedelta
from pathlib import Path

from app.schemas import Point, PriceRequest, PriceResponse

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m4"))
MODEL_FILE = MODEL_DIR / "sarima.pkl"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

STORAGE_COST_TND_PER_KG_MONTH = 0.15
HISTORY_WEEKS = 26


def load():
    """Return the trained model, or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M4): load the fitted SARIMA (statsmodels results.save / joblib) or LSTM.
    return None


def predict(model, req: PriceRequest) -> PriceResponse:
    if model is None:
        history, forecast = _mock_series(req.horizon_weeks)
    else:
        # TODO(M4): history = last HISTORY_WEEKS weekly prices from data/processed,
        #   forecast = model.get_forecast(req.horizon_weeks) with a confidence interval.
        raise NotImplementedError

    current = history[-1].price
    best = max(forecast, key=lambda p: p.price)
    months_stored = (best.date - history[-1].date).days / 30
    net_gain_per_kg = best.price - current - STORAGE_COST_TND_PER_KG_MONTH * months_stored

    if net_gain_per_kg > 0:
        recommendation = "STORE"
        reason = (
            f"Le prix pourrait atteindre {best.price:.2f} TND/kg vers le {best.date:%d/%m}, "
            f"soit +{net_gain_per_kg:.2f} TND/kg après coût de stockage."
        )
    else:
        recommendation = "SELL_NOW"
        reason = f"Aucune hausse attendue au-delà du coût de stockage : prix actuel {current:.2f} TND/kg."

    gain = round(net_gain_per_kg * req.quantity_kg, 2) if req.quantity_kg and net_gain_per_kg > 0 else None
    return PriceResponse(
        history=history,
        forecast=forecast,
        recommendation=recommendation,
        reason=reason,
        expected_gain_tnd=gain,
        model_version="mock" if model is None else MODEL_VERSION,
        mock=model is None,
    )


def _mock_series(horizon: int) -> tuple[list[Point], list[Point]]:
    today = date.today()

    def price(week: int) -> float:  # gentle seasonal wave around 13 TND/kg
        return 13 + 1.2 * math.sin(week / 8) + 0.3 * math.sin(week * 1.7)

    history = [
        Point(date=today - timedelta(weeks=HISTORY_WEEKS - 1 - i), price=round(price(i), 2))
        for i in range(HISTORY_WEEKS)
    ]
    forecast = []
    for h in range(1, horizon + 1):
        p = price(HISTORY_WEEKS - 1 + h)
        spread = 0.15 * math.sqrt(h)
        forecast.append(
            Point(
                date=today + timedelta(weeks=h), price=round(p, 2), low=round(p - spread, 2), high=round(p + spread, 2)
            )
        )
    return history, forecast
