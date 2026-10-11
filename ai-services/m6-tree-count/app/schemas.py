from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """snake_case in Python, camelCase in JSON (the contract with the Spring backend)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TreeBox(CamelModel):
    """One tree crown, in pixels of the uploaded image (top-left x1, y1 / bottom-right x2, y2)."""

    id: int
    x1: float
    y1: float
    x2: float
    y2: float
    score: float


class ZoomTrial(CamelModel):
    """One zoom tried by the automatic zoom: trees found, reliability score, median crown size."""

    zoom: float
    n: int
    score: float
    crown_px: float


class ImageSize(CamelModel):
    width: int
    height: int


class TreeCountResponse(CamelModel):
    count: int
    boxes: list[TreeBox]
    zoom_used: float | None = None
    zoom_trials: list[ZoomTrial] = []
    density_per_ha: float | None = None
    density_estimated: bool = False
    area_ha: float | None = None
    gsd_m: float | None = None  # meters per pixel used for the surfaces (given, or estimated)
    mean_crown_m2: float | None = None
    image_size: ImageSize
    warnings: list[str] = []
    annotated_image: str | None = None  # PNG in base64, only when annotated=true
    processing_ms: int
    model_version: str
    mock: bool
