from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """snake_case in Python, camelCase in JSON (the contract with the Spring backend)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DiseaseResponse(CamelModel):
    label: str  # healthy | peacock_spot | aculus_olearius | olive_knot
    label_fr: str
    confidence: float
    probabilities: dict[str, float]
    advice: str
    heatmap_base64: str | None = None  # Grad-CAM overlay (PNG, base64), optional
    model_version: str
    mock: bool
