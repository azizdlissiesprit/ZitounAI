"""M5 · Derja assistant: intent detection. Thin FastAPI wrapper: no business logic, no database.

Routing the question to M1-M4 / M6 is done by the Spring backend (ChatService), not here.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app import predictor
from app.schemas import IntentRequest, IntentResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("m5")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load both models ONCE, then warm them up so the first farmer does not wait.
    started = time.perf_counter()
    app.state.ensemble = predictor.load()
    predictor.predict(app.state.ensemble, "aslema")
    log.info("models ready in %.1f s (loaded=%s)", time.perf_counter() - started, app.state.ensemble is not None)
    yield


app = FastAPI(title="Zitouna M5 · Derja assistant (intents)", version="2.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "module": "m5-assistant", "modelLoaded": request.app.state.ensemble is not None}


@app.post("/intent", response_model=IntentResponse)
def intent(body: IntentRequest, request: Request) -> IntentResponse:
    started = time.perf_counter()
    result = predictor.predict(request.app.state.ensemble, body.text)
    log.info(
        "text=%r intent=%s confidence=%.2f clarify=%s duration_ms=%.0f",
        body.text[:60],
        result.intent,
        result.confidence,
        result.clarify,
        (time.perf_counter() - started) * 1000,
    )
    return result
