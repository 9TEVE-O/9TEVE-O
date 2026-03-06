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

    def __post_init__(self) -> None:
        if self.chunk_size_chars <= 0:
            raise ValueError(
                f"ATA_CHUNK_SIZE_CHARS must be > 0, got {self.chunk_size_chars}"
            )
        if self.chunk_overlap_chars < 0:
            raise ValueError(
                f"ATA_CHUNK_OVERLAP_CHARS must be >= 0, got {self.chunk_overlap_chars}"
            )
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError(
                f"ATA_CHUNK_OVERLAP_CHARS ({self.chunk_overlap_chars}) must be "
                f"strictly less than ATA_CHUNK_SIZE_CHARS ({self.chunk_size_chars}) "
                "to prevent an infinite loop in the chunker."
            )
        if self.max_context_chunks <= 0:
            raise ValueError(
                f"ATA_MAX_CONTEXT_CHUNKS must be > 0, got {self.max_context_chunks}"
            )
        if self.max_answer_chars <= 0:
            raise ValueError(
                f"ATA_MAX_ANSWER_CHARS must be > 0, got {self.max_answer_chars}"
            )


settings = Settings()
