"""M3 · Yield forecast. Thin FastAPI wrapper: no business logic, no database."""

from fastapi import FastAPI

from app import predictor
from app.schemas import YieldRequest, YieldResponse

app = FastAPI(title="Zitouna M3 · Yield forecast", version="1.0")
model = predictor.load()  # None -> mock mode


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "module": "m3-yield", "modelLoaded": model is not None}


@app.post("/predict", response_model=YieldResponse)
def predict(request: YieldRequest) -> YieldResponse:
    return predictor.predict(model, request)
