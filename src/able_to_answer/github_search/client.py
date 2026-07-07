"""GitHub Search API client for skill-repository discovery."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_GH_API = "https://api.github.com"
_USER_AGENT = "able-to-answer-skill-search/0.1"

# Topics and keywords used to score Manus-app skill alignment.
_MANUS_TOPICS: frozenset[str] = frozenset({"manus", "manus-skill", "manus-app"})
_SKILL_TOPICS: frozenset[str] = frozenset({"skill", "agent-skill", "ai-skill", "llm-skill"})
_AGENT_TOPICS: frozenset[str] = frozenset({"ai-agent", "autonomous-agent", "langchain", "autogpt"})
_HIGH_KEYWORDS: frozenset[str] = frozenset({"manus"})
_MEDIUM_KEYWORDS: frozenset[str] = frozenset({"skill", "tool", "agent", "capability"})


class GitHubSearchClient:
    """Minimal GitHub Search API client using stdlib ``urllib``."""

    def __init__(self, token: str | None = None) -> None:
        self._token = token

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": _USER_AGENT,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        # path is always a hardcoded internal constant (e.g. "/search/repositories");
        # user input flows only through params which are safely URL-encoded below.
        url = f"{_GH_API}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} GET {path}: {body_text}"
            ) from exc

    def search_repositories(
        self,
        query: str,
        language: str | None = None,
        topics: list[str] | None = None,
        per_page: int = 10,
    ) -> dict[str, Any]:
        """Search GitHub repositories via the Search API.

        Parameters
        ----------
        query:
            Free-text search terms, e.g. ``"manus skill"``.
        language:
            Optional programming-language filter, e.g. ``"python"``.
        topics:
            Optional list of GitHub topic filters, e.g. ``["manus", "skill"]``.
        per_page:
            Number of results to return (1–30).

        Returns
        -------
        dict
            Raw GitHub ``/search/repositories`` response payload.
        """
        q = query
        if language:
            q = f"{q} language:{language}"
        if topics:
            for topic in topics:
                q = f"{q} topic:{topic}"
        params: dict[str, Any] = {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": max(1, min(per_page, 30)),
        }
        return self._get("/search/repositories", params=params)


def score_skill_alignment(repo: dict[str, Any]) -> str:
    """Score a repository's skill alignment for Manus app integration.

    Returns one of ``"high"``, ``"medium"``, or ``"low"``.

    Scoring rules
    -------------
    * **high** — repo has a Manus-specific topic (``manus``, ``manus-skill``,
      ``manus-app``) **or** the word ``"manus"`` appears in its name or
      description.
    * **medium** — repo has a generic skill/agent topic (``skill``,
      ``agent-skill``, ``ai-agent``, etc.) **or** skill-related keywords
      (``skill``, ``tool``, ``agent``, ``capability``) appear in name /
      description.
    * **low** — neither condition above is met.
    """
    topics: set[str] = set(repo.get("topics") or [])
    description: str = (repo.get("description") or "").lower()
    name: str = (repo.get("name") or "").lower()

    if _MANUS_TOPICS & topics:
        return "high"
    if any(kw in description or kw in name for kw in _HIGH_KEYWORDS):
        return "high"

    if (_SKILL_TOPICS | _AGENT_TOPICS) & topics:
        return "medium"
    if any(kw in description or kw in name for kw in _MEDIUM_KEYWORDS):
        return "medium"

    return "low"
