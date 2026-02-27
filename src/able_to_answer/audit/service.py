from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from able_to_answer.core.storage import Citation


def build_audit_pack(
    *,
    document_id: str,
    question: str,
    answer: str,
    citations: list[Citation],
    retrieval_mode: str,
) -> dict[str, Any]:
    return {
        "created_at": int(time.time()),
        "document_id": document_id,
        "question": question,
        "answer": answer,
        "retrieval": {
            "mode": retrieval_mode,
            "citations": [asdict(c) for c in citations],
        },
        "limits": {
            "note": "This MVP uses lexical retrieval and an extractive answer builder; no external LLM call.",
        },
    }
