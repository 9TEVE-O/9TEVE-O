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
    github_token: str | None = os.getenv("ATA_GITHUB_TOKEN")

    def __post_init__(self) -> None:
        if self.chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars (ATA_CHUNK_SIZE_CHARS) must be greater than 0")
        if self.chunk_overlap_chars < 0:
            raise ValueError("chunk_overlap_chars (ATA_CHUNK_OVERLAP_CHARS) must be greater than or equal to 0")
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError(
                "chunk_overlap_chars (ATA_CHUNK_OVERLAP_CHARS) must be strictly less than "
                "chunk_size_chars (ATA_CHUNK_SIZE_CHARS) to avoid an infinite loop while chunking"
            )
        if self.max_context_chunks <= 0:
            raise ValueError("max_context_chunks (ATA_MAX_CONTEXT_CHUNKS) must be greater than 0")
        if self.max_answer_chars <= 0:
            raise ValueError("max_answer_chars (ATA_MAX_ANSWER_CHARS) must be greater than 0")


settings = Settings()
