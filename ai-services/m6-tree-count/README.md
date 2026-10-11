# M6 · Olive tree counting

**Owner:** Membre 6 · **Type:** Vision — object detection, YOLO11n (Ultralytics) trained on OliveTreeCrownsDb + Roboflow « Olive trees »

Counts the olive trees of a parcel on a top view (drone photo, satellite or Google Earth capture). The Spring backend saves the count on the parcel (after the farmer's review), where M3 reads it for the expected harvest. No business logic, no database here.

| | |
|---|---|
| Endpoint | `POST /count-trees` (multipart `image` + optional `polygon`, `gsdM`, `areaHa`, `zoom`, `annotated`) · `GET /health` |
| Contract | [docs/api-contract.md](../../docs/api-contract.md) (section M6) |
| Port (local / compose) | `8006` |
| Model | `models/m6/best.pt` + `models/m6/config.json` (5.5 MB, not in Git: `python scripts/models.py pull m6`) |
| Training notebook | [`notebooks/m6_tree_count/`](../../notebooks/m6_tree_count/) |

## How it works

The scale of the farmers' images is unknown, so the detection runs on **640 px tiles** at several **zooms**:

```
image ─ (> 4000 px: reduced) ─► zoom ×1 ─ score ≥ 0.8 ? ──yes──► keep ×1 (no other zoom tried)
                                   │ no
                                   ▼
                    every zoom of auto_zooms (0.5 … 4)
                    ×1 score ≥ 0.8 × best score ? ──yes──► keep ×1
                                   │ no
                                   ▼
          median count of the zooms scoring ≥ 90 % of the best
─► final recount with a tile overlap larger than a crown ─► boxes back in pixels of the upload
─► polygon (tree centers inside) ─► surface, density, warnings
```

| File | What |
|---|---|
| `app/counter.py` | `TreeCounter`: tiling, box merging, zoom choice. **The logic validated in the notebook: do not change the formulas or thresholds** |
| `app/postprocess.py` | decoding, polygon, surfaces and density, annotated image: edit freely |
| `app/predictor.py` | loads the model (mock mode without it), runs the pipeline |
| `app/main.py` | FastAPI: model loaded once at startup (lifespan + warm-up), 413/415/422, logs |
| `models/m6/config.json` | `tile`, `overlap`, `conf`, `iou`, `contain_thr`, `auto_zooms`, `max_side`, `auto_zoom`, `zoom_rule`, `x1_ratio`, `max_det` |

- `auto_zoom: false`: a single detection at zoom ×1 (or the `zoom` sent).
- `zoom_rule: "median"`: the original rule (no ×1 preference), for comparison.
- `max_det` (1000) has no effect in practice (detection runs per tile, 300 and 1000 give the same counts): a safety margin.
- `ultralytics` is pinned to **8.4.175**, the version that trained `best.pt`. Retrain with another version → update the pin.
- Speed on CPU: ~5 s for a 1600 × 1200 image (`TORCH_THREADS`, default 4). The backend waits up to 60 s.

## Run locally

```bash
cd ai-services/m6-tree-count
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r ../requirements-dev.txt   # torch CPU, ~800 MB download
uvicorn app.main:app --port 8006   # Swagger UI: http://localhost:8006/docs
python -m pytest -s                # -s prints the per-image counts
```

Environment variables: `MODEL_DIR` (default `../../models/m6`), `TORCH_THREADS`, `MODEL_VERSION`, `PORT` (Docker).

```bash
curl -F "image=@parcel.jpg;type=image/jpeg" -F "gsdM=0.1" http://localhost:8006/count-trees
```

## Tests

- `tests/test_counter.py`: tiling, box merging, the zoom rule (with a fake `_trial`), polygon, density. No model needed (CI).
- `tests/test_api.py`: status codes and response schema.
- `tests/test_model.py`: real images in `tests/data/` + `tests/data/expected_counts.csv` (`image,count`), count within **±15 %**. Skipped while the folder is missing.

Without the model the service runs in mock mode (`"mock": true`, trees on a regular grid), so the app works before `models/m6` is downloaded.
