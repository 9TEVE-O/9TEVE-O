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


class DocumentSummary(BaseModel):
    document_id: str
    source_name: str | None
    created_at: int
    sha256: str
    text_len: int


class AuditSummary(BaseModel):
    audit_id: str
    created_at: int
    document_id: str
    question: str


class AuditResponse(BaseModel):
    audit_id: str
    created_at: int
    document_id: str
    question: str
    answer: str
    citations: list[dict]
    audit_pack: dict
