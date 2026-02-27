from __future__ import annotations

import math
import re
from collections import Counter

from able_to_answer.core.config import settings
from able_to_answer.core.storage import Citation

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _tokenise(s: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(s)]


def _score(query_tokens: Counter, chunk_tokens: Counter) -> float:
    # Simple weighted overlap: sum(min(q, c)) / sqrt(|chunk|)
    overlap = sum(min(query_tokens[t], chunk_tokens.get(t, 0)) for t in query_tokens)
    denom = math.sqrt(max(1, sum(chunk_tokens.values())))
    return float(overlap) / denom


def retrieve_top_chunks(store, *, document_id: str, question: str) -> list[Citation]:
    rows = store.get_chunks(document_id=document_id)
    if not rows:
        return []

    q = Counter(_tokenise(question))
    scored: list[tuple[float, Citation]] = []

    for r in rows:
        c_tokens = Counter(_tokenise(r["text"]))
        s = _score(q, c_tokens)
        if s <= 0:
            continue
        scored.append(
            (
                s,
                Citation(
                    chunk_id=r["id"],
                    document_id=r["document_id"],
                    ordinal=int(r["ordinal"]),
                    score=s,
                    sha256=r["sha256"],
                    start_char=int(r["start_char"]),
                    end_char=int(r["end_char"]),
                ),
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in scored[: settings.max_context_chunks]]
    return top
