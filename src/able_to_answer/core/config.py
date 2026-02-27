from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("ATA_DB_PATH", "able_to_answer.sqlite3")
    chunk_size_chars: int = int(os.getenv("ATA_CHUNK_SIZE_CHARS", "1200"))
    chunk_overlap_chars: int = int(os.getenv("ATA_CHUNK_OVERLAP_CHARS", "200"))
    max_context_chunks: int = int(os.getenv("ATA_MAX_CONTEXT_CHUNKS", "6"))
    max_answer_chars: int = int(os.getenv("ATA_MAX_ANSWER_CHARS", "1800"))


settings = Settings()
