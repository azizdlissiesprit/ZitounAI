# M3 · Yield forecast

**Owner:** Membre 3 · **Type:** Tabular regression (XGBoost / Random Forest vs linear regression)

Thin FastAPI service: it loads the trained model and exposes `POST /predict`. No business logic, no database — that lives in the Spring backend.

| | |
|---|---|
| Endpoint | `POST /predict` — input: JSON `{governorate, season, treeCount?}` |
| Health | `GET /health` |
| Contract | [docs/api-contract.md](../../docs/api-contract.md) (section M3) |
| Port (local / compose) | `8003` |
| Model file | `models/m3/model.joblib` (not in Git, shared via Drive) |
| Training notebook | [`notebooks/m3_yield/`](../../notebooks/m3_yield/) |

## Run locally

```bash
cd ai-services/m3-yield
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r ../requirements-dev.txt
uvicorn app.main:app --reload --port 8003   # Swagger UI: http://localhost:8003/docs
python -m pytest
```

## Mock mode → real model

While `models/m3/model.joblib` does not exist, the service answers with **mock data** (`"mock": true`), so the backend and the app can be built in parallel. To plug in your model, edit **only** [`app/predictor.py`](app/predictor.py):

1. `load()` — load the exported model from `MODEL_DIR`.
2. `predict()` — same preprocessing as in your notebook, then build the response.
3. Add the ML libraries to `requirements.txt` (pinned versions).

Do not change the response schema in `app/schemas.py` without updating the contract and telling the backend owner (see [CONTRIBUTING.md](../../CONTRIBUTING.md#changing-the-api-contract)).
