"""Quality of the trained ensemble. Skipped when the model is not present (e.g. in CI)."""

import csv
from pathlib import Path

import pytest

from app import predictor

PROBE_SET = Path(__file__).parent / "data" / "m5_probe_set.csv"
MIN_PROBE_CORRECT = 21  # the training notebook got 23/25

pytestmark = pytest.mark.skipif(
    not (predictor.MODEL_DIR / "config.json").exists(),
    reason=f"trained model not found in {predictor.MODEL_DIR}",
)


def intent_of(client, text: str) -> dict:
    return client.post("/intent", json={"text": text}).json()


def test_model_is_loaded(client):
    assert client.get("/health").json()["modelLoaded"] is True
    assert intent_of(client, "aslema")["mock"] is False


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("aslema", "salutation"),
        ("fama jlid ghodwa fi beja?", "meteo_alerte"),
        ("nbi3 el zit taw walla nestanna?", "prix_vente"),
    ],
)
def test_known_examples(client, text, intent):
    assert intent_of(client, text)["intent"] == intent


def test_weather_question_extracts_governorate(client):
    assert intent_of(client, "fama jlid ghodwa fi beja?")["entities"]["gouvernorat"] == "beja"


def test_domain_guard_on_real_model(client):
    assert intent_of(client, "zitouni mouch labes")["clarify"] is True


def test_probe_set(client):
    with PROBE_SET.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    errors = []
    for row in rows:
        res = intent_of(client, row["text"])
        if res["intent"] != row["intent"]:
            errors.append(
                f"[{row['pattern']}] {row['text']!r}: expected {row['intent']}, got {res['intent']} "
                f"({res['confidence']:.2f}, clarify={res['clarify']}, "
                f"candidates={[(c['intent'], c['score']) for c in res['candidates']]})"
            )

    correct = len(rows) - len(errors)
    print(f"\nProbe set: {correct}/{len(rows)} correct")
    for e in errors:
        print("  " + e)
    assert correct >= MIN_PROBE_CORRECT, f"{correct}/{len(rows)} < {MIN_PROBE_CORRECT}:\n" + "\n".join(errors)
