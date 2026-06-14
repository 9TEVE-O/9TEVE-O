"""FastAPI router for the Control Plane API (prefix: /v1)."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from able_to_answer.control_plane.models import (
    ActionEnvelope,
    ApproveRequest,
    ArtifactDetailResponse,
    ArtifactResponse,
    CompleteTaskRequest,
    CreateRunRequest,
    CreateTaskRequest,
    DispatchTaskRequest,
    PolicyDecision,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    RunResponse,
    RequestedAction,
    RunStatus,
    TaskResponse,
    TaskStatus,
)
from able_to_answer.control_plane.policy import evaluate_action, get_policy_profile
from able_to_answer.control_plane.storage import ControlPlaneStore
from able_to_answer.core.config import settings
from able_to_answer.core.logging import logger

router = APIRouter(prefix="/v1", tags=["control-plane"])

# Module-level store — replaced in tests via: import able_to_answer.control_plane.router as mod; mod.cp_store = ...
cp_store = ControlPlaneStore(settings.db_path)

_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


# ─────────────────────────────────────────────────────────
# Runs
# ─────────────────────────────────────────────────────────

@router.post("/runs", status_code=201)
def create_run(req: CreateRunRequest) -> dict:
    run_id = cp_store.create_run(
        tenant_id=req.tenant_id,
        goal=req.goal,
        project_id=req.project_id,
        inputs=req.inputs,
        repo_refs=req.repo_refs,
        policy_profile_id=req.policy_profile_id,
        budget_tokens=req.budget.tokens,
        budget_time_s=req.budget.time_s,
    )
    logger.info("control_plane: run_created run=%s tenant=%s", run_id, req.tenant_id)
    return {"run_id": run_id}


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str) -> RunResponse:
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")
    return RunResponse(
        run_id=row["id"],
        tenant_id=row["tenant_id"],
        project_id=row["project_id"],
        goal=row["goal"],
        status=RunStatus(row["status"]),
        policy_profile_id=row["policy_profile_id"],
        created_at=row["created_at"],
    )


@router.post("/runs/{run_id}/cancel", status_code=200)
def cancel_run(run_id: str) -> dict:
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")
    if row["status"] in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Run is already in terminal state: {row['status']}",
        )
    cp_store.update_run_status(run_id=run_id, status="cancelled")
    logger.info("control_plane: run_cancelled run=%s", run_id)
    return {"run_id": run_id, "status": "cancelled"}


@router.post("/runs/{run_id}/approve", status_code=200)
def approve_run(run_id: str, req: ApproveRequest) -> dict:
    """Approve all tasks currently in *awaiting_approval* state for this run.

    ``req.approved_by`` should identify the human approver for the audit log.
    """
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")

    tasks = cp_store.list_awaiting_approval_tasks(run_id=run_id)
    for task in tasks:
        cp_store.update_task_status(task_id=task["id"], status="dispatched")

    approved_by = req.approved_by
    logger.info(
        "control_plane: run_approved run=%s approved_tasks=%d approved_by=%s",
        run_id,
        len(tasks),
        approved_by,
    )
    return {"run_id": run_id, "approved_tasks": len(tasks)}


# ─────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────

@router.post("/runs/{run_id}/tasks", status_code=201, response_model=TaskResponse)
def create_task(run_id: str, req: CreateTaskRequest) -> TaskResponse:
    """Create a new task within an existing run."""
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")
    task_id = cp_store.create_task(
        run_id=run_id,
        task_type=req.type,
        agent_role=req.agent_role,
        inputs=req.inputs,
    )
    task = cp_store.get_task(task_id=task_id)
    return TaskResponse(
        task_id=task["id"],
        run_id=task["run_id"],
        status=TaskStatus(task["status"]),
        type=task["type"],
        agent_role=task["agent_role"],
        created_at=task["created_at"],
    )


@router.get("/runs/{run_id}/tasks", response_model=list[TaskResponse])
def list_tasks(run_id: str) -> list[TaskResponse]:
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")
    tasks = cp_store.list_tasks(run_id=run_id)
    return [
        TaskResponse(
            task_id=t["id"],
            run_id=t["run_id"],
            status=TaskStatus(t["status"]),
            type=t["type"],
            agent_role=t["agent_role"],
            created_at=t["created_at"],
        )
        for t in tasks
    ]


@router.post("/tasks/{task_id}/dispatch", status_code=200)
def dispatch_task(task_id: str, req: DispatchTaskRequest) -> dict:
    """Evaluate policy before dispatching a pending task."""
    task = cp_store.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    run = cp_store.get_run(run_id=task["run_id"])
    if not run:
        raise HTTPException(status_code=404, detail="run_not_found")
    if task["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Task is not in pending state: {task['status']}",
        )

    if req.envelope is not None:
        envelope = req.envelope
    else:
        if req.actor is None or req.action_type is None:
            raise HTTPException(
                status_code=422,
                detail="dispatch_request_missing_envelope_or_shorthand_fields",
            )
        envelope = ActionEnvelope(
            run_id=run["id"],
            task_id=task["id"],
            actor=req.actor,
            tenant_id=run["tenant_id"],
            policy_profile_id=run["policy_profile_id"],
            requested_action=RequestedAction(type=req.action_type, params=req.inputs),
        )
    stored_values = {
        "run_id": run["id"],
        "task_id": task["id"],
        "tenant_id": run["tenant_id"],
        "policy_profile_id": run["policy_profile_id"],
    }
    for field, stored_value in stored_values.items():
        if getattr(envelope, field) != stored_value:
            raise HTTPException(status_code=403, detail=f"dispatch_{field}_mismatch")

    try:
        decision, reason = evaluate_action(envelope)
    except Exception:
        decision = PolicyDecision.deny
        reason = "Policy evaluation failed; defaulting to deny."
        logger.exception(
            "control_plane: policy_evaluation_failed task=%s run=%s", task_id, run["id"]
        )

    cp_store.record_policy_decision(
        run_id=run["id"],
        task_id=task_id,
        action_type=envelope.requested_action.type,
        decision=decision.value,
        reason=reason,
    )

    if decision == PolicyDecision.deny:
        raise HTTPException(
            status_code=403,
            detail={"policy_decision": decision.value, "reason": reason},
        )

    status = "dispatched" if decision == PolicyDecision.allow else "awaiting_approval"
    cp_store.update_task_status(task_id=task_id, status=status)
    logger.info(
        "control_plane: task_dispatch_evaluated task=%s run=%s decision=%s status=%s",
        task_id,
        run["id"],
        decision.value,
        status,
    )
    return {
        "task_id": task_id,
        "status": status,
        "policy_decision": decision.value,
        "reason": reason,
    }


@router.post("/tasks/{task_id}/complete", status_code=200)
def complete_task(task_id: str, req: CompleteTaskRequest) -> dict:
    """Mark a dispatched task as completed or failed."""
    task = cp_store.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    if task["status"] not in {"dispatched", "awaiting_approval"}:
        raise HTTPException(
            status_code=409,
            detail=f"Task cannot be completed from state: {task['status']}",
        )
    cp_store.update_task_status(
        task_id=task_id,
        status=req.status.value,
        outputs=req.outputs,
    )
    logger.info("control_plane: task_completed task=%s status=%s", task_id, req.status.value)
    return {"task_id": task_id, "status": req.status.value}


# ─────────────────────────────────────────────────────────
# Artifacts
# ─────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(run_id: str) -> list[ArtifactResponse]:
    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")
    artifacts = cp_store.list_artifacts(run_id=run_id)
    return [
        ArtifactResponse(
            artifact_id=a["id"],
            run_id=a["run_id"],
            type=a["type"],
            content_hash=a["content_hash"],
            created_at=a["created_at"],
        )
        for a in artifacts
    ]


@router.get("/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def get_artifact(artifact_id: str) -> ArtifactDetailResponse:
    row = cp_store.get_artifact(artifact_id=artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    return ArtifactDetailResponse(
        artifact_id=row["id"],
        run_id=row["run_id"],
        type=row["type"],
        content_hash=row["content_hash"],
        created_at=row["created_at"],
        content=json.loads(row["content_json"]),
    )


# ─────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────

@router.get("/policies/{policy_profile_id}")
def get_policy(policy_profile_id: str) -> dict:
    profile = get_policy_profile(policy_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="policy_profile_not_found")
    return profile.model_dump()


@router.post("/policies/evaluate", response_model=PolicyEvaluateResponse)
def evaluate_policy(req: PolicyEvaluateRequest) -> PolicyEvaluateResponse:
    """Dry-run policy evaluation — does NOT record a decision or change state."""
    decision, reason = evaluate_action(req.envelope)
    return PolicyEvaluateResponse(
        decision=decision,
        reason=reason,
        policy_profile_id=req.envelope.policy_profile_id,
    )
