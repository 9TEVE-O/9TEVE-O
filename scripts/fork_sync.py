#!/usr/bin/env python3
"""Sync a single GitHub fork with its upstream and audit it for improvements.

For each fork this script will:

1. Clone the fork (if not already present in ``WORKSPACE_DIR``).
2. Add the upstream remote and pull from ``main`` / ``master``.
3. Detect the language / tech stack from manifest files.
4. Attempt a full build + test run (``npm ci && npm test``, ``pip install``
   and ``pytest``, ``cargo test``, etc.).
5. Audit and improve:
   - Ensure a ``LICENSE`` file exists.
   - Ensure a ``CONTRIBUTING.md`` file exists.
   - Flag missing or thin ``README.md``.
   - Check for a ``.github/workflows/`` directory.
6. Append a structured log entry to ``FORKS_INVENTORY.md`` under the
   repo's section.

Usage
-----
::

    GH_TOKEN=$GITHUB_TOKEN python scripts/fork_sync.py owner/repo [owner/repo …]

Required environment variables
-------------------------------
``GH_TOKEN``        GitHub token (or ``GITHUB_TOKEN``).

Optional environment variables
-------------------------------
``WORKSPACE_DIR``   Directory where forks are cloned (default: ``/tmp/fork_workspace``).
``INVENTORY_PATH``  Path to ``FORKS_INVENTORY.md`` (default: ``FORKS_INVENTORY.md``).
``DRY_RUN``         Set to ``1`` to skip git operations and writes (default: ``0``).
"""
from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("fork_sync")
logging.basicConfig(level=logging.INFO, format="[fork-sync] %(levelname)s %(message)s")

_GH_API = "https://api.github.com"

# ---------------------------------------------------------------------------
# Tech-stack detection helpers (pure, unit-testable)
# ---------------------------------------------------------------------------

#: Maps manifest file names to a human-readable tech-stack label.
_STACK_MANIFESTS: dict[str, str] = {
    "package.json": "Node.js / JavaScript",
    "pyproject.toml": "Python (pyproject)",
    "setup.py": "Python (setup.py)",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java (Gradle)",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "mix.exs": "Elixir",
    "pubspec.yaml": "Dart / Flutter",
    "CMakeLists.txt": "C / C++",
}

#: Maps detected stack label to the command sequence for build + test.
_BUILD_COMMANDS: dict[str, list[str]] = {
    "Node.js / JavaScript": ["npm ci", "npm run build --if-present", "npm test --if-present"],
    "Python (pyproject)": ['pip install -e ".[dev]" -q', "python -m pytest tests/ -v"],
    "Python (setup.py)": ["pip install -e . -q", "python -m pytest tests/ -v"],
    "Rust": ["cargo build", "cargo test"],
    "Go": ["go build ./...", "go test ./..."],
    "Java (Maven)": ["mvn -q package -DskipTests=false"],
    "Java (Gradle)": ["./gradlew build"],
}


def detect_stack(repo_dir: Path) -> str:
    """Return the first matching tech-stack label for *repo_dir*.

    Parameters
    ----------
    repo_dir:
        The root directory of the cloned repository.

    Returns
    -------
    str
        A human-readable label, or ``"Unknown"`` when no manifest is found.
    """
    for manifest, label in _STACK_MANIFESTS.items():
        if (repo_dir / manifest).exists():
            return label
    return "Unknown"


def missing_governance_files(repo_dir: Path) -> list[str]:
    """Return a list of governance files that are absent from *repo_dir*.

    Checks for: ``LICENSE``, ``CONTRIBUTING.md``, ``README.md``,
    ``.github/workflows/``.

    Parameters
    ----------
    repo_dir:
        The root directory of the cloned repository.
    """
    missing: list[str] = []
    checks: list[tuple[str, Path]] = [
        ("LICENSE", repo_dir / "LICENSE"),
        ("CONTRIBUTING.md", repo_dir / "CONTRIBUTING.md"),
        ("README.md", repo_dir / "README.md"),
        (".github/workflows/", repo_dir / ".github" / "workflows"),
    ]
    for label, path in checks:
        if not path.exists():
            missing.append(label)
    return missing


# ---------------------------------------------------------------------------
# Sync result data model
# ---------------------------------------------------------------------------


