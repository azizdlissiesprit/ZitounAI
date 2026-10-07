# M5 · Derja assistant

**Owner:** Membre 5 · **Type:** NLP — intent classification (TF-IDF+LogReg vs BERT) + RAG (Chroma)

Thin FastAPI service: it loads the trained model and exposes `POST /predict`. No business logic, no database — that lives in the Spring backend.

| | |
|---|---|
| Endpoint | `POST /predict` — input: JSON `{message}` |
| Health | `GET /health` |
| Contract | [docs/api-contract.md](../../docs/api-contract.md) (section M5) |
| Port (local / compose) | `8005` |
| Model file | `models/m5/intent_model.joblib` (not in Git, shared via Drive) |
| Training notebook | [`notebooks/m5_assistant/`](../../notebooks/m5_assistant/) |

## Run locally

```bash
cd ai-services/m5-assistant
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r ../requirements-dev.txt
uvicorn app.main:app --reload --port 8005   # Swagger UI: http://localhost:8005/docs
python -m pytest
```

## Mock mode → real model

While `models/m5/intent_model.joblib` does not exist, the service answers with **mock data** (`"mock": true`), so the backend and the app can be built in parallel. To plug in your model, edit **only** [`app/predictor.py`](app/predictor.py):

1. `load()` — load the exported model from `MODEL_DIR`.
2. `predict()` — same preprocessing as in your notebook, then build the response.
3. Add the ML libraries to `requirements.txt` (pinned versions).

Do not change the response schema in `app/schemas.py` without updating the contract and telling the backend owner (see [CONTRIBUTING.md](../../CONTRIBUTING.md#changing-the-api-contract)).
