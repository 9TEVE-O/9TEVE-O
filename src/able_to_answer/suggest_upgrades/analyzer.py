"""Rule-based repository analyser for the suggest-upgrades feature.

This module produces actionable suggestions without an external LLM call,
satisfying the MVP requirement of zero external model dependencies.
"""
from __future__ import annotations

from .models import Suggestion

# ─────────────────────────────────────────────────────────
# Suggestion catalogue
# Each entry is a (focus_tags, Suggestion) pair.
# ``focus_tags`` is a frozenset of the focus values that include this item;
# the special tag "all" means the item is included for every focus.
# ─────────────────────────────────────────────────────────

_CATALOGUE: list[tuple[frozenset[str], Suggestion]] = [
    # ── Security ────────────────────────────────────────
    (
        frozenset({"security", "all"}),
        Suggestion(
            title="Add a SECURITY.md policy file",
            description=(
                "A SECURITY.md file instructs security researchers how to report "
                "vulnerabilities responsibly, reducing the risk of public disclosure "
                "before a fix is available."
            ),
            file_path="SECURITY.md",
            code_snippet=(
                "# Security Policy\n\n"
                "## Supported Versions\n\n"
                "| Version | Supported |\n"
                "|---------|----------|\n"
                "| latest  | ✅       |\n\n"
                "## Reporting a Vulnerability\n\n"
                "Please report security vulnerabilities by opening a "
                "[GitHub Security Advisory]"
                "(https://github.com/{repo}/security/advisories/new) "
                "rather than a public issue.\n\n"
                "We aim to acknowledge reports within 48 hours and publish "
                "a fix within 90 days.\n"
            ),
            rationale=(
                "GitHub and the wider open-source community expect a responsible "
                "disclosure process. Without SECURITY.md, reporters default to "
                "opening public issues, potentially exposing users before a patch lands."
            ),
        ),
    ),
    (
        frozenset({"security", "all"}),
        Suggestion(
            title="Pin GitHub Actions to full commit SHAs",
            description=(
                "Using mutable version tags (e.g. ``@v4``) for GitHub Actions "
                "exposes the workflow to supply-chain attacks if the tag is moved. "
                "Pinning to a full SHA makes the dependency immutable."
            ),
            file_path=None,
            code_snippet=None,
            rationale=(
                "Supply-chain attacks via compromised Action tags have occurred in "
                "the wild. SHA-pinning, combined with Dependabot version updates, "
                "gives both security and up-to-date dependencies."
            ),
        ),
    ),
    # ── Performance ─────────────────────────────────────
    (
        frozenset({"performance", "all"}),
        Suggestion(
            title="Enable pip dependency caching in CI",
            description=(
                "Adding ``cache: 'pip'`` to the ``setup-python`` step, or using "
                "``actions/cache``, avoids re-downloading and re-installing packages "
                "on every CI run, typically cutting install time by 60–80 %."
            ),
            file_path=None,
            code_snippet=(
                "# In .github/workflows/ci.yml, under 'Set up Python':\n"
                "- uses: actions/setup-python@v5\n"
                "  with:\n"
                "    python-version: \"3.12\"\n"
                "    cache: 'pip'\n"
            ),
            rationale=(
                "CI pipelines frequently spend more time installing dependencies than "
                "running tests. Caching reduces feedback latency and GitHub Actions "
                "minute consumption."
            ),
        ),
    ),
    (
        frozenset({"performance", "all"}),
        Suggestion(
            title="Add a .python-version file for consistent interpreter selection",
            description=(
                "A ``.python-version`` file (used by pyenv, mise, and similar tools) "
                "ensures that all contributors and CI use the same Python version, "
                "preventing subtle compatibility issues."
            ),
            file_path=".python-version",
            code_snippet="3.12\n",
            rationale=(
                "Version drift between developer machines and CI is a common source "
                "of 'works on my machine' failures. A pinned ``.python-version`` "
                "eliminates that class of issue at zero cost."
            ),
        ),
    ),
    # ── Testing ──────────────────────────────────────────
    (
        frozenset({"testing", "all"}),
        Suggestion(
            title="Add a pytest configuration block to pyproject.toml",
            description=(
                "Centralising pytest settings (test paths, verbosity, coverage "
                "requirements) in ``pyproject.toml`` removes the need for a separate "
                "``pytest.ini`` or ``setup.cfg`` and makes the test harness "
                "self-documenting."
            ),
            file_path="pyproject.toml",
            code_snippet=(
                "[tool.pytest.ini_options]\n"
                "testpaths = [\"tests\"]\n"
                "addopts = \"-v --tb=short\"\n"
            ),
            rationale=(
                "Having test configuration in a single canonical file (``pyproject.toml``) "
                "reduces cognitive overhead and prevents accidental test-runner "
                "misconfiguration."
            ),
        ),
    ),
    (
        frozenset({"testing", "all"}),
        Suggestion(
            title="Configure Dependabot for automated dependency updates",
            description=(
                "A ``.github/dependabot.yml`` file directs GitHub to open pull "
                "requests whenever a direct dependency releases a newer version, "
                "keeping the project secure and up-to-date with minimal manual effort."
            ),
            file_path=".github/dependabot.yml",
            code_snippet=(
                "version: 2\nupdates:\n"
                "  - package-ecosystem: pip\n"
                "    directory: /\n"
                "    schedule:\n"
                "      interval: weekly\n"
                "  - package-ecosystem: github-actions\n"
                "    directory: /\n"
                "    schedule:\n"
                "      interval: weekly\n"
            ),
            rationale=(
                "Manual dependency updates are often deferred until a vulnerability is "
                "disclosed. Dependabot automates the process and surfaces security "
                "advisories as actionable PRs."
            ),
        ),
    ),
]


def analyse(
    *,
    repo: str,
    focus: str,
    manifest_content: str | None = None,
) -> list[Suggestion]:
    """Return a list of suggestions for the given repository.

    Parameters
    ----------
    repo:
        Owner/repository string, e.g. ``"org/project"``.
    focus:
        One of ``"security"``, ``"performance"``, ``"testing"``, or ``"all"``.
    manifest_content:
        Raw text of the repo's ``pyproject.toml`` or ``package.json`` (optional).
        When provided, suggestions that conflict with already-present config are
        filtered out.

    Returns
    -------
    list[Suggestion]
        Up to 5 suggestions, most relevant first.
    """
    normalised_focus = focus.lower().strip()
    if normalised_focus not in {"security", "performance", "testing", "all"}:
        normalised_focus = "all"

    results: list[Suggestion] = []
    for tags, suggestion in _CATALOGUE:
        # Include the suggestion only when the requested focus matches one of its
        # tags, or when the focus is "all" (in which case every entry is included).
        if normalised_focus != "all" and normalised_focus not in tags:
            continue
        # Skip suggestions whose file content already exists in the manifest.
        if manifest_content and suggestion.file_path == "pyproject.toml":
            if "[tool.pytest.ini_options]" in manifest_content:
                continue
        results.append(
            # Interpolate {repo} placeholder in code snippets if present.
            Suggestion(
                title=suggestion.title,
                description=suggestion.description,
                file_path=suggestion.file_path,
                code_snippet=(
                    suggestion.code_snippet.replace("{repo}", repo)
                    if suggestion.code_snippet
                    else None
                ),
                rationale=suggestion.rationale,
            )
        )

    return results[:5]
