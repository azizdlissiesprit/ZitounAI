# M2 · Irrigation & weather alerts — notebooks

| | |
|---|---|
| Data | Open-Meteo ERA5 for the main governorates |
| Baseline | "Same day last year" for ET0 and rain |
| Model(s) | Prophet and LSTM |
| Metrics | MAE and RMSE on predicted ET0 |
| Export | `models/m2/et0_model.pkl` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m2/et0_model.pkl`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
