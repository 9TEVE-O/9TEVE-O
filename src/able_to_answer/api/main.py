from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from able_to_answer.core.config import settings
from able_to_answer.core.logging import logger
from able_to_answer.core.storage import SqliteStore
from able_to_answer.ingestion.service import ingest_text
from able_to_answer.retrieval.service import retrieve_top_chunks
from able_to_answer.audit.service import build_audit_pack
from able_to_answer.api.models import (
    AskRequest,
    AskResponse,
    AuditResponse,
    AuditSummary,
    DocumentSummary,
    IngestResponse,
    IngestTextRequest,
)

app = FastAPI(
    title="Able to Answer",
    description="Governance-grade AI document intelligence: ingest → retrieve → answer → audit",
    version="0.1.0",
)

store = SqliteStore(settings.db_path)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest/text", response_model=IngestResponse)
def ingest_text_route(req: IngestTextRequest):
    try:
        res = ingest_text(store, source_name=req.source_name, text=req.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return IngestResponse(
        document_id=res.document_id,
        chunk_count=res.chunk_count,
        document_sha256=res.document_sha256,
    )


@app.post("/ingest/file", response_model=IngestResponse)
async def ingest_file_route(file: UploadFile = File(...)):
    # MVP: treat uploaded file as text if it decodes cleanly.
    # PDF parsing is intentionally not implemented here (keeps MVP dependency-free).
    raw = await file.read()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Unsupported file format in MVP",
                "detail": "Upload UTF-8 text. PDF extraction will be added next.",
            },
        )

    res = ingest_text(store, source_name=file.filename, text=text)
    return IngestResponse(
        document_id=res.document_id,
        chunk_count=res.chunk_count,
        document_sha256=res.document_sha256,
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    doc = store.get_document(document_id=req.document_id)
    if not doc:
        return JSONResponse(status_code=404, content={"error": "document_not_found"})

    citations = retrieve_top_chunks(store, document_id=req.document_id, question=req.question)

    # MVP "answer builder": return the highest-scoring chunk(s) as an extractive answer.
    # This proves the end-to-end contract + citations + audit trail without model integration.
    if not citations:
        answer = (
            "No relevant evidence was found in the indexed chunks for this question. "
            "Try rephrasing the question or ingesting a more complete document."
        )
        cited_dicts = []
    else:
        chunk_rows = {r["id"]: r for r in store.get_chunks(document_id=req.document_id)}
        evidence = []
        for c in citations:
            row = chunk_rows.get(c.chunk_id)
            txt = row["text"] if row is not None else None
            if txt:
                evidence.append(txt.strip())

        combined = "\n\n---\n\n".join(evidence)
        answer = combined[: settings.max_answer_chars]
        cited_dicts = [asdict(c) for c in citations]

    pack = build_audit_pack(
        document_id=req.document_id,
        question=req.question,
        answer=answer,
        citations=citations,
        retrieval_mode="lexical_overlap_v1",
    )
    audit_id = store.insert_audit(
        document_id=req.document_id,
        question=req.question,
        answer=answer,
        citations=citations,
        pack=pack,
    )

    logger.info("ask: doc=%s audit=%s citations=%d", req.document_id, audit_id, len(citations))

    return AskResponse(
        document_id=req.document_id,
        question=req.question,
        answer=answer,
        citations=cited_dicts,
        audit_id=audit_id,
        audit_pack=pack,
    )


@app.get("/documents", response_model=list[DocumentSummary])
def list_documents():
    rows = store.list_documents()
    return [
        DocumentSummary(
            document_id=r["id"],
            source_name=r["source_name"],
            created_at=r["created_at"],
            sha256=r["sha256"],
            text_len=r["text_len"],
        )
        for r in rows
    ]


@app.get("/documents/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str):
    row = store.get_document(document_id=document_id)
    if not row:
        return JSONResponse(status_code=404, content={"error": "document_not_found"})
    return DocumentSummary(
        document_id=row["id"],
        source_name=row["source_name"],
        created_at=row["created_at"],
        sha256=row["sha256"],
        text_len=row["text_len"],
    )


@app.get("/audits", response_model=list[AuditSummary])
def list_audits():
    rows = store.list_audits()
    return [
        AuditSummary(
            audit_id=r["id"],
            created_at=r["created_at"],
            document_id=r["document_id"],
            question=r["question"],
        )
        for r in rows
    ]


@app.get("/audits/{audit_id}", response_model=AuditResponse)
def get_audit(audit_id: str):
    row = store.get_audit(audit_id=audit_id)
    if not row:
        return JSONResponse(status_code=404, content={"error": "audit_not_found"})
    return AuditResponse(
        audit_id=row["id"],
        created_at=row["created_at"],
        document_id=row["document_id"],
        question=row["question"],
        answer=row["answer"],
        citations=json.loads(row["citations_json"]),
        audit_pack=json.loads(row["pack_json"]),
    )
