"""M6 · Olive tree counting. Thin FastAPI wrapper: no business logic, no database.

POST /count-trees: YOLO11n by 640 px tiles with automatic zoom (app/counter.py), then parcel polygon,
density and warnings (app/postprocess.py). Saving the count on the parcel is done by the Spring backend.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile

from app import predictor
from app.postprocess import InvalidInputError
from app.schemas import TreeCountResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("m6")

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model ONCE, then warm it up so the first farmer does not wait.
    started = time.perf_counter()
    app.state.counter = predictor.load()
    predictor.warm_up(app.state.counter)
    log.info("model ready in %.1f s (loaded=%s)", time.perf_counter() - started, app.state.counter is not None)
    yield


app = FastAPI(title="Zitouna M6 · Olive tree counting", version="2.0", lifespan=lifespan)


@app.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "module": "m6-tree-count", "modelLoaded": request.app.state.counter is not None}


@app.post(
    "/count-trees",
    response_model=TreeCountResponse,
    responses={413: {"description": "Image over 15 MB"}, 415: {"description": "Not a JPEG or PNG"}},
)
def count_trees(
    request: Request,
    image: Annotated[UploadFile, File(description="Top view of the parcel (drone, satellite, Google Earth)")],
    polygon: Annotated[str | None, Form(description="Parcel outline, JSON [[x, y], ...] in image pixels")] = None,
    gsd_m: Annotated[float | None, Form(alias="gsdM", gt=0, description="Meters per pixel of the image")] = None,
    area_ha: Annotated[float | None, Form(alias="areaHa", gt=0, description="Parcel area, if no gsdM")] = None,
    zoom: Annotated[float | None, Form(gt=0, le=8, description="Force one zoom instead of the automatic one")] = None,
    annotated: Annotated[bool, Form(description="Also return a PNG with the boxes drawn")] = False,
) -> TreeCountResponse:
    # Sync endpoint: FastAPI runs it in a thread, so the CPU-bound detection does not block /health.
    if (image.content_type or "").lower() not in IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Image JPEG ou PNG attendue")
    data = image.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image trop lourde (15 Mo maximum)")
    try:
        result = predictor.count(request.app.state.counter, data, polygon, gsd_m, area_ha, zoom, annotated)
    except InvalidInputError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    log.info(
        "image=%dx%d (%d KB) trees=%d zoom=%s polygon=%s duration_ms=%d",
        result.image_size.width,
        result.image_size.height,
        len(data) // 1024,
        result.count,
        result.zoom_used,
        polygon is not None,
        result.processing_ms,
    )
    return result
