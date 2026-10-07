# M4 · Price & selling time — notebooks

| | |
|---|---|
| Data | COI monthly producer prices + ONAGRI + FAOSTAT |
| Baseline | SARIMA |
| Model(s) | LSTM, compared to SARIMA; sell/store rule or classifier |
| Metrics | MAPE + simulated gain vs "always sell now" |
| Export | `models/m4/sarima.pkl` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m4/sarima.pkl`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