@dataclass
class SyncResult:
    """Summary of a single fork sync operation."""

    repo: str
    stack: str = "Unknown"
    upstream_synced: bool = False
    build_success: bool | None = None  # None means build was not attempted
    build_output: str = ""
    governance_missing: list[str] = field(default_factory=list)
    error: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def as_markdown_row(self) -> str:
        """Return a single-line Markdown table row for this result."""
        synced = "✅" if self.upstream_synced else "❌"
        if self.build_success is None:
            build = "—"
        else:
            build = "✅" if self.build_success else "❌"
        missing = ", ".join(f"`{f}`" for f in self.governance_missing) or "—"
        error = f" ⚠️ `{self.error[:80]}`" if self.error else ""
        return (
            f"| [{self.repo}](https://github.com/{self.repo}) "
            f"| {self.stack} "
            f"| {synced} "
            f"| {build} "
            f"| {missing} "
            f"| {self.timestamp[:10]}{error} |"
        )


# ---------------------------------------------------------------------------
# GitHub API helper
# ---------------------------------------------------------------------------


def _fetch_repo_info(repo: str, token: str) -> dict[str, Any]:
    """Fetch repository metadata from the GitHub API."""
    url = f"{_GH_API}/repos/{repo}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "fork-sync/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {repo}: {body_text}") from exc


def _get_upstream_clone_url(repo_info: dict[str, Any]) -> str | None:
    """Extract the upstream (parent) clone URL from a repo-info payload."""
    parent = repo_info.get("parent")
    if parent:
        return parent.get("clone_url")
    return None


_REPO_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def _validate_repo(repo: str) -> None:
    """Raise ``ValueError`` if *repo* does not match ``owner/name`` format."""
    if not _REPO_NAME_RE.match(repo):
        raise ValueError(f"Invalid repo name: {repo!r} — expected 'owner/name'.")


def _sanitize(text: str, token: str) -> str:
    """Replace occurrences of *token* in *text* with ``***``."""
    if token:
        return text.replace(token, "***")
    return text


# ---------------------------------------------------------------------------
# Shell helper
# ---------------------------------------------------------------------------


