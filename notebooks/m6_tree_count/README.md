# M6 · Olive tree counting — notebooks

| | |
|---|---|
| Data | OliveTreeCrownsDb tiles + Tunisian satellite captures for the demo |
| Baseline | OpenCV thresholding + blob detection |
| Model(s) | YOLOv8 fine-tuned |
| Metrics | mAP@0.5, counting error per image |
| Export | `models/m6/best.pt` |

Suggested notebooks:

1. `01_eda.ipynb` — distributions, missing values, corrupted files, breaks in the series.
2. `02_baseline.ipynb` — simple model + metric (phase 2).
3. `03_model.ipynb` — at least two approaches compared to the baseline, logged in MLflow (phase 3).
4. `04_export.ipynb` — export the best model to `models/m6/best.pt`.

Notebooks must run top to bottom on a fresh kernel. Read data from `../../data/`, never from your Downloads folder. Strip outputs before committing (see CONTRIBUTING.md).
