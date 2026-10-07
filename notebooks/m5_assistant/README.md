# M5 · Derja assistant — notebooks

| | |
|---|---|
| Data | TUNIZI + team-written questions + FAO/COI/ministry guides |
| Baseline | TF-IDF + logistic regression (intent) |
| Model(s) | mBERT / Tunisian BERT fine-tuned + RAG (Chroma + LLM) |
| Metrics | Intent F1 + 30-50 test questions graded by hand |
| Export | `models/m5/intent_model.joblib` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m5/intent_model.joblib`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
