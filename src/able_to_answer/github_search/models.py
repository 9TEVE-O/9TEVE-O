"""Pydantic models for the GitHub skill-search API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SkillRepository(BaseModel):
    """A GitHub repository returned by the skill-search endpoint."""

    id: int = Field(..., description="GitHub repository ID")
    full_name: str = Field(..., description="Owner/repo, e.g. 'example/manus-skills'")
    description: str | None = Field(default=None, description="Repository description")
    html_url: str = Field(..., description="URL to the repository on GitHub")
    stars: int = Field(..., description="Number of stargazers")
    language: str | None = Field(default=None, description="Primary programming language")
    topics: list[str] = Field(default_factory=list, description="Repository topics/tags")
    skill_alignment: str = Field(
        ...,
        description="Manus app skill-alignment score: 'high', 'medium', or 'low'",
    )


class SkillSearchResponse(BaseModel):
    """Response payload for ``GET /v1/github/skills/search``."""

    query: str = Field(..., description="Search query as submitted (without API filters)")
    total_count: int = Field(..., description="Total matching repositories on GitHub")
    repositories: list[SkillRepository] = Field(
        ..., description="Repositories returned in this page, ranked by stars"
    )
