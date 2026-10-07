# M1 · Leaf diseases

**Owner:** Membre 1 · **Type:** Vision — classification (MobileNetV3 / EfficientNet-B0 vs simple CNN, Grad-CAM)

Thin FastAPI service: it loads the trained model and exposes `POST /predict`. No business logic, no database — that lives in the Spring backend.

| | |
|---|---|
| Endpoint | `POST /predict` — input: multipart `image` |
| Health | `GET /health` |
| Contract | [docs/api-contract.md](../../docs/api-contract.md) (section M1) |
| Port (local / compose) | `8001` |
| Model file | `models/m1/model.pt` (not in Git, shared via Drive) |
| Training notebook | [`notebooks/m1_disease/`](../../notebooks/m1_disease/) |

## Run locally

```bash
cd ai-services/m1-disease
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r ../requirements-dev.txt
uvicorn app.main:app --reload --port 8001   # Swagger UI: http://localhost:8001/docs
python -m pytest
```

## Mock mode → real model

While `models/m1/model.pt` does not exist, the service answers with **mock data** (`"mock": true`), so the backend and the app can be built in parallel. To plug in your model, edit **only** [`app/predictor.py`](app/predictor.py):

1. `load()` — load the exported model from `MODEL_DIR`.
2. `predict()` — same preprocessing as in your notebook, then build the response.
3. Add the ML libraries to `requirements.txt` (pinned versions).

Do not change the response schema in `app/schemas.py` without updating the contract and telling the backend owner (see [CONTRIBUTING.md](../../CONTRIBUTING.md#changing-the-api-contract)).
