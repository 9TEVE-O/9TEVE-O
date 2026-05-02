"""FastAPI router for the suggest-upgrades feature (prefix: /v1/github)."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from able_to_answer.core.config import settings
from able_to_answer.core.logging import logger
from able_to_answer.suggest_upgrades.analyzer import analyse
from able_to_answer.suggest_upgrades.github_ops import GitHubOpsClient
from able_to_answer.suggest_upgrades.models import SuggestUpgradesRequest, SuggestUpgradesResponse

router = APIRouter(prefix="/v1/github", tags=["suggest-upgrades"])

# Module-level client — replaced in tests via:
#   import able_to_answer.suggest_upgrades.router as su_router_module
#   su_router_module.gh_ops_client = <mock>
gh_ops_client = GitHubOpsClient(token=settings.github_token)


@router.post("/suggest-upgrades", response_model=SuggestUpgradesResponse)
def suggest_upgrades(req: SuggestUpgradesRequest) -> SuggestUpgradesResponse:
    """Analyse a GitHub repository and propose up to 5 actionable enhancements.

    When ``auto_push`` is ``true`` the endpoint also:

    1. Creates a new branch (``upgrade-<timestamp>``) from the default branch.
    2. Commits each suggestion that carries a ``file_path`` and ``code_snippet``.
    3. Opens a pull request and returns its URL in ``pr_url``.

    A GitHub token (``ATA_GITHUB_TOKEN``) with ``contents:write`` and
    ``pull-requests:write`` permissions is required for ``auto_push=true``.
    """
    owner, repo_name = req.repo.split("/", 1)

    # ── Step 1: fetch optional manifest for smarter suggestions ─────────────
    manifest_content: str | None = None
    try:
        manifest_content = gh_ops_client.get_file_contents(owner, repo_name, "pyproject.toml")
        if manifest_content is None:
            manifest_content = gh_ops_client.get_file_contents(owner, repo_name, "package.json")
    except RuntimeError as exc:
        logger.warning("suggest_upgrades: could not fetch manifest for %s: %s", req.repo, exc)

    # ── Step 2: rule-based analysis ──────────────────────────────────────────
    suggestions = analyse(
        repo=req.repo,
        focus=req.focus,
        manifest_content=manifest_content,
    )

    if not suggestions:
        logger.info("suggest_upgrades: no suggestions for repo=%s focus=%s", req.repo, req.focus)
        return SuggestUpgradesResponse(repo=req.repo, focus=req.focus, suggestions=[])

    logger.info(
        "suggest_upgrades: repo=%s focus=%s suggestions=%d auto_push=%s",
        req.repo,
        req.focus,
        len(suggestions),
        req.auto_push,
    )

    # ── Step 3 (optional): implement suggestions on a new branch ────────────
    pr_url: str | None = None
    if req.auto_push:
        if not gh_ops_client.has_token:
            raise HTTPException(
                status_code=422,
                detail="auto_push requires ATA_GITHUB_TOKEN to be configured.",
            )
        try:
            default_branch, base_sha = gh_ops_client.get_default_branch_sha(owner, repo_name)
            new_branch = f"upgrade-{int(time.time())}"
            gh_ops_client.create_branch(owner, repo_name, branch=new_branch, sha=base_sha)

            implementable = [s for s in suggestions if s.file_path and s.code_snippet]
            for suggestion in implementable:
                gh_ops_client.create_or_update_file(
                    owner,
                    repo_name,
                    path=suggestion.file_path,  # type: ignore[arg-type]
                    message=f"[suggest-upgrades] {suggestion.title}",
                    content=suggestion.code_snippet,  # type: ignore[arg-type]
                    branch=new_branch,
                )

            body_lines = [
                "## Proposed repository enhancements\n",
                f"Focus area: **{req.focus}**\n",
            ]
            for s in suggestions:
                body_lines.append(f"### {s.title}\n{s.description}\n\n_{s.rationale}_\n")

            pr_url = gh_ops_client.create_pull_request(
                owner,
                repo_name,
                title=f"[suggest-upgrades] Repository enhancements ({req.focus})",
                body="\n".join(body_lines),
                head=new_branch,
                base=default_branch,
            )
            logger.info("suggest_upgrades: pr_created repo=%s pr=%s", req.repo, pr_url)
        except RuntimeError as exc:
            logger.error("suggest_upgrades: auto_push failed for %s: %s", req.repo, exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SuggestUpgradesResponse(
        repo=req.repo,
        focus=req.focus,
        suggestions=suggestions,
        pr_url=pr_url,
    )
