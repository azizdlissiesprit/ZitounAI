# M5 · Derja assistant (intent detection)

**Owner:** Membre 5 · **Type:** NLP — TF-IDF + SetFit (`multilingual-e5-base`) ensemble, clarification rules, governorate entity.

Detects the intent of a farmer's question written in Tunisian Arabic (Arabic script or arabizi) or mixed with French. The Spring backend (`ChatService`) then routes it to the right module. No business logic, no database here.

| | |
|---|---|
| Endpoints | `POST /intent` `{"text": "..."}` · `GET /health` |
| Contract | [docs/api-contract.md](../../docs/api-contract.md) (section M5) |
| Port (local / compose) | `8005` |
| Model | `models/m5_ensemble/` (`config.json`, `tfidf.joblib`, `setfit/`), ~1 GB, not in Git |

## How it works

```
text ─┬─ normalize()    → TF-IDF pipeline  → p_tfidf  (columns reordered to config.labels)
      └─ light_clean()  → SetFit ("query: ") → p_setfit
p = 0.4 · p_setfit + 0.6 · p_tfidf                     (weight_setfit in config.json)
→ top1, top2, confidence, margin → clarification rules → governorate entity
```

| File | What |
|---|---|
| `app/preprocessing.py` | `normalize` / `light_clean`: **identical to training, do not change** |
| `app/rules.py` | domain words, confusable pairs, clarification questions: edit freely |
| `app/entities.py` | the 24 governorates (Latin, arabizi, Arabic): add spellings freely |
| `app/predictor.py` | loads the ensemble, combines the models; keyword fallback if no model |
| `app/main.py` | FastAPI: models loaded once at startup (lifespan), logs with duration |

Clarification rules, first match wins:
1. **Domain guard:** the top intent is `hors_sujet` but the text mentions olives or farming. This guard exists because refusing a real farmer's question is the worst error.
2. **Disagreement:** the two models disagree and `confidence < clarify_threshold`.
3. **Confusable pair:** the top two intents are a known pair and `margin < 0.15`.

## Run locally

```bash
cd ai-services/m5-assistant
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r ../requirements-dev.txt   # torch CPU, ~1 GB download
uvicorn app.main:app --port 8005   # Swagger UI: http://localhost:8005/docs
python -m pytest -s                # -s prints the probe-set errors
```

Environment variables: `MODEL_DIR` (default `../../models/m5_ensemble`), `PORT` (Docker, default 8000), `MODEL_VERSION`.

`scikit-learn` is pinned to the `sklearn_version` of `config.json` (1.6.1): with another version `joblib.load` may fail. Retrain → update both.

## Tests

- `tests/test_rules.py`: preprocessing, rules, entities and ensemble maths, with fake models (always run, also in CI).
- `tests/test_api.py`: API schema and validation (with the model, or the keyword fallback).
- `tests/test_model.py`: known examples and the probe set `tests/data/m5_probe_set.csv` (≥ 21/25). **Skipped when the model is missing**, e.g. in CI.
