# M3 · Yield forecast — notebooks

| | |
|---|---|
| Data | FAOSTAT + ONAGRI per governorate + seasonal Open-Meteo weather |
| Baseline | Linear regression |
| Model(s) | Random Forest / XGBoost (winter rain, spring heat, previous season) |
| Metrics | MAE and MAPE, chronological validation |
| Export | `models/m3/model.joblib` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m3/model.joblib`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
