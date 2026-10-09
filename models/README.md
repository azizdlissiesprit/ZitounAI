# Trained models

Weights are **not in Git**. Upload them to the shared Drive folder `zitouna-ai/models/` and copy them here. `docker-compose.yml` mounts this folder read-only into each AI container at `/models`.

| Module | Expected file | Loaded by |
|---|---|---|
| M1 | `models/m1/model.pt` | `ai-services/m1-disease/app/predictor.py` |
| M2 | `models/m2/et0_model.pkl` | `ai-services/m2-irrigation/app/predictor.py` |
| M3 | `models/m3/model.joblib` | `ai-services/m3-yield/app/predictor.py` |
| M4 | `models/m4/sarima.pkl` | `ai-services/m4-price/app/predictor.py` |
| M5 | `models/m5_ensemble/` (`config.json`, `tfidf.joblib`, `setfit/`) | `ai-services/m5-assistant/app/predictor.py` |
| M6 | `models/m6/best.pt` | `ai-services/m6-tree-count/app/predictor.py` |

If a file is missing, the service runs in mock mode (`"mock": true`). Put the model version (e.g. the MLflow run id) in the `MODEL_VERSION` environment variable.
