from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Intent = Literal["disease", "irrigation", "yield", "price", "general"]


class CamelModel(BaseModel):
    """snake_case in Python, camelCase in JSON (the contract with the Spring backend)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatRequest(CamelModel):
    message: str = Field(min_length=1, max_length=1000, examples=["chnowa na3mel ki el war9a tsfar?"])


class Source(CamelModel):
    title: str
    url: str | None = None


class ChatResponse(CamelModel):
    intent: Intent
    confidence: float
    answer: str | None = None  # RAG answer; may be None when another module should answer
    sources: list[Source] = []
    model_version: str
    mock: bool
