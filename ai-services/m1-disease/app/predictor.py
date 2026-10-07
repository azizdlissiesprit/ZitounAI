"""Model loading and inference for M1. This is the file the module owner edits.

Until a trained model exists in MODEL_DIR, the service runs in mock mode: it returns
plausible predictions with mock=True so the backend and the app can be built in parallel.
"""

import hashlib
import io
import os
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.schemas import DiseaseResponse

# Relative to the service folder when run locally; Docker sets MODEL_DIR=/models/m1.
MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m1"))
MODEL_FILE = MODEL_DIR / "model.pt"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

CLASSES = ["healthy", "peacock_spot", "aculus_olearius", "olive_knot"]
LABELS_FR = {
    "healthy": "Feuille saine",
    "peacock_spot": "Œil de paon",
    "aculus_olearius": "Aculus olearius (acarien)",
    "olive_knot": "Tuberculose de l'olivier",
}
ADVICE = {
    "healthy": "Aucune maladie détectée. Continuez à surveiller le verger régulièrement.",
    "peacock_spot": (
        "Traitement préventif à base de cuivre (bouillie bordelaise) en automne et en fin d'hiver. "
        "Taillez pour aérer l'arbre et ramassez les feuilles tombées."
    ),
    "aculus_olearius": (
        "Traitement au soufre mouillable au printemps et surveillance des jeunes pousses. "
        "Demandez l'avis d'un technicien avant de traiter."
    ),
    "olive_knot": (
        "Coupez et brûlez les rameaux atteints, désinfectez les outils de taille, "
        "puis appliquez un produit cuprique après la taille, la grêle ou le gel."
    ),
}


class InvalidImageError(ValueError):
    pass


def load():
    """Return the trained model, or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M1): load the exported model, for example:
    #   import torch
    #   model = torch.jit.load(MODEL_FILE, map_location="cpu")
    #   model.eval()
    #   return model
    return None


def predict(model, image_bytes: bytes) -> DiseaseResponse:
    image = _open_image(image_bytes)
    if model is None:
        return _mock(image_bytes)

    # TODO(M1): same preprocessing as in the training notebook, then:
    #   probs = softmax(model(tensor))  -> dict {class: prob}
    #   heatmap = grad_cam(model, tensor)  (optional)
    raise NotImplementedError(f"Real inference not implemented yet ({image.size})")


def _build(probabilities: dict[str, float], mock: bool, heatmap: str | None = None) -> DiseaseResponse:
    label = max(probabilities, key=probabilities.get)
    return DiseaseResponse(
        label=label,
        label_fr=LABELS_FR[label],
        confidence=round(probabilities[label], 4),
        probabilities={k: round(v, 4) for k, v in probabilities.items()},
        advice=ADVICE[label],
        heatmap_base64=heatmap,
        model_version="mock" if mock else MODEL_VERSION,
        mock=mock,
    )


def _mock(image_bytes: bytes) -> DiseaseResponse:
    # Deterministic: the same photo always gives the same fake answer.
    seed = hashlib.sha256(image_bytes).digest()
    winner = CLASSES[seed[0] % len(CLASSES)]
    rest = (1 - 0.82) / (len(CLASSES) - 1)
    return _build({c: 0.82 if c == winner else rest for c in CLASSES}, mock=True)


def _open_image(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        return image.convert("RGB")
    except (UnidentifiedImageError, OSError) as e:
        raise InvalidImageError("The uploaded file is not a readable image") from e
