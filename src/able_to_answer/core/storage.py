from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  source_name TEXT,
  sha256 TEXT NOT NULL,
  text_len INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  start_char INTEGER NOT NULL,
  end_char INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  text TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_ord ON chunks(document_id, ordinal);

CREATE TABLE IF NOT EXISTS audits (
  id TEXT PRIMARY KEY,
  created_at INTEGER NOT NULL,
  document_id TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  citations_json TEXT NOT NULL,
  pack_json TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);
"""


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _now_ts() -> int:
    return int(time.time())


def _make_id(prefix: str, payload: str) -> str:
    # stable-ish IDs: prefix + short hash
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    document_id: str
    ordinal: int
    score: float
    sha256: str
    start_char: int
    end_char: int


class SqliteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.executescript(SCHEMA)
            con.commit()

    # -------- Documents --------
    def upsert_document(self, *, source_name: str | None, text: str) -> str:
        doc_hash = _sha256(text)
        doc_id = _make_id("doc", doc_hash)

        with self._connect() as con:
            con.execute(
                """
                INSERT OR IGNORE INTO documents (id, created_at, source_name, sha256, text_len)
                VALUES (?, ?, ?, ?, ?)
                """,
                (doc_id, _now_ts(), source_name, doc_hash, len(text)),
            )
            con.commit()

        return doc_id

    def insert_chunks(
        self,
        *,
        document_id: str,
        chunks: Iterable[dict[str, Any]],
    ) -> None:
        with self._connect() as con:
            for ch in chunks:
                con.execute(
                    """
                    INSERT OR REPLACE INTO chunks
                    (id, document_id, ordinal, start_char, end_char, sha256, text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ch["id"],
                        document_id,
                        ch["ordinal"],
                        ch["start_char"],
                        ch["end_char"],
                        ch["sha256"],
                        ch["text"],
                    ),
                )
            con.commit()

    def get_chunks(self, *, document_id: str) -> list[sqlite3.Row]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT * FROM chunks WHERE document_id = ?
                ORDER BY ordinal ASC
                """,
                (document_id,),
            ).fetchall()
        return rows

    def get_document(self, *, document_id: str) -> sqlite3.Row | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return row

    # -------- Audit --------
    def insert_audit(
        self,
        *,
        document_id: str,
        question: str,
        answer: str,
        citations: list[Citation],
        pack: dict[str, Any],
    ) -> str:
        payload = f"{document_id}:{question}:{pack.get('created_at')}:{answer[:100]}"
        audit_id = _make_id("audit", payload)

        citations_json = json.dumps([asdict(c) for c in citations], ensure_ascii=False)
        pack_json = json.dumps(pack, ensure_ascii=False)

        with self._connect() as con:
            con.execute(
                """
                INSERT OR REPLACE INTO audits
                (id, created_at, document_id, question, answer, citations_json, pack_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (audit_id, _now_ts(), document_id, question, answer, citations_json, pack_json),
            )
            con.commit()

        return audit_id
