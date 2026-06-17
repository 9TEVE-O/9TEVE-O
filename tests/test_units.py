"""Unit tests for ingestion, retrieval, and audit internal functions."""

from __future__ import annotations

from collections import Counter

import pytest

from able_to_answer.audit.service import build_audit_pack, self_modelling_pressure
from able_to_answer.core.config import Settings
from able_to_answer.core.storage import Citation, SqliteStore
from able_to_answer.ingestion.service import _chunk_text, ingest_text
from able_to_answer.retrieval.service import _score, _tokenise, retrieve_top_chunks

# ────────────────────────────────────────────────────────────
# Ingestion — _chunk_text
# ────────────────────────────────────────────────────────────


def test_chunk_text_single_chunk():
    text = "Short text."
    chunks = list(_chunk_text(text, size=100, overlap=10))
    assert len(chunks) == 1
    assert chunks[0]["ordinal"] == 0
    assert chunks[0]["text"] == "Short text."
    assert chunks[0]["start_char"] == 0
    assert len(chunks[0]["sha256"]) == 64


def test_chunk_text_multiple_chunks():
    text = "a" * 100
    chunks = list(_chunk_text(text, size=50, overlap=10))
    assert len(chunks) >= 2
    # ordinals increase
    ordinals = [c["ordinal"] for c in chunks]
    assert ordinals == list(range(len(ordinals)))


def test_chunk_text_overlap_produces_overlap():
    text = "x" * 100
    chunks = list(_chunk_text(text, size=60, overlap=20))
    # Second chunk should start before end of first
    if len(chunks) >= 2:
        assert chunks[1]["start_char"] < chunks[0]["end_char"]


def test_chunk_text_skips_whitespace_only():
    # A chunk of just whitespace should not be yielded
    chunks = list(_chunk_text("   ", size=100, overlap=10))
    assert chunks == []


def test_chunk_text_windows_line_endings():
    text = "line one\r\nline two\r\nline three"
    chunks = list(_chunk_text(text, size=200, overlap=0))
    assert len(chunks) == 1
    # \r\n is normalised to \n
    assert "\r" not in chunks[0]["text"]


def test_ingest_text_raises_on_empty(tmp_path):
    store = SqliteStore(str(tmp_path / "db.sqlite3"))
    with pytest.raises(ValueError):
        ingest_text(store, source_name="test", text="   ")


def test_ingest_text_idempotent(tmp_path):
    store = SqliteStore(str(tmp_path / "db.sqlite3"))
    r1 = ingest_text(store, source_name="test", text="Hello world.")
    r2 = ingest_text(store, source_name="test", text="Hello world.")
    assert r1.document_id == r2.document_id
    assert r1.document_sha256 == r2.document_sha256


# ────────────────────────────────────────────────────────────
# Retrieval — _tokenise and _score
# ────────────────────────────────────────────────────────────


def test_tokenise_basic():
    tokens = _tokenise("Hello World!")
    assert tokens == ["hello", "world"]


def test_tokenise_empty():
    assert _tokenise("") == []


def test_tokenise_numbers_and_apostrophes():
    tokens = _tokenise("it's 2024 ok")
    assert "it's" in tokens
    assert "2024" in tokens


def test_score_exact_overlap():
    q = Counter(["audit", "trail"])
    c = Counter(["audit", "trail", "compliance"])
    s = _score(q, c)
    assert s > 0.0


def test_score_no_overlap():
    q = Counter(["audit"])
    c = Counter(["banana", "apple"])
    s = _score(q, c)
    assert s == 0.0


def test_score_empty_chunk():
    q = Counter(["audit"])
    # empty chunk → denom = sqrt(max(1, 0)) = 1, overlap = 0
    s = _score(q, Counter())
    assert s == 0.0


def test_retrieve_top_chunks_returns_empty_for_no_chunks(tmp_path):
    store = SqliteStore(str(tmp_path / "db.sqlite3"))
    result = retrieve_top_chunks(
        store, document_id="doc_doesnotexist", question="anything"
    )
    assert result == []


def test_retrieve_top_chunks_ranks_relevant_first(tmp_path):
    store = SqliteStore(str(tmp_path / "db.sqlite3"))
    # Produce two distinct chunks: one about audit, one about unrelated fruit
    audit_text = "audit trails compliance governance framework " * 30
    fruit_text = " " * 50 + "apples oranges bananas fruit salad " * 30
    result = ingest_text(store, source_name="test", text=audit_text + fruit_text)
    citations = retrieve_top_chunks(
        store, document_id=result.document_id, question="audit compliance"
    )
    assert len(citations) >= 2
    # The first result must score strictly higher than the second — the audit
    # chunk should outrank the unrelated fruit chunk for this query.
    assert citations[0].score > citations[1].score
    top = citations[0]
    assert isinstance(top, Citation)
    assert top.document_id == result.document_id
    assert top.score > 0.0


# ────────────────────────────────────────────────────────────
# Audit — build_audit_pack
# ────────────────────────────────────────────────────────────


