"""Unit tests for Settings.__post_init__ validation logic."""

from __future__ import annotations

import ast
from pathlib import Path

import able_to_answer.core.config as config_module
import pytest

from able_to_answer.core.config import Settings

# ---------------------------------------------------------------------------
# Helper – build a valid Settings with explicit values so env-vars are
# bypassed and we have a known baseline to mutate per test.
# ---------------------------------------------------------------------------

_VALID_KWARGS: dict = dict(
    db_path="test.sqlite3",
    chunk_size_chars=1200,
    chunk_overlap_chars=200,
    max_context_chunks=6,
    max_answer_chars=1800,
    github_token=None,
)


def _make(**overrides) -> Settings:
    return Settings(**{**_VALID_KWARGS, **overrides})


# ---------------------------------------------------------------------------
# Happy-path: valid construction
# ---------------------------------------------------------------------------


def test_settings_valid_defaults_succeed():
    """A Settings instance with valid values should construct without error."""
    s = _make()
    assert s.chunk_size_chars == 1200
    assert s.chunk_overlap_chars == 200
    assert s.max_context_chunks == 6
    assert s.max_answer_chars == 1800


def test_settings_minimum_valid_values_succeed():
    """Boundary-minimum values that are just inside the valid range succeed."""
    s = _make(
        chunk_size_chars=1,
        chunk_overlap_chars=0,
        max_context_chunks=1,
        max_answer_chars=1,
    )
    assert s.chunk_size_chars == 1
    assert s.chunk_overlap_chars == 0
    assert s.max_context_chunks == 1
    assert s.max_answer_chars == 1


def test_settings_chunk_overlap_zero_is_valid():
    """chunk_overlap_chars=0 is explicitly allowed (>= 0 threshold)."""
    s = _make(chunk_overlap_chars=0)
    assert s.chunk_overlap_chars == 0


# ---------------------------------------------------------------------------
# chunk_size_chars validation
# ---------------------------------------------------------------------------


def test_settings_chunk_size_chars_zero_raises():
    with pytest.raises(ValueError, match="chunk_size_chars"):
        _make(chunk_size_chars=0)


def test_settings_chunk_size_chars_negative_raises():
    with pytest.raises(ValueError, match="chunk_size_chars"):
        _make(chunk_size_chars=-1)


def test_settings_chunk_size_chars_error_mentions_env_var():
    with pytest.raises(ValueError, match="ATA_CHUNK_SIZE_CHARS"):
        _make(chunk_size_chars=0)


# ---------------------------------------------------------------------------
# chunk_overlap_chars validation
# ---------------------------------------------------------------------------


def test_settings_chunk_overlap_chars_negative_raises():
    with pytest.raises(ValueError, match="chunk_overlap_chars"):
        _make(chunk_overlap_chars=-1)


def test_settings_chunk_overlap_chars_negative_error_mentions_env_var():
    with pytest.raises(ValueError, match="ATA_CHUNK_OVERLAP_CHARS"):
        _make(chunk_overlap_chars=-1)


def test_settings_chunk_overlap_chars_equal_to_chunk_size_raises():
    """chunk_overlap_chars == chunk_size_chars is forbidden (infinite loop)."""
    with pytest.raises(ValueError, match="chunk_overlap_chars"):
        _make(chunk_size_chars=500, chunk_overlap_chars=500)


def test_settings_chunk_overlap_chars_greater_than_chunk_size_raises():
    with pytest.raises(ValueError, match="chunk_overlap_chars"):
        _make(chunk_size_chars=100, chunk_overlap_chars=200)


def test_settings_chunk_overlap_equal_error_mentions_infinite_loop():
    """The error message for overlap >= size should mention the infinite-loop risk."""
    with pytest.raises(ValueError, match="infinite loop"):
        _make(chunk_size_chars=100, chunk_overlap_chars=100)


def test_settings_chunk_overlap_equal_error_mentions_both_env_vars():
    with pytest.raises(ValueError, match="ATA_CHUNK_OVERLAP_CHARS"):
        _make(chunk_size_chars=100, chunk_overlap_chars=100)


def test_settings_chunk_overlap_one_less_than_chunk_size_is_valid():
    """chunk_overlap_chars == chunk_size_chars - 1 is the maximum valid overlap."""
    s = _make(chunk_size_chars=10, chunk_overlap_chars=9)
    assert s.chunk_overlap_chars == 9


