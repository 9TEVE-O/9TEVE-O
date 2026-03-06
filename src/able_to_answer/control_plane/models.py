"""Pydantic models for the Control Plane API."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────

class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TaskStatus(str, Enum):
    pending = "pending"
    dispatched = "dispatched"
    awaiting_approval = "awaiting_approval"
    completed = "completed"
    failed = "failed"


class PolicyDecision(str, Enum):
    allow = "allow"
    deny = "deny"
    pending_approval = "pending_approval"


# ─────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────

class Budget(BaseModel):
    tokens: int | None = Field(default=None, description="Maximum token budget")
    time_s: int | None = Field(default=None, description="Maximum wall-clock time in seconds")


class Actor(BaseModel):
    agent_id: str = Field(..., description="Agent instance identifier")
    role: str = Field(..., description="Agent role: planner/coder/reviewer/qa")


class RequestedAction(BaseModel):
    type: str = Field(
        ...,
        description="Action type, e.g. GIT_COMMIT, GIT_PUSH, DEPLOY, SECRET_ACCESS",
    )
    params: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────
# Action Envelope — wraps every tool/agent call
# ─────────────────────────────────────────────────────────

class ActionEnvelope(BaseModel):
    """Every tool or agent call must be wrapped in this envelope before policy evaluation."""

    run_id: str
    task_id: str
    actor: Actor
    tenant_id: str
    policy_profile_id: str = "default"
    requested_action: RequestedAction
    data_tags: list[str] = Field(
        default_factory=list,
        description="Data classification tags, e.g. ['public', 'pii:none']",
    )
    budget: Budget = Field(default_factory=Budget)


# ─────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────

class PolicyProfile(BaseModel):
    profile_id: str
    description: str
    side_effect_actions: list[str] = Field(
        description="Known side-effect action types tracked by this profile"
    )
    deny_action_types: list[str] = Field(
        description="Action types that are always denied"
    )
    require_approval_for: list[str] = Field(
        description="Action types that require human approval"
    )
    default_decision: PolicyDecision = Field(
        description="Decision for all other (non-side-effect) actions"
    )


# ─────────────────────────────────────────────────────────
# Runs
# ─────────────────────────────────────────────────────────

class CreateRunRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant / workspace identifier")
    project_id: str | None = Field(default=None, description="Project identifier")
    goal: str = Field(..., min_length=1, description="Natural-language goal for this run")
    inputs: dict[str, Any] = Field(default_factory=dict)
    repo_refs: list[str] = Field(default_factory=list, description="Repository refs")
    policy_profile_id: str = Field(default="default", description="Policy profile to enforce")
    budget: Budget = Field(default_factory=Budget)


class RunResponse(BaseModel):
    run_id: str
    tenant_id: str
    project_id: str | None
    goal: str
    status: RunStatus
    policy_profile_id: str
    created_at: int


# ─────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────

class CreateTaskRequest(BaseModel):
    type: str = Field(..., description="Task type, e.g. plan, code, review, test")
    agent_role: str = Field(..., description="Agent role: planner/coder/reviewer/qa")
    inputs: dict[str, Any] = Field(default_factory=dict)


class DispatchTaskRequest(BaseModel):
    action_type: str = Field(
        ...,
        description="Action type for policy evaluation, e.g. GIT_COMMIT, GIT_PUSH",
    )
    inputs: dict[str, Any] = Field(default_factory=dict)


class CompleteTaskRequest(BaseModel):
    outputs: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = Field(
        default=TaskStatus.completed,
        description="Terminal status: completed or failed",
    )


class TaskResponse(BaseModel):
    task_id: str
    run_id: str
    status: TaskStatus
    type: str
    agent_role: str | None
    created_at: int


# ─────────────────────────────────────────────────────────
# Artifacts
# ─────────────────────────────────────────────────────────

class ArtifactResponse(BaseModel):
    artifact_id: str
    run_id: str
    type: str
    content_hash: str
    created_at: int


class ArtifactDetailResponse(ArtifactResponse):
    content: dict[str, Any]


# ─────────────────────────────────────────────────────────
# Policy evaluation
# ─────────────────────────────────────────────────────────

class PolicyEvaluateRequest(BaseModel):
    envelope: ActionEnvelope


class PolicyEvaluateResponse(BaseModel):
    decision: PolicyDecision
    reason: str
    policy_profile_id: str


# ─────────────────────────────────────────────────────────
# Approval
# ─────────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    approved_by: str | None = Field(default=None, description="Identity of the approver")
    note: str | None = Field(default=None, description="Optional approval note")
