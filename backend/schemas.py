from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class IngestRequest(BaseModel):
    type: Literal["note", "url"]
    content: str = Field(..., min_length=1, max_length=50_000)
    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content cannot be empty")
        return stripped

    @model_validator(mode="after")
    def url_must_be_http(self):
        if self.type == "url" and not self.content.startswith(("http://", "https://")):
            raise ValueError("URL content must start with http:// or https://")
        return self

class IngestResponse(BaseModel):
    id: str
    type: str
    title: str
    source: str | None
    created_at: str
    chunk_count: int

class ItemResponse(BaseModel):
    id: str
    type: str
    title: str
    source: str | None
    created_at: str
    preview: str

class ItemListResponse(BaseModel):
    items: list[ItemResponse]

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=8)
    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        return value.strip()

class SourceSnippet(BaseModel):
    item_id: str
    title: str
    type: str | None
    source: str | None
    snippet: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]

class ErrorResponse(BaseModel):
    error: str