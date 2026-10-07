"""Model loading and inference for M2. This is the file the module owner edits.

Until a trained model exists in MODEL_DIR, the service runs in mock mode with synthetic
weather. The water-balance formula below (FAO-56) is real and is kept with the real model.
"""

import math
import os
from datetime import date, timedelta
from pathlib import Path

from app.schemas import Alert, Day, IrrigationRequest, IrrigationResponse

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m2"))
MODEL_FILE = MODEL_DIR / "et0_model.pkl"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

KC_OLIVE = 0.65  # FAO-56 crop coefficient, mature olive grove
EFFECTIVE_RAIN = 0.8  # share of rain that reaches the roots
IRRIGATE_THRESHOLD_MM = 2.0
FROST_C, HEATWAVE_C = 0.0, 40.0


def load():
    """Return the trained model, or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M2): load the Prophet / LSTM model, e.g. joblib.load(MODEL_FILE)
    return None


def predict(model, req: IrrigationRequest) -> IrrigationResponse:
    if model is None:
        forecast = _mock_forecast(req)
    else:
        # TODO(M2): fetch recent weather from Open-Meteo for (lat, lon), then forecast
        #   ET0, rain, tmin, tmax for req.days days with the model.
        raise NotImplementedError

    days, alerts = [], []
    for d, et0, rain, tmin, tmax in forecast:
        need = max(0.0, et0 * KC_OLIVE - EFFECTIVE_RAIN * rain)
        days.append(
            Day(
                date=d,
                et0_mm=round(et0, 2),
                rain_mm=round(rain, 1),
                water_need_mm=round(need, 2),
                liters_per_tree=_liters_per_tree(need, req),
                irrigate=need >= IRRIGATE_THRESHOLD_MM,
            )
        )
        if tmin <= FROST_C:
            alerts.append(
                Alert(
                    date=d,
                    type="FROST",
                    severity="HIGH" if tmin <= -2 else "MEDIUM",
                    message=f"Risque de gel ({tmin:.0f} °C) : protégez les jeunes plants.",
                )
            )
        if tmax >= HEATWAVE_C:
            alerts.append(
                Alert(
                    date=d,
                    type="HEATWAVE",
                    severity="HIGH" if tmax >= 44 else "MEDIUM",
                    message=f"Canicule ({tmax:.0f} °C) : irriguez tôt le matin ou le soir.",
                )
            )

    return IrrigationResponse(
        days=days, alerts=alerts, model_version="mock" if model is None else MODEL_VERSION, mock=model is None
    )


def _liters_per_tree(need_mm: float, req: IrrigationRequest) -> float | None:
    """1 mm of water on 1 m² = 1 litre."""
    if not req.tree_count or not req.area_ha:
        return None
    m2_per_tree = req.area_ha * 10_000 / req.tree_count
    return round(need_mm * m2_per_tree, 1)


def _mock_forecast(req: IrrigationRequest):
    """Synthetic but plausible weather; warmer in the south (lower latitude)."""
    warm = max(0.0, 37 - req.latitude)  # Bizerte ~0, Tataouine ~4
    out = []
    for i in range(req.days):
        d = date.today() + timedelta(days=i)
        season = math.sin((d.timetuple().tm_yday - 105) / 365 * 2 * math.pi)  # peak in July
        et0 = 3.5 + 2.5 * season + 0.3 * warm + 0.4 * math.sin(i)
        rain = 6.0 if i % 5 == 3 and season < 0.5 else 0.0
        tmax = 26 + 10 * season + 1.5 * warm + 2 * math.sin(i * 1.3)
        tmin = tmax - 12
        out.append((d, et0, rain, tmin, tmax))
    return out
