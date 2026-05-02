"""GitHub write-operations client for the suggest-upgrades feature.

Provides file-read, branch-creation, file-upsert and pull-request
creation — all the side-effects needed for ``auto_push`` mode.

All methods raise ``RuntimeError`` on a GitHub API error so callers
can map the exception to an appropriate HTTP response.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_GH_API = "https://api.github.com"
_USER_AGENT = "able-to-answer-suggest-upgrades/0.1"


class GitHubOpsClient:
    """Minimal GitHub API client for repository write operations."""

    def __init__(self, token: str | None = None) -> None:
        self._token = token

    @property
    def has_token(self) -> bool:
        """Return ``True`` when a GitHub token is available for write operations."""
        return bool(self._token)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": _USER_AGENT,
            "Content-Type": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        # ``path`` is always a hardcoded string literal passed by the methods
        # below (e.g. ``"/repos/{owner}/{repo}/contents/{file}"``).  It is never
        # derived from user-supplied input, so the resulting URL is safe to open.
        # User data flows only through ``params`` (URL-encoded) or ``body`` (JSON).
        url = f"{_GH_API}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"GitHub API error {exc.code} {method} {path}: {body_text}"
            ) from exc

    # ── Read operations ──────────────────────────────────────────────────────

    def get_file_contents(self, owner: str, repo: str, path: str) -> str | None:
        """Return the decoded text content of a file, or ``None`` if not found."""
        try:
            data = self._request("GET", f"/repos/{owner}/{repo}/contents/{path}")
        except RuntimeError as exc:
            if "404" in str(exc):
                return None
            raise
        if isinstance(data, dict) and "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return None

    def get_default_branch_sha(self, owner: str, repo: str) -> tuple[str, str]:
        """Return ``(branch_name, sha)`` for the default branch of the repository."""
        data = self._request("GET", f"/repos/{owner}/{repo}")
        branch = data["default_branch"]
        ref_data = self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        sha: str = ref_data["object"]["sha"]
        return branch, sha

    # ── Write operations ─────────────────────────────────────────────────────

    def create_branch(self, owner: str, repo: str, *, branch: str, sha: str) -> None:
        """Create a new branch pointing at the given commit SHA."""
        self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            body={"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        *,
        path: str,
        message: str,
        content: str,
        branch: str,
    ) -> None:
        """Create or update a single file on ``branch``.

        ``content`` is the *decoded* (plain text) content; this method handles
        the base-64 encoding required by the GitHub API.
        """
        encoded = base64.b64encode(content.encode()).decode()
        body: dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        # Fetch the current SHA if the file already exists so we can update it.
        try:
            existing = self._request(
                "GET",
                f"/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
            )
            if isinstance(existing, dict) and "sha" in existing:
                body["sha"] = existing["sha"]
        except RuntimeError:
            pass  # File does not exist yet — omit sha for a create.

        self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", body=body)

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        *,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> str:
        """Open a pull request and return its ``html_url``."""
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            body={"title": title, "body": body, "head": head, "base": base},
        )
        return str(data["html_url"])