def test_build_audit_pack_structure():
    citation = Citation(
        chunk_id="chunk_abc",
        document_id="doc_xyz",
        ordinal=0,
        score=0.75,
        sha256="a" * 64,
        start_char=0,
        end_char=100,
    )
    pack = build_audit_pack(
        document_id="doc_xyz",
        question="What is the policy?",
        answer="The policy requires compliance.",
        citations=[citation],
        retrieval_mode="lexical_overlap_v1",
    )
    assert pack["document_id"] == "doc_xyz"
    assert pack["question"] == "What is the policy?"
    assert pack["answer"] == "The policy requires compliance."
    assert "created_at" in pack
    assert isinstance(pack["created_at"], int)
    assert pack["retrieval"]["mode"] == "lexical_overlap_v1"
    assert len(pack["retrieval"]["citations"]) == 1


def test_build_audit_pack_empty_citations():
    pack = build_audit_pack(
        document_id="doc_1",
        question="q",
        answer="a",
        citations=[],
        retrieval_mode="lexical_overlap_v1",
    )
    assert pack["retrieval"]["citations"] == []


# ────────────────────────────────────────────────────────────
# Audit — self_modelling_pressure
# ────────────────────────────────────────────────────────────


def test_self_modelling_pressure_low_for_empty_system():
    result = self_modelling_pressure({})

    assert result["self_modelling_pressure_score"] == 0.0
    assert result["review_level"] == "LOW: tool-like system"
    assert "does not prove consciousness" in result["warning"]


def test_self_modelling_pressure_critical_for_all_features():
    result = self_modelling_pressure(
        {
            "complexity": 1.0,
            "world_model": 1.0,
            "self_model": 1.0,
            "persistent_memory": 1.0,
            "autonomous_goals": 1.0,
            "embodied_or_feedback_loop": 1.0,
            "uncertainty_tracking": 1.0,
            "social_prediction": 1.0,
            "affect_like_regulation": 1.0,
            "recursive_control": 1.0,
        }
    )

    assert result["self_modelling_pressure_score"] == 1.1
    assert result["review_level"] == (
        "CRITICAL: treat as morally and operationally sensitive"
    )


def test_self_modelling_pressure_review_threshold_boundaries():
    assert (
        self_modelling_pressure({"self_model": 1.0, "world_model": 1.0})["review_level"]
        == "LOW: tool-like system"
    )

    assert (
        self_modelling_pressure(
            {
                "self_model": 1.0,
                "world_model": 1.0,
                "complexity": 0.25,
            }
        )["review_level"]
        == "MODERATE: monitor for agency-like behaviour"
    )

    assert (
        self_modelling_pressure(
            {
                "self_model": 1.0,
                "world_model": 1.0,
                "persistent_memory": 1.0,
                "autonomous_goals": 1.0,
                "uncertainty_tracking": 1.0,
            }
        )["review_level"]
        == "HIGH: requires ethical and safety review"
    )


# ────────────────────────────────────────────────────────────
# Settings validation
# ────────────────────────────────────────────────────────────

def test_settings_valid_defaults():
    s = Settings(
        db_path="test.sqlite3",
        chunk_size_chars=1200,
        chunk_overlap_chars=200,
        max_context_chunks=6,
        max_answer_chars=1800,
    )
    assert s.chunk_size_chars == 1200
    assert s.chunk_overlap_chars == 200


def test_settings_overlap_equal_to_size_raises():
    with pytest.raises(ValueError, match="ATA_CHUNK_OVERLAP_CHARS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=500,
            chunk_overlap_chars=500,
            max_context_chunks=6,
            max_answer_chars=1800,
        )


def test_settings_overlap_greater_than_size_raises():
    with pytest.raises(ValueError, match="ATA_CHUNK_OVERLAP_CHARS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=100,
            chunk_overlap_chars=200,
            max_context_chunks=6,
            max_answer_chars=1800,
        )


def test_settings_zero_chunk_size_raises():
    with pytest.raises(ValueError, match="ATA_CHUNK_SIZE_CHARS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=0,
            chunk_overlap_chars=0,
            max_context_chunks=6,
            max_answer_chars=1800,
        )


def test_settings_negative_overlap_raises():
    with pytest.raises(ValueError, match="ATA_CHUNK_OVERLAP_CHARS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=1200,
            chunk_overlap_chars=-1,
            max_context_chunks=6,
            max_answer_chars=1800,
        )


def test_settings_zero_max_context_chunks_raises():
    with pytest.raises(ValueError, match="ATA_MAX_CONTEXT_CHUNKS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=1200,
            chunk_overlap_chars=200,
            max_context_chunks=0,
            max_answer_chars=1800,
        )


def test_settings_zero_max_answer_chars_raises():
    with pytest.raises(ValueError, match="ATA_MAX_ANSWER_CHARS"):
        Settings(
            db_path="x.sqlite3",
            chunk_size_chars=1200,
            chunk_overlap_chars=200,
            max_context_chunks=6,
            max_answer_chars=0,
        )
