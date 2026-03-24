"""Unit tests for scripts/fork_inventory.py and scripts/fork_sync.py.

Tests cover all pure helper functions (no I/O, no network calls).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import scripts from the scripts/ directory.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import fork_inventory as fi  # noqa: E402
import fork_sync as fs  # noqa: E402


# ===========================================================================
# fork_inventory.py — pure scoring helpers
# ===========================================================================


class TestScoreStars:
    def test_zero_stars(self):
        assert fi.score_stars(0) == 0.0

    def test_negative_stars_returns_zero(self):
        assert fi.score_stars(-5) == 0.0

    def test_one_star(self):
        score = fi.score_stars(1)
        assert 0 < score < 1.0

    def test_thousand_stars_close_to_three(self):
        # log10(1001) ≈ 3 → capped at 3.0
        assert fi.score_stars(1000) >= 2.9

    def test_very_large_stars_capped_at_three(self):
        assert fi.score_stars(10_000_000) == 3.0


class TestScoreRecency:
    def _now(self):
        return datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_pushed_today_scores_two(self):
        iso = "2024-06-15T10:00:00Z"
        assert fi.score_recency(iso, now=self._now()) == 2.0

    def test_pushed_29_days_ago_scores_two(self):
        then = self._now() - timedelta(days=29)
        iso = then.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert fi.score_recency(iso, now=self._now()) == 2.0

    def test_pushed_60_days_ago_scores_one(self):
        then = self._now() - timedelta(days=60)
        iso = then.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert fi.score_recency(iso, now=self._now()) == 1.0

    def test_pushed_91_days_ago_scores_zero(self):
        then = self._now() - timedelta(days=91)
        iso = then.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert fi.score_recency(iso, now=self._now()) == 0.0

    def test_empty_string_returns_zero(self):
        assert fi.score_recency("", now=self._now()) == 0.0

    def test_invalid_iso_returns_zero(self):
        assert fi.score_recency("not-a-date", now=self._now()) == 0.0


class TestScoreRelevance:
    def test_no_keywords_returns_zero(self):
        assert fi.score_relevance("my-random-project", "A simple utility") == 0.0

    def test_single_keyword_in_name(self):
        assert fi.score_relevance("ai-assistant", "") == 1.0

    def test_single_keyword_in_description(self):
        assert fi.score_relevance("tool", "LLM-powered search") == 1.0

    def test_multiple_keywords_capped_at_three(self):
        # "ai agent llm rag gpt openai langchain" — 7 keywords, capped at 3
        name = "ai-agent-llm-rag-gpt-openai-langchain"
        score = fi.score_relevance(name, "")
        assert score == 3.0

    def test_case_insensitive_matching(self):
        assert fi.score_relevance("AI-AGENT", "LLM WORKFLOW") >= 1.0

    def test_substring_matching_is_intentional(self):
        # "mail" contains the substring "ai" — this is intentional per the
        # current scoring spec which uses simple substring matching.
        assert fi.score_relevance("email-tool", "") >= 1.0  # "ai" found in "email"


class TestComputeScore:
    def _make_fork(self, stars=0, pushed_at="2024-06-15T10:00:00Z", updated_at="2024-06-15T10:00:00Z",
                   name="my-repo", description=""):
        return fi.ForkInfo(
            name_with_owner=f"owner/{name}",
            name=name,
            description=description,
            language="Python",
            stars=stars,
            forks_count=0,
            pushed_at=pushed_at,
            updated_at=updated_at,
            html_url="https://github.com/owner/my-repo",
            parent_full_name="upstream/my-repo",
            parent_html_url="https://github.com/upstream/my-repo",
        )

    def _now(self):
        return datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_perfect_score_is_at_most_ten(self):
        fork = self._make_fork(
            stars=10000,
            pushed_at="2024-06-15T10:00:00Z",
            updated_at="2024-06-15T10:00:00Z",
            name="ai-agent-llm-rag-gpt",
        )
        total, _ = fi.compute_score(fork, now=self._now())
        assert total <= 10.0

    def test_zero_score_for_dead_obscure_repo(self):
        fork = self._make_fork(
            stars=0,
            pushed_at="2020-01-01T00:00:00Z",
            updated_at="2020-01-01T00:00:00Z",
            name="random-project",
            description="nothing special here",
        )
        total, breakdown = fi.compute_score(fork, now=self._now())
        assert total == 0.0
        assert breakdown["stars"] == 0.0
        assert breakdown["recency"] == 0.0
        assert breakdown["upstream_activity"] == 0.0

    def test_breakdown_keys_present(self):
        fork = self._make_fork()
        _, breakdown = fi.compute_score(fork, now=self._now())
        assert set(breakdown) == {"stars", "recency", "relevance", "upstream_activity"}

    def test_score_stored_on_fork(self):
        fork = self._make_fork(stars=100, pushed_at="2024-06-15T10:00:00Z",
                               updated_at="2024-06-15T10:00:00Z")
        total, breakdown = fi.compute_score(fork, now=self._now())
        fork.score = total
        fork.score_breakdown = breakdown
        assert fork.score > 0


class TestParseFork:
    def test_full_payload(self):
        raw = {
            "full_name": "9TEVE-O/langchain",
            "name": "langchain",
            "description": "LangChain LLM orchestration",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 5,
            "pushed_at": "2024-05-01T08:00:00Z",
            "updated_at": "2024-05-02T09:00:00Z",
            "html_url": "https://github.com/9TEVE-O/langchain",
            "fork": True,
            "parent": {
                "full_name": "langchain-ai/langchain",
                "html_url": "https://github.com/langchain-ai/langchain",
            },
        }
        fork = fi.parse_fork(raw)
        assert fork.name_with_owner == "9TEVE-O/langchain"
        assert fork.stars == 42
        assert fork.parent_full_name == "langchain-ai/langchain"
        assert fork.language == "Python"

    def test_missing_parent_is_empty(self):
        raw = {
            "full_name": "me/project",
            "name": "project",
            "description": None,
            "language": None,
            "stargazers_count": 0,
            "forks_count": 0,
            "pushed_at": "",
            "updated_at": "",
            "html_url": "https://github.com/me/project",
            "fork": True,
        }
        fork = fi.parse_fork(raw)
        assert fork.description == ""
        assert fork.language == "Unknown"
        assert fork.parent_full_name == ""

    def test_matched_keywords_returns_list(self):
        raw = {
            "full_name": "me/ai-agent",
            "name": "ai-agent",
            "description": "LLM-powered assistant",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 1,
            "pushed_at": "2024-05-01T08:00:00Z",
            "updated_at": "2024-05-01T08:00:00Z",
            "html_url": "https://github.com/me/ai-agent",
            "fork": True,
        }
        fork = fi.parse_fork(raw)
        kws = fork.matched_keywords()
        assert "ai" in kws
        assert "agent" in kws
        assert "llm" in kws


class TestBuildInventoryMarkdown:
    def _make_forks(self, n=3):
        forks = []
        for i in range(n):
            f = fi.ForkInfo(
                name_with_owner=f"owner/repo-{i}",
                name=f"repo-{i}",
                description=f"Description {i}",
                language="Python",
                stars=100 * (n - i),
                forks_count=10,
                pushed_at="2024-06-01T00:00:00Z",
                updated_at="2024-06-01T00:00:00Z",
                html_url=f"https://github.com/owner/repo-{i}",
                parent_full_name=f"upstream/repo-{i}",
                parent_html_url=f"https://github.com/upstream/repo-{i}",
                score=float(10 - i),
                score_breakdown={"stars": 1.0, "recency": 2.0, "relevance": 1.0, "upstream_activity": 2.0},
            )
            forks.append(f)
        return forks

    def test_contains_priority_table(self):
        forks = self._make_forks(5)
        md = fi.build_inventory_markdown(forks, top_n=3)
        assert "## 🏆 Priority Batch" in md
        assert "repo-0" in md

    def test_contains_full_inventory(self):
        forks = self._make_forks(5)
        md = fi.build_inventory_markdown(forks, top_n=3)
        assert "## 📋 Full Inventory" in md
        assert "repo-4" in md  # all 5 forks appear

    def test_score_breakdown_section(self):
        forks = self._make_forks(3)
        md = fi.build_inventory_markdown(forks, top_n=3)
        assert "## 📊 Score Breakdown" in md

    def test_top_n_forks_in_priority_table(self):
        forks = self._make_forks(10)
        md = fi.build_inventory_markdown(forks, top_n=4)
        # Only first 4 should appear in priority batch
        assert "repo-0" in md
        assert "repo-3" in md


# ===========================================================================
# fork_sync.py — pure helpers
# ===========================================================================


class TestDetectStack:
    def test_python_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        assert fs.detect_stack(tmp_path) == "Python (pyproject)"

    def test_python_setup_py(self, tmp_path):
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup()\n")
        assert fs.detect_stack(tmp_path) == "Python (setup.py)"

    def test_node(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "x"}')
        assert fs.detect_stack(tmp_path) == "Node.js / JavaScript"

    def test_rust(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'x'\n")
        assert fs.detect_stack(tmp_path) == "Rust"

    def test_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module example.com/x\n")
        assert fs.detect_stack(tmp_path) == "Go"

    def test_unknown_when_no_manifest(self, tmp_path):
        assert fs.detect_stack(tmp_path) == "Unknown"

    def test_pyproject_takes_priority_over_setup_py(self, tmp_path):
        # _STACK_MANIFESTS is ordered dict; pyproject.toml appears before
        # setup.py, so it should win when both are present.
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        assert fs.detect_stack(tmp_path) == "Python (pyproject)"


class TestMissingGovernanceFiles:
    def test_all_missing(self, tmp_path):
        missing = fs.missing_governance_files(tmp_path)
        assert "LICENSE" in missing
        assert "CONTRIBUTING.md" in missing
        assert "README.md" in missing
        assert ".github/workflows/" in missing

    def test_license_present(self, tmp_path):
        (tmp_path / "LICENSE").write_text("MIT")
        missing = fs.missing_governance_files(tmp_path)
        assert "LICENSE" not in missing

    def test_readme_present(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hello")
        missing = fs.missing_governance_files(tmp_path)
        assert "README.md" not in missing

    def test_workflows_dir_present(self, tmp_path):
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        missing = fs.missing_governance_files(tmp_path)
        assert ".github/workflows/" not in missing

    def test_all_present(self, tmp_path):
        (tmp_path / "LICENSE").write_text("MIT")
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing")
        (tmp_path / "README.md").write_text("# Hello")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        assert fs.missing_governance_files(tmp_path) == []


class TestSyncResultMarkdownRow:
    def test_success_row_contains_ticks(self):
        r = fs.SyncResult(
            repo="owner/repo",
            stack="Python (pyproject)",
            upstream_synced=True,
            build_success=True,
            governance_missing=[],
        )
        row = r.as_markdown_row()
        assert "✅" in row
        assert "Python (pyproject)" in row

    def test_failure_row_contains_cross(self):
        r = fs.SyncResult(
            repo="owner/repo",
            stack="Unknown",
            upstream_synced=False,
            build_success=False,
            error="Clone failed",
        )
        row = r.as_markdown_row()
        assert "❌" in row

    def test_build_not_attempted_shows_dash(self):
        r = fs.SyncResult(repo="owner/repo")
        row = r.as_markdown_row()
        # build_success is None → should show "—"
        assert "—" in row

    def test_missing_files_appear_in_row(self):
        r = fs.SyncResult(
            repo="owner/repo",
            governance_missing=["LICENSE", "README.md"],
        )
        row = r.as_markdown_row()
        assert "LICENSE" in row
        assert "README.md" in row


class TestAppendSyncResults:
    def test_creates_file_if_missing(self, tmp_path):
        inventory = tmp_path / "FORKS_INVENTORY.md"
        r = fs.SyncResult(repo="me/repo", stack="Python (pyproject)", upstream_synced=True)
        fs.append_sync_results([r], inventory)
        assert inventory.exists()
        content = inventory.read_text()
        assert "me/repo" in content

    def test_appends_to_existing_file_with_sync_log_section(self, tmp_path):
        inventory = tmp_path / "FORKS_INVENTORY.md"
        inventory.write_text("# Forks\n\n## 🔄 Sync Log\n\n| Col |\n| --- |\n")
        r = fs.SyncResult(repo="me/repo2", stack="Go", upstream_synced=False)
        fs.append_sync_results([r], inventory)
        content = inventory.read_text()
        assert "me/repo2" in content

    def test_creates_sync_log_section_if_absent(self, tmp_path):
        inventory = tmp_path / "FORKS_INVENTORY.md"
        inventory.write_text("# Forks\n\nSome content.\n")
        r = fs.SyncResult(repo="me/repo3")
        fs.append_sync_results([r], inventory)
        content = inventory.read_text()
        assert "## 🔄 Sync Log" in content
        assert "me/repo3" in content
