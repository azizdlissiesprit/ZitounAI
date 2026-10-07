# API contract

Frozen at the end of week 2. Every change goes through a PR reviewed by the backend owner (M2) and the frontend owner (M4), see [CONTRIBUTING.md](../CONTRIBUTING.md#changing-the-api-contract).

- All JSON uses **camelCase**. Python services keep snake_case internally (Pydantic aliases do the conversion).
- Errors from the backend are [RFC 9457 ProblemDetail](https://www.rfc-editor.org/rfc/rfc9457): `{"status": 404, "title": "Not Found", "detail": "Parcel 3 not found"}`.
- Every AI result has `"mock": true` while the module has no trained model yet. The app shows a "données de démo" badge.

Where the contract lives in code (keep the three in sync):

| Layer | Files |
|---|---|
| AI service (Python) | `ai-services/mX-*/app/schemas.py` |
| Backend (Java) | `backend/src/main/java/tn/zitouna/ai/*/…Result.java`, `…Client.Request` |
| Frontend (TypeScript) | `frontend/src/app/core/api/models.ts` |

---

## 1. Backend API (what the Angular app calls)

Base URL `/api`. All endpoints except `/api/auth/**` need `Authorization: Bearer <token>`. Interactive docs: http://localhost:8080/swagger-ui.html

| Method | Path | Body / params | Response | Module |
|---|---|---|---|---|
| POST | `/auth/register` | `{fullName, email, password}` | `201 {token, expiresAt, user}` | — |
| POST | `/auth/login` | `{email, password}` | `{token, expiresAt, user}` | — |
| GET | `/users/me` | | `{id, fullName, email, role}` | — |
| GET | `/parcels` | | `Parcel[]` | — |
| POST | `/parcels` | `ParcelRequest` | `201 Parcel` | — |
| GET / PUT / DELETE | `/parcels/{id}` | `ParcelRequest` for PUT | `Parcel` / `204` | — |
| POST | `/ai/disease` | multipart `image`, optional `?parcelId=` | `DiseaseResult` | M1 |
| GET | `/parcels/{id}/irrigation` | | `IrrigationResult` | M2 |
| GET | `/parcels/{id}/yield` | optional `?season=2026` | `YieldResult` | M3 |
| GET | `/ai/price` | `?horizonWeeks=8&quantityKg=` | `PriceResult` | M4 |
| POST | `/ai/chat` | `{message, parcelId?}` | `{intent, answer, answeredBy, sources, mock}` | M5 (+M2/M3/M4) |
| POST | `/parcels/{id}/count-trees` | multipart `image` | `TreeCountResult` (also saves `treeCount` on the parcel when not mock) | M6 |
| POST | `/parcels/{id}/harvest-plan` | optional multipart `image` | `HarvestPlan` | M6 → M3 → M4 |
| GET | `/history` | `?type=DISEASE&page=0&size=20` | `{content: Prediction[], page, size, totalElements, totalPages}` | — |

`Parcel`:

```json
{ "id": 1, "name": "Henchir Sfax", "governorate": "Sfax", "latitude": 34.74, "longitude": 10.76,
  "areaHa": 2.5, "treeCount": 250, "variety": "Chemlali", "irrigated": false, "createdAt": "2026-10-07T10:00:00Z" }
```

`ParcelRequest` is the same without `id` and `createdAt`. `name`, `governorate`, `latitude`, `longitude` are required.

`HarvestPlan`:

```json
{ "treeCount": 250, "treeCountSource": "M6", "yield": { "…": "YieldResult" }, "estimatedOilKg": 1500.0,
  "price": { "…": "PriceResult" }, "summary": "250 arbres, récolte estimée 7500 kg d'olives (≈ 1500 kg d'huile). Conseil : stocker.",
  "mock": true }
```

---

## 2. AI services (what the backend calls)

Each service is a FastAPI app on port `8000` in Docker (`8001`–`8006` on your machine). Each exposes:

- `GET /health` → `{"status": "ok", "module": "m1-disease", "modelLoaded": false}`
- `POST /predict` → described below. Invalid input → `422`.

### M1

`POST /predict` — multipart field `image` (JPEG/PNG of one leaf).

```json
{
  "label": "peacock_spot",
  "labelFr": "Œil de paon",
  "confidence": 0.82,
  "probabilities": { "healthy": 0.06, "peacock_spot": 0.82, "aculus_olearius": 0.06, "olive_knot": 0.06 },
  "advice": "Traitement préventif à base de cuivre…",
  "heatmapBase64": null,
  "modelVersion": "mock",
  "mock": true
}
```

`label` ∈ `healthy | peacock_spot | aculus_olearius | olive_knot`. `heatmapBase64`: optional Grad-CAM PNG.

### M2

`POST /predict`

```json
{ "latitude": 34.74, "longitude": 10.76, "treeCount": 250, "areaHa": 2.5, "days": 7 }
```

```json
{
  "days": [
    { "date": "2026-10-07", "et0Mm": 4.1, "rainMm": 0.0, "waterNeedMm": 2.67, "litersPerTree": 266.5, "irrigate": true }
  ],
  "alerts": [
    { "date": "2026-10-09", "type": "HEATWAVE", "severity": "MEDIUM", "message": "Canicule (41 °C) : irriguez tôt le matin ou le soir." }
  ],
  "modelVersion": "mock",
  "mock": true
}
```

`waterNeedMm = ET0 × Kc − 0.8 × rain` (Kc olive = 0.65, FAO-56). `litersPerTree` is `null` without `treeCount` and `areaHa`. `type` ∈ `FROST | HEATWAVE`, `severity` ∈ `LOW | MEDIUM | HIGH`.

### M3

`POST /predict`

```json
{ "governorate": "Sfax", "season": 2026, "treeCount": 250 }
```

```json
{
  "governorate": "Sfax", "season": 2026, "regionalProductionTonnes": 504000,
  "kgPerTree": 30.0, "parcelEstimateKg": 7500, "parcelLowKg": 5625, "parcelHighKg": 9375,
  "modelVersion": "mock", "mock": true
}
```

`season` = year the harvest starts (2026 = 2026/2027). Parcel fields are `null` without `treeCount`.

### M4

`POST /predict`

```json
{ "horizonWeeks": 8, "quantityKg": 1500 }
```

```json
{
  "currency": "TND", "unit": "kg",
  "history":  [ { "date": "2026-04-15", "price": 12.4, "low": null, "high": null } ],
  "forecast": [ { "date": "2026-10-14", "price": 13.1, "low": 12.95, "high": 13.25 } ],
  "recommendation": "STORE",
  "reason": "Le prix pourrait atteindre 13.60 TND/kg vers le 25/11, soit +0.42 TND/kg après coût de stockage.",
  "expectedGainTnd": 630.0,
  "modelVersion": "mock", "mock": true
}
```

Prices are producer prices of olive oil (TND per kg of oil). `recommendation` ∈ `SELL_NOW | STORE`. `expectedGainTnd` is `null` without `quantityKg` or when selling now is better.

### M5

`POST /predict`

```json
{ "message": "chnowa na3mel ki el war9a tsfar?" }
```

```json
{
  "intent": "disease", "confidence": 0.9, "answer": null,
  "sources": [ { "title": "FAO — Guide de production de l'olivier", "url": "https://…" } ],
  "modelVersion": "mock", "mock": true
}
```

`intent` ∈ `disease | irrigation | yield | price | general`. `answer` is the RAG answer; it may be `null` when another module should answer. The backend (`ChatService`) routes `price` → M4, `irrigation` → M2, `yield` → M3 and falls back to `answer` if that module fails.

### M6

`POST /predict` — multipart field `image` (drone or satellite view of a parcel).

```json
{
  "treeCount": 42,
  "boxes": [ { "x": 120.0, "y": 64.0, "width": 30.0, "height": 30.0, "confidence": 0.91 } ],
  "annotatedImageBase64": "iVBORw0KGgo…",
  "modelVersion": "mock", "mock": true
}
```

Box coordinates are in pixels of the (possibly downscaled, max 1280 px) image.
