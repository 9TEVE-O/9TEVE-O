"""Unit tests for scripts/gh_review_bot.py guardrail functions.

All tests exercise only the pure, I/O-free functions so that no network
calls are made and no GitHub token is required.
"""
from __future__ import annotations

import sys
import os

# Make the scripts/ directory importable without installing it as a package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import gh_review_bot as bot  # noqa: E402


# ─────────────────────────────────────────────────────────
# classify_files
# ─────────────────────────────────────────────────────────

def test_classify_files_no_sensitive():
    has_sensitive, hits = bot.classify_files(["docs/index.md", "README.md"])
    assert has_sensitive is False
    assert hits == []


def test_classify_files_exact_match():
    has_sensitive, hits = bot.classify_files(["pyproject.toml"])
    assert has_sensitive is True
    assert "pyproject.toml" in hits


def test_classify_files_prefix_match():
    has_sensitive, hits = bot.classify_files(
        [".github/workflows/ci.yml"]
    )
    assert has_sensitive is True
    assert ".github/workflows/ci.yml" in hits


def test_classify_files_mixed():
    files = ["docs/readme.md", "src/able_to_answer/control_plane/policy.py"]
    has_sensitive, hits = bot.classify_files(files)
    assert has_sensitive is True
    assert "src/able_to_answer/control_plane/policy.py" in hits
    assert "docs/readme.md" not in hits


def test_classify_files_empty():
    has_sensitive, hits = bot.classify_files([])
    assert has_sensitive is False
    assert hits == []


def test_classify_files_env_example():
    has_sensitive, hits = bot.classify_files([".env.example"])
    assert has_sensitive is True


def test_classify_files_core_config():
    has_sensitive, hits = bot.classify_files(
        ["src/able_to_answer/core/config.py"]
    )
    assert has_sensitive is True


# ─────────────────────────────────────────────────────────
# all_safe_paths
# ─────────────────────────────────────────────────────────

def test_all_safe_paths_empty_list():
    assert bot.all_safe_paths([]) is True


def test_all_safe_paths_docs_only():
    assert bot.all_safe_paths(["docs/guide.md", "docs/api.md"]) is True


def test_all_safe_paths_tests_only():
    assert bot.all_safe_paths(["tests/test_foo.py"]) is True


def test_all_safe_paths_readme():
    assert bot.all_safe_paths(["README.md"]) is True


def test_all_safe_paths_adr():
    assert bot.all_safe_paths(["ADR/ADR-0001.md"]) is True


def test_all_safe_paths_mixed_unsafe():
    # src/ is not a safe prefix
    assert bot.all_safe_paths(["docs/guide.md", "src/able_to_answer/api/main.py"]) is False


def test_all_safe_paths_single_unsafe():
    assert bot.all_safe_paths(["src/able_to_answer/api/main.py"]) is False


# ─────────────────────────────────────────────────────────
# decide_action — draft
# ─────────────────────────────────────────────────────────

def test_decide_action_draft_always_acknowledges():
    action = bot.decide_action(
        is_draft=True,
        changed_files=["docs/guide.md"],
        check_conclusions=["success"],
    )
    assert action == "acknowledge_draft"


def test_decide_action_draft_even_with_sensitive_files():
    """Draft guardrail is checked before sensitive-path guardrail."""
    action = bot.decide_action(
        is_draft=True,
        changed_files=["pyproject.toml"],
        check_conclusions=["success"],
    )
    assert action == "acknowledge_draft"


# ─────────────────────────────────────────────────────────
# decide_action — sensitive files
# ─────────────────────────────────────────────────────────

def test_decide_action_sensitive_files():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["src/able_to_answer/control_plane/policy.py"],
        check_conclusions=["success"],
    )
    assert action == "flag_sensitive"


def test_decide_action_sensitive_takes_priority_over_ci():
    """Sensitive-file guardrail fires before CI check."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["pyproject.toml"],
        check_conclusions=["failure"],
    )
    assert action == "flag_sensitive"


# ─────────────────────────────────────────────────────────
# decide_action — CI checks
# ─────────────────────────────────────────────────────────

def test_decide_action_ci_pending_none():
    """A None conclusion means the check is still in progress."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=[None],
    )
    assert action == "ci_pending"


def test_decide_action_ci_pending_queued():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["queued"],
    )
    assert action == "ci_pending"


def test_decide_action_ci_failing():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["failure"],
    )
    assert action == "ci_failing"


def test_decide_action_ci_timed_out():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["timed_out"],
    )
    assert action == "ci_failing"


def test_decide_action_ci_cancelled():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["cancelled"],
    )
    assert action == "ci_failing"


def test_decide_action_ci_action_required():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["action_required"],
    )
    assert action == "ci_failing"


def test_decide_action_ci_startup_failure():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["startup_failure"],
    )
    assert action == "ci_failing"


def test_decide_action_empty_checks_defers():
    """Empty check list means CI hasn't started — always defer."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=[],
    )
    assert action == "ci_pending"


def test_decide_action_mixed_success_and_failure():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["success", "failure"],
    )
    assert action == "ci_failing"


def test_decide_action_mixed_success_and_pending():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["success", None],
    )
    assert action == "ci_pending"


# ─────────────────────────────────────────────────────────
# decide_action — approve
# ─────────────────────────────────────────────────────────

def test_decide_action_approve_docs_only_all_success():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md", "ADR/ADR-0002.md"],
        check_conclusions=["success", "success"],
    )
    assert action == "approve"


def test_decide_action_approve_no_checks_safe_paths():
    """Empty check list means CI hasn't started yet — defers to ci_pending."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/index.md"],
        check_conclusions=[],
    )
    assert action == "ci_pending"


def test_decide_action_approve_tests_path():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["tests/test_new.py"],
        check_conclusions=["success"],
    )
    assert action == "approve"


def test_decide_action_approve_neutral_check():
    """neutral is not a failure — should not block approval."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md"],
        check_conclusions=["success", "neutral"],
    )
    assert action == "approve"


# ─────────────────────────────────────────────────────────
# decide_action — general acknowledge
# ─────────────────────────────────────────────────────────

def test_decide_action_acknowledge_src_changes_all_success():
    """Non-sensitive src changes with passing CI get general acknowledgment."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=["src/able_to_answer/api/models.py"],
        check_conclusions=["success"],
    )
    assert action == "acknowledge"


def test_decide_action_acknowledge_mixed_safe_and_src():
    action = bot.decide_action(
        is_draft=False,
        changed_files=["docs/guide.md", "src/able_to_answer/api/main.py"],
        check_conclusions=["success"],
    )
    assert action == "acknowledge"


def test_decide_action_acknowledge_no_files_no_checks():
    """Empty PR with no checks — CI hasn't started, so defer."""
    action = bot.decide_action(
        is_draft=False,
        changed_files=[],
        check_conclusions=[],
    )
    assert action == "ci_pending"
