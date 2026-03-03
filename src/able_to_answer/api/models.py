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


class FeedbackRequest(BaseModel):
    audit_id: str = Field(..., description="ID of the audit record being rated")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (very poor) to 5 (excellent)")
    comment: str | None = Field(default=None, description="Optional free-text comment")


class FeedbackResponse(BaseModel):
    feedback_id: str
    audit_id: str
    rating: int
    comment: str | None
    created_at: int


class FeedbackSummary(BaseModel):
    feedback_id: str
    audit_id: str
    rating: int
    created_at: int
