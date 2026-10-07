"""Model loading and inference for M5. This is the file the module owner edits.

Until a trained intent classifier exists in MODEL_DIR, the service runs in mock mode with
a keyword matcher (derja / arabizi / French). It is also a fair first baseline to beat.
"""

import os
import re
from pathlib import Path

from app.schemas import ChatRequest, ChatResponse, Source

MODEL_DIR = Path(os.getenv("MODEL_DIR", "../../models/m5"))
MODEL_FILE = MODEL_DIR / "intent_model.joblib"
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

KEYWORDS = {
    "disease": ["war9a", "war9", "mridh", "mard", "maladie", "feuille", "tsfar", "taches", "dwe"],
    "irrigation": ["sgi", "sga", "nesgi", "irrig", "arros", "chta", "mtar", "pluie", "gel", "skhana"],
    "yield": ["sab", "ghalla", "saba", "jni", "récolte", "recolte", "rendement", "production"],
    "price": ["soum", "s3ar", "prix", "nbi3", "bi3", "vendre", "huile", "stock"],
}

MOCK_SOURCES = [
    Source(
        title="FAO — Guide de production de l'olivier",
        url="https://www.fao.org/land-water/databases-and-software/crop-information/olive/en/",
    )
]


def load():
    """Return the trained intent classifier (+ RAG chain), or None to run in mock mode."""
    if not MODEL_FILE.exists():
        return None
    # TODO(M5): load the TF-IDF+LogReg pipeline or the fine-tuned BERT, and the Chroma retriever.
    return None


def predict(model, req: ChatRequest) -> ChatResponse:
    if model is None:
        intent, confidence = _keyword_intent(req.message)
        answer = None
        if intent == "general":
            answer = (
                "Réponse de démonstration : l'assistant cherchera bientôt la réponse dans les guides "
                "FAO, COI et du ministère de l'Agriculture."
            )
        return ChatResponse(
            intent=intent,
            confidence=confidence,
            answer=answer,
            sources=MOCK_SOURCES if answer else [],
            model_version="mock",
            mock=True,
        )

    # TODO(M5): intent = classifier.predict(normalize(req.message))
    #   if intent == "general": answer, sources = rag_chain(req.message)
    raise NotImplementedError


def _keyword_intent(message: str) -> tuple[str, float]:
    words = re.findall(r"[\w']+", message.lower())
    scores = {intent: sum(any(w.startswith(k) for k in kws) for w in words) for intent, kws in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general", 0.5
    return best, min(0.95, 0.6 + 0.15 * scores[best])
