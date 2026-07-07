from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from able_to_answer.core.storage import Citation

SELF_MODELLING_PRESSURE_WEIGHTS: dict[str, float] = {
    "complexity": 0.08,
    "world_model": 0.12,
    "self_model": 0.16,
    "persistent_memory": 0.12,
    "autonomous_goals": 0.12,
    "embodied_or_feedback_loop": 0.10,
    "uncertainty_tracking": 0.10,
    "social_prediction": 0.08,
    "affect_like_regulation": 0.10,
    "recursive_control": 0.12,
}


def self_modelling_pressure(system: dict[str, float]) -> dict[str, Any]:
    """Score whether a system deserves deeper review for awareness-like behaviour.

    This is not a consciousness detector. It is a governance and research triage
    function. Each input feature should be scored from 0.0 to 1.0; missing
    features are treated as 0.0.
    """
    score = sum(
        system.get(feature, 0.0) * weight
        for feature, weight in SELF_MODELLING_PRESSURE_WEIGHTS.items()
    )

    if score < 0.30:
        review_level = "LOW: tool-like system"
    elif score < 0.55:
        review_level = "MODERATE: monitor for agency-like behaviour"
    elif score < 0.75:
        review_level = "HIGH: requires ethical and safety review"
    else:
        review_level = "CRITICAL: treat as morally and operationally sensitive"

    return {
        "self_modelling_pressure_score": round(score, 3),
        "review_level": review_level,
        "warning": (
            "This score does not prove consciousness. "
            "It flags systems that require deeper review."
        ),
    }


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
