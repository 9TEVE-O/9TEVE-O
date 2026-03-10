"""FastAPI router for GitHub skill search (prefix: /v1/github)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from able_to_answer.core.config import settings
from able_to_answer.core.logging import logger
from able_to_answer.github_search.client import GitHubSearchClient, score_skill_alignment
from able_to_answer.github_search.models import SkillRepository, SkillSearchResponse

router = APIRouter(prefix="/v1/github", tags=["github-skill-search"])

# Module-level client — replaced in tests via:
#   import able_to_answer.github_search.router as gh_router_module
#   gh_router_module.gh_client = <mock>
gh_client = GitHubSearchClient(token=settings.github_token)


def _parse_topic_list(topics: str | None) -> list[str] | None:
    """Convert a comma-separated topic string to a list, or ``None`` if empty."""
    if not topics:
        return None
    return [t.strip() for t in topics.split(",") if t.strip()]


@router.get("/skills/search", response_model=SkillSearchResponse)
def search_skills(
    query: str = Query(..., min_length=1, description="Search terms, e.g. 'manus skill'"),
    language: str | None = Query(default=None, description="Filter by language, e.g. 'python'"),
    topics: str | None = Query(
        default=None,
        description="Comma-separated topic filters, e.g. 'manus,skill'",
    ),
    per_page: int = Query(default=10, ge=1, le=30, description="Results per page (max 30)"),
) -> SkillSearchResponse:
    """Search GitHub for repositories whose skills can be aligned with a Manus app.

    The endpoint queries the GitHub repository search API and scores each result
    against Manus-relevant topics and keywords, returning an alignment score of
    ``"high"``, ``"medium"``, or ``"low"`` for every repository.

    Requires ``ATA_GITHUB_TOKEN`` for better rate limits (optional but recommended).
    """
    topic_list = _parse_topic_list(topics)

    try:
        result = gh_client.search_repositories(
            query=query,
            language=language,
            topics=topic_list,
            per_page=per_page,
        )
    except RuntimeError as exc:
        logger.warning("github_search: GitHub API error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repositories = [
        SkillRepository(
            id=item["id"],
            full_name=item["full_name"],
            description=item.get("description"),
            html_url=item["html_url"],
            stars=item.get("stargazers_count", 0),
            language=item.get("language"),
            topics=item.get("topics") or [],
            skill_alignment=score_skill_alignment(item),
        )
        for item in result.get("items", [])
    ]

    logger.info(
        "github_search: query=%r total=%d returned=%d",
        query,
        result.get("total_count", 0),
        len(repositories),
    )

    return SkillSearchResponse(
        query=query,
        total_count=result.get("total_count", 0),
        repositories=repositories,
    )
