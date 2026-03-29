#!/usr/bin/env python3
"""Inventory and prioritize GitHub fork repositories.

Fetches all forked repositories for the authenticated GitHub user,
scores them by relevance, and writes a ranked inventory to
``FORKS_INVENTORY.md`` (Memory Bank).

Scoring criteria (0–10 per fork)
---------------------------------
* **Stars** (0–3 pts):  log-scaled star count of the upstream repo.
* **Recency** (0–2 pts): how recently the fork was pushed to (last 30 days
  scores 2, last 90 days 1, older 0).
* **Relevance** (0–3 pts): keywords in name / description matching skills
  (AI, agents, full-stack, etc.).
* **Upstream activity** (0–2 pts): whether the upstream was updated in the
  last 90 days (based on the fork's ``updated_at``).

Required environment variables
-------------------------------
``GH_TOKEN``    GitHub personal access token with ``repo`` or ``public_repo``
                scope; also accepts ``GITHUB_TOKEN``.

Optional environment variables
-------------------------------
``GH_USER``         GitHub username (defaults to the authenticated user).
``INVENTORY_PATH``  Output path (default: ``FORKS_INVENTORY.md``).
``TOP_N``           Number of top forks to highlight (default: ``8``).
"""
from __future__ import annotations

import json
import logging
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("fork_inventory")
logging.basicConfig(level=logging.INFO, format="[fork-inventory] %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_GH_API = "https://api.github.com"

# Skill-relevance keywords — matched case-insensitively against name/description.
_SKILL_KEYWORDS: tuple[str, ...] = (
    "ai",
    "agent",
    "llm",
    "rag",
    "gpt",
    "openai",
    "langchain",
    "ml",
    "nlp",
    "automation",
    "fastapi",
    "full-stack",
    "fullstack",
    "react",
    "nextjs",
    "typescript",
    "security",
    "owasp",
    "copilot",
    "workflow",
    "scraper",
    "spider",
    "crawler",
    "vector",
    "embedding",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ForkInfo:
    """Represents a single fork with its scoring metadata."""

    name_with_owner: str
    name: str
    description: str
    language: str
    stars: int
    forks_count: int
    pushed_at: str  # ISO-8601 string
    updated_at: str  # ISO-8601 string
    html_url: str
    parent_full_name: str
    parent_html_url: str
    score: float = field(default=0.0)
    score_breakdown: dict[str, float] = field(default_factory=dict)

    def matched_keywords(self) -> list[str]:
        """Return skill keywords found in the repo name or description."""
        haystack = f"{self.name} {self.description}".lower()
        return [kw for kw in _SKILL_KEYWORDS if kw in haystack]


# ---------------------------------------------------------------------------
# Pure scoring helpers (fully unit-testable)
# ---------------------------------------------------------------------------


def score_stars(star_count: int) -> float:
    """Return a 0–3 score based on log-scaled star count.

    >>> score_stars(0)
    0.0
    >>> score_stars(1000) >= 2.5
    True
    """
    if star_count <= 0:
        return 0.0
    # log10(1000) ≈ 3 → capped at 3.0
    return min(3.0, math.log10(star_count + 1))


def score_recency(pushed_at_iso: str, now: datetime | None = None) -> float:
    """Return a 0–2 score based on how recently *pushed_at_iso* was.

    * ≤ 30 days ago → 2.0
    * ≤ 90 days ago → 1.0
    * > 90 days ago → 0.0

    Parameters
    ----------
    pushed_at_iso:
        ISO-8601 timestamp string (UTC), e.g. ``"2024-01-15T12:34:56Z"``.
    now:
        Override the current time (for testing).
    """
    if not pushed_at_iso:
        return 0.0
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        pushed = datetime.fromisoformat(pushed_at_iso.replace("Z", "+00:00"))
        delta_days = (now - pushed).days
    except ValueError:
        return 0.0
    if delta_days <= 30:
        return 2.0
    if delta_days <= 90:
        return 1.0
    return 0.0


def score_relevance(name: str, description: str) -> float:
    """Return a 0–3 score based on matched skill keywords.

    Each unique keyword match adds 1.0, capped at 3.0.

    Parameters
    ----------
    name:
        Repository name (without the owner prefix).
    description:
        Repository description string (may be empty).
    """
    haystack = f"{name} {description}".lower()
    hits = sum(1 for kw in _SKILL_KEYWORDS if kw in haystack)
    return min(3.0, float(hits))


def score_upstream_activity(updated_at_iso: str, now: datetime | None = None) -> float:
    """Return a 0–2 score if the fork was updated within the last 90 days.

    This is a proxy for upstream activity — forks that are still receiving
    pushes (from upstream syncs or personal work) are more valuable.
    """
    return 2.0 if score_recency(updated_at_iso, now=now) > 0 else 0.0


def compute_score(fork: ForkInfo, now: datetime | None = None) -> tuple[float, dict[str, float]]:
    """Compute the aggregate 0–10 score for a fork.

    Returns
    -------
    tuple[float, dict[str, float]]
        ``(total_score, breakdown_dict)``
    """
    s_stars = score_stars(fork.stars)
    s_recency = score_recency(fork.pushed_at, now=now)
    s_relevance = score_relevance(fork.name, fork.description)
    s_upstream = score_upstream_activity(fork.updated_at, now=now)

    breakdown = {
        "stars": s_stars,
        "recency": s_recency,
        "relevance": s_relevance,
        "upstream_activity": s_upstream,
    }
    total = s_stars + s_recency + s_relevance + s_upstream
    return total, breakdown


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _gh_get(path: str, token: str) -> Any:
    """Perform a single GET request against the GitHub REST API."""
    url = f"{_GH_API}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "fork-inventory/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} GET {path}: {body_text}") from exc


def fetch_forks(token: str, username: str | None = None) -> list[dict[str, Any]]:
    """Return all fork repos for *username* (defaults to the token owner).

    Handles pagination automatically.
    """
    if username:
        base = f"/users/{username}/repos"
    else:
        base = "/user/repos"

    results: list[dict[str, Any]] = []
    page = 1
    while True:
        data = _gh_get(f"{base}?type=forks&per_page=100&page={page}", token)
        if not data:
            break
        for repo in data:
            if repo.get("fork"):
                results.append(repo)
        if len(data) < 100:
            break
        page += 1

    logger.info("Fetched %d forks from GitHub.", len(results))
    return results


def parse_fork(raw: dict[str, Any]) -> ForkInfo:
    """Parse a raw GitHub API repository object into a :class:`ForkInfo`."""
    parent = raw.get("parent") or {}
    return ForkInfo(
        name_with_owner=raw.get("full_name", ""),
        name=raw.get("name", ""),
        description=raw.get("description") or "",
        language=raw.get("language") or "Unknown",
        stars=raw.get("stargazers_count", 0),
        forks_count=raw.get("forks_count", 0),
        pushed_at=raw.get("pushed_at") or "",
        updated_at=raw.get("updated_at") or "",
        html_url=raw.get("html_url", ""),
        parent_full_name=parent.get("full_name", ""),
        parent_html_url=parent.get("html_url", ""),
    )


# ---------------------------------------------------------------------------
# Markdown report builder
# ---------------------------------------------------------------------------

_RANK_EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}


