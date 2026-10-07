# M1 · Leaf diseases — notebooks

| | |
|---|---|
| Data | Uğuz & Uysal + Roboflow leaf images |
| Baseline | Frozen CNN (transfer learning, head only) or a simple CNN |
| Model(s) | MobileNetV3 / EfficientNet-B0 fine-tuned + Grad-CAM |
| Metrics | Accuracy, per-class F1, confusion matrix |
| Export | `models/m1/model.pt (TorchScript)` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m1/model.pt (TorchScript)`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
