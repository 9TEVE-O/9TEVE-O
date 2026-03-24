"""Tests for the suggest-upgrades feature."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import able_to_answer.suggest_upgrades.router as su_router_module
from able_to_answer.api.main import app
from able_to_answer.suggest_upgrades.analyzer import analyse
from able_to_answer.suggest_upgrades.models import Suggestion


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def api_client():
    """TestClient backed by the full FastAPI app."""
    yield TestClient(app)


def _mock_ops_client(
    *,
    manifest: str | None = None,
    default_branch: str = "main",
    base_sha: str = "abc123",
    pr_html_url: str = "https://github.com/org/repo/pull/1",
    has_token: bool = False,
) -> MagicMock:
    mock = MagicMock()
    mock.get_file_contents.return_value = manifest
    mock.get_default_branch_sha.return_value = (default_branch, base_sha)
    mock.create_branch.return_value = None
    mock.create_or_update_file.return_value = None
    mock.create_pull_request.return_value = pr_html_url
    mock.has_token = has_token
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — analyse()
# ─────────────────────────────────────────────────────────────────────────────

def test_analyse_all_returns_suggestions():
    results = analyse(repo="org/repo", focus="all")
    assert len(results) >= 1
    assert all(isinstance(s, Suggestion) for s in results)


def test_analyse_security_focus_includes_security():
    results = analyse(repo="org/repo", focus="security")
    titles = [s.title for s in results]
    assert any("SECURITY" in t or "security" in t.lower() or "SHA" in t for t in titles)


def test_analyse_performance_focus():
    results = analyse(repo="org/repo", focus="performance")
    assert len(results) >= 1


def test_analyse_testing_focus():
    results = analyse(repo="org/repo", focus="testing")
    assert len(results) >= 1


def test_analyse_unknown_focus_falls_back_to_all():
    results_unknown = analyse(repo="org/repo", focus="unicorn")
    results_all = analyse(repo="org/repo", focus="all")
    assert results_unknown == results_all


def test_analyse_returns_at_most_five():
    results = analyse(repo="org/repo", focus="all")
    assert len(results) <= 5


def test_analyse_skips_pytest_suggestion_when_already_configured():
    manifest = "[tool.pytest.ini_options]\ntestpaths = [\"tests\"]\n"
    results = analyse(repo="org/repo", focus="testing", manifest_content=manifest)
    titles = [s.title for s in results]
    assert not any("pytest configuration" in t.lower() for t in titles)


def test_analyse_repo_placeholder_interpolated():
    results = analyse(repo="example/my-repo", focus="security")
    for s in results:
        if s.code_snippet:
            assert "{repo}" not in s.code_snippet


def test_analyse_suggestion_fields_present():
    results = analyse(repo="org/repo", focus="all")
    for s in results:
        assert s.title
        assert s.description
        assert s.rationale


# ─────────────────────────────────────────────────────────────────────────────
# API integration tests — POST /v1/github/suggest-upgrades
# ─────────────────────────────────────────────────────────────────────────────

def test_suggest_upgrades_returns_suggestions(api_client, monkeypatch):
    monkeypatch.setattr(su_router_module, "gh_ops_client", _mock_ops_client())
    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "focus": "all", "auto_push": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"] == "org/repo"
    assert data["focus"] == "all"
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) >= 1
    assert data["pr_url"] is None


def test_suggest_upgrades_security_focus(api_client, monkeypatch):
    monkeypatch.setattr(su_router_module, "gh_ops_client", _mock_ops_client())
    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "focus": "security"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["focus"] == "security"
    assert len(data["suggestions"]) >= 1


def test_suggest_upgrades_default_focus_is_all(api_client, monkeypatch):
    monkeypatch.setattr(su_router_module, "gh_ops_client", _mock_ops_client())
    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo"},
    )
    assert resp.status_code == 200
    assert resp.json()["focus"] == "all"


def test_suggest_upgrades_invalid_repo_format(api_client):
    """repo must be in 'owner/repo' format."""
    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "no-slash-here"},
    )
    assert resp.status_code == 422


def test_suggest_upgrades_manifest_fetch_error_still_returns(api_client, monkeypatch):
    """A manifest-fetch error should not abort the request."""
    mock = _mock_ops_client()
    mock.get_file_contents.side_effect = RuntimeError("GitHub API error 403")
    monkeypatch.setattr(su_router_module, "gh_ops_client", mock)

    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["suggestions"]) >= 1


def test_suggest_upgrades_auto_push_creates_pr(api_client, monkeypatch):
    mock = _mock_ops_client(
        pr_html_url="https://github.com/org/repo/pull/42",
        has_token=True,
    )
    monkeypatch.setattr(su_router_module, "gh_ops_client", mock)

    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "auto_push": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pr_url"] == "https://github.com/org/repo/pull/42"
    mock.create_branch.assert_called_once()
    mock.create_pull_request.assert_called_once()


def test_suggest_upgrades_auto_push_without_token_returns_422(api_client, monkeypatch):
    monkeypatch.setattr(su_router_module, "gh_ops_client", _mock_ops_client(has_token=False))

    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "auto_push": True},
    )
    assert resp.status_code == 422
    assert "ATA_GITHUB_TOKEN" in resp.json()["detail"]


def test_suggest_upgrades_auto_push_github_api_error_returns_502(api_client, monkeypatch):
    mock = _mock_ops_client(has_token=True)
    mock.get_default_branch_sha.side_effect = RuntimeError("GitHub API error 500 Internal")
    monkeypatch.setattr(su_router_module, "gh_ops_client", mock)

    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "auto_push": True},
    )
    assert resp.status_code == 502
    assert "GitHub API error" in resp.json()["detail"]


def test_suggest_upgrades_suggestion_shape(api_client, monkeypatch):
    """Every returned suggestion must have title, description, and rationale."""
    monkeypatch.setattr(su_router_module, "gh_ops_client", _mock_ops_client())
    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo"},
    )
    assert resp.status_code == 200
    for s in resp.json()["suggestions"]:
        assert s["title"]
        assert s["description"]
        assert s["rationale"]


def test_suggest_upgrades_auto_push_commits_implementable_suggestions(api_client, monkeypatch):
    """Files with a file_path and code_snippet should be committed."""
    mock = _mock_ops_client(has_token=True)
    monkeypatch.setattr(su_router_module, "gh_ops_client", mock)

    resp = api_client.post(
        "/v1/github/suggest-upgrades",
        json={"repo": "org/repo", "focus": "all", "auto_push": True},
    )
    assert resp.status_code == 200
    # At least one create_or_update_file call should have been made because
    # the "all" focus set includes suggestions with file paths.
    assert mock.create_or_update_file.call_count >= 1