def _fmt_score(score: float) -> str:
    return f"{score:.1f}/10"


def build_inventory_markdown(forks: list[ForkInfo], top_n: int) -> str:
    """Build the full FORKS_INVENTORY.md content.

    Parameters
    ----------
    forks:
        All forks, already sorted descending by ``score``.
    top_n:
        Number of forks highlighted in the **Priority Batch** table.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    lines += [
        "# 🍴 Fork Inventory — Memory Bank",
        "",
        f"> Auto-generated {now_str} by `scripts/fork_inventory.py`.",
        f"> Total forks: **{len(forks)}** · Top batch for deep work: **{top_n}**",
        "",
        "---",
        "",
        f"## 🏆 Priority Batch — Top {top_n} Forks",
        "",
        "| Rank | Repository | Lang | ⭐ Stars | Score | Keywords |",
        "| ---- | ---------- | ---- | ------- | ----- | -------- |",
    ]

    for i, fork in enumerate(forks[:top_n], start=1):
        medal = _RANK_EMOJI.get(i, f"#{i}")
        kws = ", ".join(fork.matched_keywords()) or "—"
        repo_link = f"[{fork.name_with_owner}]({fork.html_url})"
        lines.append(
            f"| {medal} | {repo_link} | {fork.language} | {fork.stars:,} | {_fmt_score(fork.score)} | {kws} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 📋 Full Inventory",
        "",
        "| # | Repository | Lang | ⭐ Stars | Last Push | Score | Parent |",
        "| - | ---------- | ---- | ------- | --------- | ----- | ------ |",
    ]

    for i, fork in enumerate(forks, start=1):
        pushed = fork.pushed_at[:10] if fork.pushed_at else "—"
        repo_link = f"[{fork.name_with_owner}]({fork.html_url})"
        parent_link = f"[{fork.parent_full_name}]({fork.parent_html_url})" if fork.parent_full_name else "—"
        lines.append(
            f"| {i} | {repo_link} | {fork.language} | {fork.stars:,} | {pushed} | {_fmt_score(fork.score)} | {parent_link} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 📊 Score Breakdown (Top Batch)",
        "",
        "| Repository | Stars (0–3) | Recency (0–2) | Relevance (0–3) | Upstream (0–2) | **Total** |",
        "| ---------- | ----------- | ------------- | --------------- | -------------- | --------- |",
    ]

    for fork in forks[:top_n]:
        bd = fork.score_breakdown
        lines.append(
            f"| [{fork.name}]({fork.html_url}) "
            f"| {bd.get('stars', 0):.1f} "
            f"| {bd.get('recency', 0):.1f} "
            f"| {bd.get('relevance', 0):.1f} "
            f"| {bd.get('upstream_activity', 0):.1f} "
            f"| **{_fmt_score(fork.score)}** |"
        )

    lines += [
        "",
        "---",
        "",
        "## 🔧 Recommended Actions",
        "",
        "For the priority batch above, run `scripts/fork_sync.py <owner/repo>` to:",
        "",
        "1. Sync with upstream (`git pull upstream main`)",
        "2. Detect language / tech stack",
        "3. Attempt build + tests",
        "4. Audit README, CI, and LICENSE",
        "5. Commit improvements and open a PR",
        "",
        "```bash",
        "# Example — sync a single fork",
        "GH_TOKEN=$GITHUB_TOKEN python scripts/fork_sync.py 9TEVE-O/some-fork",
        "```",
        "",
        "---",
        "",
        "_Generated by [fork_inventory.py](scripts/fork_inventory.py) · "
        "Part of the 9TEVE-O/9TEVE-O Memory Bank_",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("GH_TOKEN (or GITHUB_TOKEN) environment variable is required.")
        sys.exit(1)

    username = os.environ.get("GH_USER", "")
    top_n = int(os.environ.get("TOP_N", "8"))
    inventory_path = os.environ.get("INVENTORY_PATH", "FORKS_INVENTORY.md")

    logger.info("Fetching forks for %s …", username or "authenticated user")
    raw_forks = fetch_forks(token, username or None)

    now = datetime.now(timezone.utc)
    forks: list[ForkInfo] = []
    for raw in raw_forks:
        fork = parse_fork(raw)
        total, breakdown = compute_score(fork, now=now)
        fork.score = total
        fork.score_breakdown = breakdown
        forks.append(fork)

    forks.sort(key=lambda f: f.score, reverse=True)

    markdown = build_inventory_markdown(forks, top_n)

    with open(inventory_path, "w", encoding="utf-8") as fh:
        fh.write(markdown)

    logger.info("Wrote inventory to %s (%d forks, top %d highlighted).", inventory_path, len(forks), top_n)

    # Print summary to stdout so CI logs are informative.
    print(f"\n{'='*60}")
    print(f"FORK INVENTORY SUMMARY  ({now.strftime('%Y-%m-%d')})")
    print(f"{'='*60}")
    print(f"Total forks found : {len(forks)}")
    print(f"Top {top_n} forks:")
    for i, fork in enumerate(forks[:top_n], start=1):
        print(f"  {i:2}. {fork.name_with_owner:<40} score={_fmt_score(fork.score)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
