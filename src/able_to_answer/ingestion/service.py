from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from able_to_answer.core.config import settings


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _chunk_text(text: str, *, size: int, overlap: int) -> Iterable[dict]:
    text = text.replace("\r\n", "\n")
    n = len(text)
    start = 0
    ordinal = 0

    while start < n:
        end = min(n, start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunk_hash = _sha256(chunk)
            chunk_id = f"chunk_{chunk_hash[:16]}"
            yield {
                "id": chunk_id,
                "ordinal": ordinal,
                "start_char": start,
                "end_char": end,
                "sha256": chunk_hash,
                "text": chunk,
            }
            ordinal += 1

        if end == n:
            break

        start = max(0, end - overlap)


@dataclass(frozen=True)
class IngestResult:
    document_id: str
    chunk_count: int
    document_sha256: str


def ingest_text(store, *, source_name: str | None, text: str) -> IngestResult:
    if not text or not text.strip():
        raise ValueError("Empty text")

    document_sha = _sha256(text)
    document_id = store.upsert_document(source_name=source_name, text=text)

    chunks = list(_chunk_text(text, size=settings.chunk_size_chars, overlap=settings.chunk_overlap_chars))
    store.insert_chunks(document_id=document_id, chunks=chunks)

    return IngestResult(
        document_id=document_id,
        chunk_count=len(chunks),
        document_sha256=document_sha,
    )