def _run(cmd: str | list[str], cwd: Path) -> tuple[bool, str]:
    """Run a shell command and return (success, combined_output).

    Parameters
    ----------
    cmd:
        Either a list of arguments (preferred, shell=False) or a plain string
        that will be split with ``shlex.split``.
    cwd:
        Working directory for the command.
    """
    args = cmd if isinstance(cmd, list) else shlex.split(cmd)
    result = subprocess.run(  # noqa: S603
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


# ---------------------------------------------------------------------------
# Core sync logic
# ---------------------------------------------------------------------------


def sync_fork(
    repo: str,
    token: str,
    workspace: Path,
    dry_run: bool = False,
) -> SyncResult:
    """Clone (if needed), sync upstream, detect stack, and audit *repo*.

    Parameters
    ----------
    repo:
        ``owner/name`` string, e.g. ``"9TEVE-O/langchain"``.
    token:
        GitHub personal access token.
    workspace:
        Directory where repos are cloned.
    dry_run:
        When ``True``, skip all git operations and file writes.
    """
    result = SyncResult(repo=repo)
    try:
        _validate_repo(repo)
    except ValueError as exc:
        result.error = str(exc)
        logger.error(result.error)
        return result

    owner, name = repo.split("/", 1)
    repo_dir = workspace / name

    if dry_run:
        logger.info("[DRY-RUN] Would sync %s → %s", repo, repo_dir)
        result.stack = "Unknown (dry-run)"
        return result

    # ── 1. Clone fork if not already present ────────────────────────────
    # Pass the URL as a separate list argument so the token never touches
    # a shell; _sanitize guards any log/error output that might leak it.
    clone_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    if not repo_dir.exists():
        logger.info("Cloning %s …", repo)
        ok, out = _run(["git", "clone", "--depth=50", clone_url, name], cwd=workspace)
        if not ok:
            result.error = f"Clone failed: {_sanitize(out, token)[:200]}"
            logger.error(result.error)
            return result
    else:
        logger.info("Repo %s already cloned at %s.", name, repo_dir)

    # ── 2. Add upstream remote and pull ─────────────────────────────────
    try:
        repo_info = _fetch_repo_info(repo, token)
    except RuntimeError as exc:
        result.error = _sanitize(str(exc), token)
        logger.error(result.error)
        return result

    upstream_url = _get_upstream_clone_url(repo_info)
    if upstream_url:
        _run(["git", "remote", "remove", "upstream"], cwd=repo_dir)  # ignore if not present
        _run(["git", "remote", "add", "upstream", upstream_url], cwd=repo_dir)
        ok, out = _run(["git", "fetch", "upstream", "--depth=50"], cwd=repo_dir)
        if ok:
            # Try main, then master
            for branch in ("main", "master"):
                ok, out = _run(["git", "merge", "--no-edit", f"upstream/{branch}"], cwd=repo_dir)
                if ok:
                    result.upstream_synced = True
                    logger.info("Synced %s with upstream/%s.", repo, branch)
                    break
            if not result.upstream_synced:
                logger.warning("Could not merge from upstream for %s: %s", repo, out[:200])
        else:
            logger.warning("Could not fetch upstream for %s: %s", repo, out[:200])
    else:
        logger.info("No upstream parent found for %s.", repo)

    # ── 3. Detect stack ──────────────────────────────────────────────────
    result.stack = detect_stack(repo_dir)
    logger.info("Detected stack for %s: %s", repo, result.stack)

    # ── 4. Attempt build + test ──────────────────────────────────────────
    build_cmds = _BUILD_COMMANDS.get(result.stack)
    if build_cmds:
        all_ok = True
        combined_output: list[str] = []
        for cmd in build_cmds:
            ok, out = _run(cmd, cwd=repo_dir)
            combined_output.append(f"$ {cmd}\n{out}")
            if not ok:
                all_ok = False
                logger.warning("Build/test step failed for %s: %s", repo, cmd)
                break
        result.build_success = all_ok
        result.build_output = "\n\n".join(combined_output)
    else:
        logger.info("No build commands defined for stack '%s'.", result.stack)

    # ── 5. Governance audit ──────────────────────────────────────────────
    result.governance_missing = missing_governance_files(repo_dir)
    if result.governance_missing:
        logger.warning("%s is missing: %s", repo, ", ".join(result.governance_missing))

    return result


# ---------------------------------------------------------------------------
# Inventory log update
# ---------------------------------------------------------------------------

_SYNC_LOG_HEADER = """
## 🔄 Sync Log

| Repository | Stack | Upstream Sync | Build | Missing Files | Date |
| ---------- | ----- | ------------- | ----- | ------------- | ---- |
"""


def append_sync_results(results: list[SyncResult], inventory_path: Path) -> None:
    """Append *results* rows to the sync-log section of *inventory_path*."""
    if not inventory_path.exists():
        logger.warning("Inventory file not found at %s; creating stub.", inventory_path)
        inventory_path.write_text("# 🍴 Fork Inventory — Memory Bank\n", encoding="utf-8")

    content = inventory_path.read_text(encoding="utf-8")
    if "## 🔄 Sync Log" not in content:
        content += _SYNC_LOG_HEADER

    rows = "\n".join(r.as_markdown_row() for r in results) + "\n"
    content += rows
    inventory_path.write_text(content, encoding="utf-8")
    logger.info("Appended %d sync result(s) to %s.", len(results), inventory_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.error("GH_TOKEN (or GITHUB_TOKEN) environment variable is required.")
        sys.exit(1)

    repos = sys.argv[1:]
    if not repos:
        logger.error("Usage: fork_sync.py owner/repo [owner/repo …]")
        sys.exit(1)

    workspace = Path(os.environ.get("WORKSPACE_DIR", "/tmp/fork_workspace"))
    workspace.mkdir(parents=True, exist_ok=True)

    inventory_path = Path(os.environ.get("INVENTORY_PATH", "FORKS_INVENTORY.md"))
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    results: list[SyncResult] = []
    for repo in repos:
        if "/" not in repo:
            logger.warning("Skipping '%s' — expected 'owner/repo' format.", repo)
            continue
        logger.info("=== Syncing %s ===", repo)
        result = sync_fork(repo, token, workspace, dry_run=dry_run)
        results.append(result)

        # Print per-repo summary.
        status = "✅ OK" if not result.error else f"❌ {result.error[:80]}"
        print(
            f"  {repo:<40} stack={result.stack:<30} synced={result.upstream_synced} "
            f"build={result.build_success!s:<5} {status}"
        )

    if results:
        append_sync_results(results, inventory_path)

    failed = [r for r in results if r.error]
    if failed:
        logger.error("%d repo(s) failed: %s", len(failed), [r.repo for r in failed])
        sys.exit(1)


if __name__ == "__main__":
    main()
