"""M5 · Derja assistant. Thin FastAPI wrapper: no business logic, no database.

Routing a question to M1-M4 is done by the Spring backend (ChatService), not here.
"""

from fastapi import FastAPI

from app import predictor
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Zitouna M5 · Derja assistant", version="1.0")
model = predictor.load()  # None -> mock mode


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "module": "m5-assistant", "modelLoaded": model is not None}


@app.post("/predict", response_model=ChatResponse)
def predict(request: ChatRequest) -> ChatResponse:
    return predictor.predict(model, request)
