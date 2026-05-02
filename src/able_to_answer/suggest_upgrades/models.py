"""Pydantic models for the suggest-upgrades API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SuggestUpgradesRequest(BaseModel):
    """Request body for ``POST /v1/github/suggest-upgrades``."""

    repo: str = Field(
        ...,
        description="Owner/repository identifier, e.g. 'org/project-name'.",
        pattern=r"^[^/]+/[^/]+$",
    )
    focus: str = Field(
        default="all",
        description="Area of focus: 'security', 'performance', 'testing', or 'all'.",
    )
    auto_push: bool = Field(
        default=False,
        description="When true, implement suggestions on a new branch and open a PR.",
    )


class Suggestion(BaseModel):
    """A single proposed repository enhancement."""

    title: str = Field(..., description="Short title of the suggestion")
    description: str = Field(..., description="Explanation of the change and its benefits")
    file_path: str | None = Field(
        default=None, description="Target file path relative to the repository root"
    )
    code_snippet: str | None = Field(
        default=None, description="Code or configuration to write to *file_path*"
    )
    rationale: str = Field(..., description="Why this change is important")


class SuggestUpgradesResponse(BaseModel):
    """Response from ``POST /v1/github/suggest-upgrades``."""

    repo: str = Field(..., description="Owner/repository identifier")
    focus: str = Field(..., description="Area of focus that was applied")
    suggestions: list[Suggestion] = Field(..., description="Proposed enhancements")
    pr_url: str | None = Field(
        default=None,
        description="URL of the pull request created when auto_push=true",
    )
