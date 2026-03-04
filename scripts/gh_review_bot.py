#!/usr/bin/env python3
"""GitHub Review Automation Bot.

Processes ``pull_request``, ``pull_request_review``, and
``pull_request_review_comment`` events to automatically handle approval /
review tasks using policy guardrails.

Guardrail rules
---------------
* Draft PRs are acknowledged but **never** approved.
* PRs that touch ``SENSITIVE_PATHS`` are flagged for mandatory human review.
* PRs with failing or pending CI checks are not approved.
* PRs that touch **only** safe paths and have all CI checks passing are
  auto-approved with a standard LGTM comment.
* Everything else receives a general acknowledgment and is left for manual
  review.

Standard response messages
--------------------------
All user-facing strings use common GitHub collaboration language so that
automated responses feel natural alongside human reviewer activity.

Environment variables consumed
------------------------------
``GH_TOKEN``        GitHub token (required — set via ``secrets.GITHUB_TOKEN``)
``GH_REPO``         ``owner/repo`` string (required)
``EVENT_NAME``      GitHub event name (required)
``EVENT_ACTION``    GitHub event action (required)
``PR_NUMBER``       Pull-request number as string (required for PR events)
``PR_DRAFT``        "true" / "false" — whether PR is a draft (required for PR events)
``PR_HEAD_SHA``     Head commit SHA of the PR (required for PR events)
``REVIEW_BODY``     Body of an incoming review or comment (optional)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("gh_review_bot")
logging.basicConfig(level=logging.INFO, format="[review-bot] %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Guardrail configuration
# ---------------------------------------------------------------------------

# File paths / path prefixes that require mandatory human review.
SENSITIVE_PATHS: frozenset[str] = frozenset(
    {
        ".env",
        ".env.example",
        "pyproject.toml",
        "src/able_to_answer/core/config.py",
        "src/able_to_answer/control_plane/policy.py",
        ".github/workflows/",
        "Makefile",
    }
)

# File path prefixes that are always considered safe to auto-approve when
# they are the *only* files touched and CI passes.
SAFE_PATH_PREFIXES: tuple[str, ...] = (
    "docs/",
    "ADR/",
    "specs/",
    "tests/",
    "README",
    "CLAUDE.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".gitignore",
)

# ---------------------------------------------------------------------------
# Standard response messages — common GitHub collaboration language
# ---------------------------------------------------------------------------

MSG_DRAFT_ACK = (
    "👋 Thanks for opening this draft PR! "
    "I'll take a look once it's marked as **ready for review**."
)

MSG_SENSITIVE_FILES = (
    "🔒 This PR touches security-sensitive or policy-critical paths:\n\n"
    "{files}\n\n"
    "These changes require **manual human review** before merging. "
    "I've flagged this for the team."
)

MSG_CI_PENDING = (
    "⏳ CI checks are still in progress (or haven't been triggered yet). "
    "I'll defer my review until all checks complete. "
    "Please re-request a review once they pass."
)

MSG_CI_FAILING = (
    "❌ Some CI checks are not passing yet:\n\n"
    "{checks}\n\n"
    "Please fix the failing checks and re-request a review when they're green."
)

MSG_AUTO_APPROVE = (
    "✅ **LGTM!** This PR only touches safe paths and all CI checks pass. "
    "Auto-approving — no blocking concerns found.\n\n"
    "Merging is still subject to branch-protection rules."
)

MSG_GENERAL_ACK = (
    "👀 Thanks for the contribution! "
    "I've noted the changed files and will complete a full review shortly. "
    "Feel free to ping me here if you need anything in the meantime."
)

MSG_REVIEW_COMMENT_ACK = (
    "Thanks for the feedback! "
    "I'll address this in the next update. "
    "Let me know if you have any further questions. 🙏"
)

MSG_REVIEW_SUBMITTED_ACK = (
    "Thanks for the thorough review! "
    "I'll work through the feedback and push an updated revision accordingly."
)

# ---------------------------------------------------------------------------
# Pure guardrail functions (no I/O — fully unit-testable)
# ---------------------------------------------------------------------------


def classify_files(changed_files: list[str]) -> tuple[bool, list[str]]:
    """Return *(has_sensitive, sensitive_file_list)* for the given file list.

    A file is considered sensitive if its path equals or starts with any
    entry in ``SENSITIVE_PATHS``.

    Parameters
    ----------
    changed_files:
        List of file paths returned by the GitHub "List pull request files"
        endpoint (the ``filename`` field).

    Returns
    -------
    tuple[bool, list[str]]
        ``(True, [<matching paths>])`` when at least one sensitive path is
        matched; ``(False, [])`` otherwise.
    """
    hits: list[str] = []
    for path in changed_files:
        for sensitive in SENSITIVE_PATHS:
            if path == sensitive or path.startswith(sensitive):
                hits.append(path)
                break
    return bool(hits), hits


def all_safe_paths(changed_files: list[str]) -> bool:
    """Return ``True`` when *every* changed file is under a safe path prefix.

    An empty list is treated as safe (nothing changed → trivially safe).

    Parameters
    ----------
    changed_files:
        List of file paths from the pull-request diff.
    """
    if not changed_files:
        return True
    return all(
        any(path.startswith(prefix) for prefix in SAFE_PATH_PREFIXES)
        for path in changed_files
    )


def decide_action(
    is_draft: bool,
    changed_files: list[str],
    check_conclusions: list[str | None],
) -> str:
    """Apply guardrails and return a decision string.

    Decision values
    ---------------
    ``"acknowledge_draft"``
        PR is a draft — acknowledge only, do not approve.
    ``"flag_sensitive"``
        PR touches sensitive paths — require human review.
    ``"ci_pending"``
        At least one check is still queued / in-progress — defer.
    ``"ci_failing"``
        At least one check has failed — decline approval.
    ``"approve"``
        PR is safe-path-only and all checks passed — auto-approve.
    ``"acknowledge"``
        Fallback — acknowledge and leave for human review.

    Parameters
    ----------
    is_draft:
        Whether the pull request is currently a draft.
    changed_files:
        File paths changed by the PR.
    check_conclusions:
        List of conclusion strings from GitHub check-runs
        (e.g. ``"success"``, ``"failure"``, ``"neutral"``, ``None`` for
        in-progress checks).  May be empty when no checks are configured.
    """
    if is_draft:
        return "acknowledge_draft"

    has_sensitive, _ = classify_files(changed_files)
    if has_sensitive:
        return "flag_sensitive"

    # Map None (in-progress / queued) → "pending"
    normalised = [c if c is not None else "pending" for c in check_conclusions]

    pending = [c for c in normalised if c in {"pending", "queued", "in_progress"}]
    if pending:
        return "ci_pending"

    failing = [
        c
        for c in normalised
        if c in {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}
    ]
    if failing:
        return "ci_failing"

    if all_safe_paths(changed_files):
        return "approve"

    return "acknowledge"


# ---------------------------------------------------------------------------
# GitHub REST API client (I/O layer — not unit-tested directly)
# ---------------------------------------------------------------------------

_GH_API = "https://api.github.com"


class GitHubClient:
    """Minimal GitHub REST API client using only stdlib ``urllib``."""

    def __init__(self, token: str, repo: str) -> None:
        self._token = token
        self._repo = repo

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{_GH_API}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "gh-review-bot/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} {method} {path}: {body_text}"
            ) from exc

    def get_pr_files(self, pr_number: int) -> list[str]:
        """Return the list of filenames changed in *pr_number*."""
        data = self._request("GET", f"/repos/{self._repo}/pulls/{pr_number}/files")
        return [f["filename"] for f in data]

    def get_commit_check_runs(self, sha: str) -> list[dict[str, Any]]:
        """Return all check-run objects for the given commit SHA."""
        all_runs: list[dict[str, Any]] = []
        page = 1
        total_count: int | None = None

        while True:
            data = self._request(
                "GET",
                f"/repos/{self._repo}/commits/{sha}/check-runs?per_page=100&page={page}",
            )
            check_runs = data.get("check_runs", [])
            all_runs.extend(check_runs)

            if total_count is None:
                # GitHub returns the total number of check runs for this commit.
                total_count = data.get("total_count")

            # Stop if this page returned no results, or we've collected all known runs.
            if not check_runs:
                break
            if total_count is not None and len(all_runs) >= total_count:
                break

            page += 1

        return all_runs
    def post_comment(self, pr_number: int, body: str) -> None:
        """Post an issue comment on the pull request."""
        self._request(
            "POST",
            f"/repos/{self._repo}/issues/{pr_number}/comments",
            body={"body": body},
        )

    def submit_pr_review(
        self,
        pr_number: int,
        event: str,
        body: str,
    ) -> None:
        """Submit a pull-request review.

        Parameters
        ----------
        pr_number:
            Pull-request number.
        event:
            One of ``"APPROVE"``, ``"REQUEST_CHANGES"``, or ``"COMMENT"``.
        body:
            Review body text.
        """
        self._request(
            "POST",
            f"/repos/{self._repo}/pulls/{pr_number}/reviews",
            body={"event": event, "body": body},
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _env(name: str, required: bool = True) -> str:
    """Read an environment variable; raise clearly if required and missing."""
    value = os.environ.get(name, "")
    if required and not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set."
        )
    return value


def main() -> None:  # pragma: no cover — exercised end-to-end in CI
    """Read GitHub Actions environment variables and process the event."""
    token = _env("GH_TOKEN")
    repo = _env("GH_REPO")
    event_name = _env("EVENT_NAME")
    event_action = _env("EVENT_ACTION")

    client = GitHubClient(token=token, repo=repo)

    # ── pull_request_review_comment ──────────────────────────────────────
    if event_name == "pull_request_review_comment" and event_action == "created":
        pr_number_str = _env("PR_NUMBER")
        client.post_comment(int(pr_number_str), MSG_REVIEW_COMMENT_ACK)
        logger.info("Acknowledged review comment on PR #%s", pr_number_str)
        return

    # ── pull_request_review submitted ────────────────────────────────────
    if event_name == "pull_request_review" and event_action == "submitted":
        pr_number_str = _env("PR_NUMBER")
        client.post_comment(int(pr_number_str), MSG_REVIEW_SUBMITTED_ACK)
        logger.info("Acknowledged submitted review on PR #%s", pr_number_str)
        return

    # ── pull_request events ──────────────────────────────────────────────
    if event_name == "pull_request":
        pr_number = int(_env("PR_NUMBER"))
        is_draft = _env("PR_DRAFT", required=False).lower() == "true"
        head_sha = _env("PR_HEAD_SHA")

        changed_files = client.get_pr_files(pr_number)
        check_runs = client.get_commit_check_runs(head_sha)
        check_conclusions: list[str | None] = [
            cr.get("conclusion") for cr in check_runs
        ]

        action = decide_action(is_draft, changed_files, check_conclusions)

        if action == "acknowledge_draft":
            client.post_comment(pr_number, MSG_DRAFT_ACK)
            logger.info("Draft PR #%d — acknowledged only.", pr_number)

        elif action == "flag_sensitive":
            _, sensitive = classify_files(changed_files)
            bullet_list = "\n".join(f"- `{p}`" for p in sensitive)
            client.post_comment(
                pr_number,
                MSG_SENSITIVE_FILES.format(files=bullet_list),
            )
            logger.info("PR #%d — sensitive files flagged: %s", pr_number, sensitive)

        elif action == "ci_pending":
            client.post_comment(pr_number, MSG_CI_PENDING)
            logger.info("PR #%d — CI still pending.", pr_number)

        elif action == "ci_failing":
            failing = [
                cr["name"]
                for cr in check_runs
                if cr.get("conclusion") in {"failure", "timed_out", "cancelled"}
            ]
            bullet_list = "\n".join(f"- {name}" for name in failing)
            client.post_comment(
                pr_number,
                MSG_CI_FAILING.format(checks=bullet_list),
            )
            logger.info("PR #%d — CI failing: %s", pr_number, failing)

        elif action == "approve":
            client.submit_pr_review(pr_number, event="APPROVE", body=MSG_AUTO_APPROVE)
            logger.info("PR #%d — auto-approved.", pr_number)

        else:  # "acknowledge"
            client.post_comment(pr_number, MSG_GENERAL_ACK)
            logger.info("PR #%d — general acknowledgment posted.", pr_number)

        return

    logger.info(
        "No handler for event=%s action=%s; skipping.", event_name, event_action
    )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        logger.error("%s", exc)
        sys.exit(1)
