from __future__ import annotations

from pydantic import BaseModel, Field


class IngestTextRequest(BaseModel):
    source_name: str | None = Field(default=None, description="Optional label for the document source")
    text: str = Field(..., description="Raw text to ingest")


class IngestResponse(BaseModel):
    document_id: str
    chunk_count: int
    document_sha256: str


class AskRequest(BaseModel):
    document_id: str
    question: str
    max_context_chunks: int | None = None  # future override hook


class AskResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    citations: list[dict]
    audit_id: str
    audit_pack: dict