# ---------------------------------------------------------------------------
# max_context_chunks validation
# ---------------------------------------------------------------------------


def test_settings_max_context_chunks_zero_raises():
    with pytest.raises(ValueError, match="max_context_chunks"):
        _make(max_context_chunks=0)


def test_settings_max_context_chunks_negative_raises():
    with pytest.raises(ValueError, match="max_context_chunks"):
        _make(max_context_chunks=-5)


def test_settings_max_context_chunks_error_mentions_env_var():
    with pytest.raises(ValueError, match="ATA_MAX_CONTEXT_CHUNKS"):
        _make(max_context_chunks=0)


# ---------------------------------------------------------------------------
# max_answer_chars validation
# ---------------------------------------------------------------------------


def test_settings_max_answer_chars_zero_raises():
    with pytest.raises(ValueError, match="max_answer_chars"):
        _make(max_answer_chars=0)


def test_settings_max_answer_chars_negative_raises():
    with pytest.raises(ValueError, match="max_answer_chars"):
        _make(max_answer_chars=-100)


def test_settings_max_answer_chars_error_mentions_env_var():
    with pytest.raises(ValueError, match="ATA_MAX_ANSWER_CHARS"):
        _make(max_answer_chars=0)


# ---------------------------------------------------------------------------
# Regression: validation order – chunk_size_chars is checked before overlap
# ---------------------------------------------------------------------------


def test_settings_chunk_size_checked_before_overlap():
    """When both chunk_size_chars and chunk_overlap_chars are invalid,
    the error raised first should be about chunk_size_chars."""
    with pytest.raises(ValueError, match="chunk_size_chars"):
        _make(chunk_size_chars=0, chunk_overlap_chars=-1)


# ---------------------------------------------------------------------------
# Regression: Settings must define __post_init__ exactly once.
#
# A previous version of this module accidentally defined __post_init__
# twice; the second (duplicate) definition silently shadowed the first
# and used a different, terser error-message format ("ATA_X must be > 0,
# got Y" with no field name prefix). These tests pin the *current*,
# single-definition message format so a regression to the duplicate
# method would be caught immediately.
# ---------------------------------------------------------------------------


def test_settings_defines_post_init_exactly_once():
    module_ast = ast.parse(Path(config_module.__file__).read_text(encoding="utf-8"))
    settings_class = next(
        node
        for node in module_ast.body
        if isinstance(node, ast.ClassDef) and node.name == "Settings"
    )
    post_init_defs = [
        node
        for node in settings_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    ]
    assert len(post_init_defs) == 1


def test_settings_chunk_size_error_uses_canonical_message_format():
    with pytest.raises(
        ValueError,
        match=r"chunk_size_chars \(ATA_CHUNK_SIZE_CHARS\) must be greater than 0, got 0\.",
    ):
        _make(chunk_size_chars=0)


def test_settings_chunk_overlap_negative_error_uses_canonical_message_format():
    with pytest.raises(
        ValueError,
        match=(
            r"chunk_overlap_chars \(ATA_CHUNK_OVERLAP_CHARS\) must be greater "
            r"than or equal to 0, got -1\."
        ),
    ):
        _make(chunk_overlap_chars=-1)


def test_settings_chunk_overlap_size_error_uses_canonical_message_format():
    """The overlap-vs-size message must use the current wording ("must be
    less than ... to avoid an infinite loop"), not the removed duplicate's
    wording ("must be strictly less than ... to prevent an infinite loop
    in the chunker")."""
    with pytest.raises(
        ValueError,
        match=(
            r"chunk_overlap_chars \(ATA_CHUNK_OVERLAP_CHARS\) must be less than "
            r"chunk_size_chars \(ATA_CHUNK_SIZE_CHARS\), got 100 and got 100, "
            r"to avoid an infinite loop\."
        ),
    ):
        _make(chunk_size_chars=100, chunk_overlap_chars=100)


def test_settings_max_context_chunks_error_uses_canonical_message_format():
    with pytest.raises(
        ValueError,
        match=r"max_context_chunks \(ATA_MAX_CONTEXT_CHUNKS\) must be greater than 0, got 0\.",
    ):
        _make(max_context_chunks=0)


def test_settings_max_answer_chars_error_uses_canonical_message_format():
    with pytest.raises(
        ValueError,
        match=r"max_answer_chars \(ATA_MAX_ANSWER_CHARS\) must be greater than 0, got -100\.",
    ):
        _make(max_answer_chars=-100)
