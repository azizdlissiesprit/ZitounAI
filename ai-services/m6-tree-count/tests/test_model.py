"""Real counting accuracy on reference images: needs models/m6 and tests/data/expected_counts.csv.

tests/data/expected_counts.csv: "image,count" (image file names relative to tests/data/).
Skipped when the model or the images are missing (e.g. in CI). Run with -s to see the details.
"""

import csv
from pathlib import Path

import pytest

from app import predictor

DATA = Path(__file__).parent / "data"
EXPECTED = DATA / "expected_counts.csv"
TOLERANCE = 0.15

pytestmark = pytest.mark.skipif(not EXPECTED.exists(), reason="no tests/data/expected_counts.csv")


@pytest.fixture(scope="module")
def counter(client):
    if client.app.state.counter is None:
        pytest.skip("model not found (models/m6/best.pt)")
    return client.app.state.counter


def test_counts_within_15_percent(counter):
    with EXPECTED.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    errors = []
    print(f"\n{'image':<32} {'expected':>8} {'counted':>8} {'error':>7}  zoom")
    for row in rows:
        result = predictor.count(counter, (DATA / row["image"]).read_bytes())
        expected = int(row["count"])
        error = (result.count - expected) / expected
        print(f"{row['image']:<32} {expected:>8} {result.count:>8} {error:>+7.1%}  x{result.zoom_used}")
        if abs(error) > TOLERANCE:
            errors.append(f"{row['image']}: {result.count} instead of {expected} ({error:+.0%})")
    assert not errors, "Counting error over 15 %:\n" + "\n".join(errors)
