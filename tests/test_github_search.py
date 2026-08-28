"""Tests for the GitHub skill-search feature."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import able_to_answer.github_search.router as gh_router_module
from able_to_answer.api.main import app
from able_to_answer.github_search.client import score_skill_alignment
from able_to_answer.github_search.router import _parse_topic_list

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

@pytest.fixture()
def api_client():
    """Test client for the GitHub skill-search routes."""
    yield TestClient(app)


def _mock_gh_client(items=None, total_count=0):
    """Return a mock GitHubSearchClient with canned search results."""
    mock = MagicMock()
    mock.search_repositories.return_value = {
        "total_count": total_count,
        "items": items or [],
    }
    return mock


def _make_repo(
    *,
    id: int = 1,
    full_name: str = "org/repo",
    description: str | None = None,
    html_url: str = "https://github.com/org/repo",
    stars: int = 0,
    language: str | None = None,
    topics: list[str] | None = None,
) -> dict:
    return {
        "id": id,
        "full_name": full_name,
        "name": full_name.split("/")[-1],
        "description": description,
        "html_url": html_url,
        "stargazers_count": stars,
        "language": language,
        "topics": topics or [],
    }


# ────────────────────────────────────────────────────────────
# Unit tests — score_skill_alignment
# ────────────────────────────────────────────────────────────

def test_alignment_high_manus_topic():
    repo = _make_repo(topics=["manus"])
    assert score_skill_alignment(repo) == "high"


def test_alignment_high_manus_skill_topic():
    repo = _make_repo(topics=["manus-skill"])
    assert score_skill_alignment(repo) == "high"


def test_alignment_high_manus_in_description():
    repo = _make_repo(description="A collection of Manus app skills")
    assert score_skill_alignment(repo) == "high"


def test_alignment_high_manus_in_name():
    repo = _make_repo(full_name="example/manus-tools")
    assert score_skill_alignment(repo) == "high"


def test_alignment_medium_skill_topic():
    repo = _make_repo(topics=["skill"])
    assert score_skill_alignment(repo) == "medium"


def test_alignment_medium_ai_agent_topic():
    repo = _make_repo(topics=["ai-agent"])
    assert score_skill_alignment(repo) == "medium"


def test_alignment_medium_skill_keyword_in_description():
    repo = _make_repo(description="A library of reusable agent tools and capabilities")
    assert score_skill_alignment(repo) == "medium"


def test_alignment_low_unrelated_repo():
    repo = _make_repo(description="A fast HTTP server", topics=["web", "server"])
    assert score_skill_alignment(repo) == "low"


def test_alignment_low_no_description_no_topics():
    repo = _make_repo()
    assert score_skill_alignment(repo) == "low"


def test_alignment_manus_topic_beats_generic_skill_topic():
    """manus topic → high, not just medium."""
    repo = _make_repo(topics=["manus", "skill"])
    assert score_skill_alignment(repo) == "high"


# ────────────────────────────────────────────────────────────
# Unit tests — _parse_topic_list
# ────────────────────────────────────────────────────────────

def test_parse_topic_list_none_returns_none():
    assert _parse_topic_list(None) is None


def test_parse_topic_list_empty_string_returns_none():
    assert _parse_topic_list("") is None


def test_parse_topic_list_single_topic():
    assert _parse_topic_list("manus") == ["manus"]


def test_parse_topic_list_multiple_topics():
    assert _parse_topic_list("manus,skill,agent") == ["manus", "skill", "agent"]


def test_parse_topic_list_strips_whitespace():
    assert _parse_topic_list("manus , skill , agent") == ["manus", "skill", "agent"]


def test_parse_topic_list_ignores_blank_segments():
    assert _parse_topic_list("manus,,skill") == ["manus", "skill"]


# ────────────────────────────────────────────────────────────
# API integration tests — GET /v1/github/skills/search
# ────────────────────────────────────────────────────────────

def test_search_skills_empty_results(api_client, monkeypatch):
    monkeypatch.setattr(gh_router_module, "gh_client", _mock_gh_client())
    resp = api_client.get("/v1/github/skills/search?query=manus+skills")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "manus skills"
    assert data["total_count"] == 0
    assert data["repositories"] == []


def test_search_skills_returns_repos(api_client, monkeypatch):
    items = [
        _make_repo(
            id=42,
            full_name="example/manus-skills",
            description="Manus app skill collection",
            html_url="https://github.com/example/manus-skills",
            stars=100,
            language="Python",
            topics=["manus", "skill"],
        )
    ]
    monkeypatch.setattr(gh_router_module, "gh_client", _mock_gh_client(items=items, total_count=1))

    resp = api_client.get("/v1/github/skills/search?query=manus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 1
    assert len(data["repositories"]) == 1
    repo = data["repositories"][0]
    assert repo["id"] == 42
    assert repo["full_name"] == "example/manus-skills"
    assert repo["description"] == "Manus app skill collection"
    assert repo["html_url"] == "https://github.com/example/manus-skills"
    assert repo["stars"] == 100
    assert repo["language"] == "Python"
    assert "manus" in repo["topics"]
    assert repo["skill_alignment"] == "high"


def test_search_skills_alignment_scores_in_response(api_client, monkeypatch):
    """Multiple repos are scored independently."""
    items = [
        _make_repo(id=1, full_name="org/manus-tools", topics=["manus"]),
        _make_repo(id=2, full_name="org/ai-skills", topics=["skill"]),
        _make_repo(id=3, full_name="org/web-framework", description="Fast web server"),
    ]
    monkeypatch.setattr(
        gh_router_module, "gh_client", _mock_gh_client(items=items, total_count=3)
    )

    resp = api_client.get("/v1/github/skills/search?query=skills")
    assert resp.status_code == 200
    repos = resp.json()["repositories"]
    assert repos[0]["skill_alignment"] == "high"
    assert repos[1]["skill_alignment"] == "medium"
    assert repos[2]["skill_alignment"] == "low"


def test_search_skills_with_language_filter(api_client, monkeypatch):
    mock = _mock_gh_client()
    monkeypatch.setattr(gh_router_module, "gh_client", mock)

    resp = api_client.get("/v1/github/skills/search?query=manus+skill&language=python")
    assert resp.status_code == 200
    mock.search_repositories.assert_called_once_with(
        query="manus skill",
        language="python",
        topics=None,
        per_page=10,
    )


def test_search_skills_with_topics_filter(api_client, monkeypatch):
    mock = _mock_gh_client()
    monkeypatch.setattr(gh_router_module, "gh_client", mock)

    resp = api_client.get("/v1/github/skills/search?query=agent&topics=manus,skill")
    assert resp.status_code == 200
    mock.search_repositories.assert_called_once_with(
        query="agent",
        language=None,
        topics=["manus", "skill"],
        per_page=10,
    )


def test_search_skills_with_per_page(api_client, monkeypatch):
    mock = _mock_gh_client()
    monkeypatch.setattr(gh_router_module, "gh_client", mock)

    resp = api_client.get("/v1/github/skills/search?query=manus&per_page=5")
    assert resp.status_code == 200
    mock.search_repositories.assert_called_once_with(
        query="manus",
        language=None,
        topics=None,
        per_page=5,
    )


def test_search_skills_missing_query(api_client):
    """query is required — missing it returns 422."""
    resp = api_client.get("/v1/github/skills/search")
    assert resp.status_code == 422


def test_search_skills_per_page_out_of_range(api_client):
    """per_page must be 1–30."""
    resp = api_client.get("/v1/github/skills/search?query=manus&per_page=100")
    assert resp.status_code == 422


def test_search_skills_github_api_error(api_client, monkeypatch):
    """GitHub API errors surface as HTTP 502."""
    mock = MagicMock()
    mock.search_repositories.side_effect = RuntimeError("GitHub API error 403 rate limited")
    monkeypatch.setattr(gh_router_module, "gh_client", mock)

    resp = api_client.get("/v1/github/skills/search?query=manus")
    assert resp.status_code == 502
    assert "GitHub API error" in resp.json()["detail"]


def test_search_skills_null_description_and_topics(api_client, monkeypatch):
    """Repos with null description and empty topics list are handled safely."""
    items = [_make_repo(id=10, description=None, topics=[])]
    monkeypatch.setattr(
        gh_router_module, "gh_client", _mock_gh_client(items=items, total_count=1)
    )

    resp = api_client.get("/v1/github/skills/search?query=test")
    assert resp.status_code == 200
    repo = resp.json()["repositories"][0]
    assert repo["description"] is None
    assert repo["topics"] == []
    assert repo["skill_alignment"] == "low"
