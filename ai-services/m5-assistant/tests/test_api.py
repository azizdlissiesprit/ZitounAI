import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("chnowa na3mel ki el war9a tsfar?", "disease"),
        ("9adech lezem nesgi el zitoun?", "irrigation"),
        ("soum el zit tawa bech yatla3?", "price"),
        ("Quelle sera ma récolte cette année ?", "yield"),
        ("ahla", "general"),
    ],
)
def test_intents(message, intent):
    body = client.post("/predict", json={"message": message}).json()
    assert body["intent"] == intent


def test_rejects_empty_message():
    assert client.post("/predict", json={"message": ""}).status_code == 422
