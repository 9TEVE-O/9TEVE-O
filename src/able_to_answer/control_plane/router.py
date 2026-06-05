"""FastAPI router for the Control Plane API (prefix: /v1)."""
from __future__ import annotations

import json
import sqlite3
import time

from fastapi import APIRouter, Header, HTTPException

from able_to_answer.control_plane.models import (
    ApproveRequest,
    ArtifactDetailResponse,
    ArtifactResponse,
    CompleteTaskRequest,
    CreateRunRequest,
    CreateTaskRequest,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    RunResponse,
    RunStatus,
    TaskResponse,
    TaskStatus,
)
from able_to_answer.control_plane.policy import evaluate_action, get_policy_profile
from able_to_answer.control_plane.storage import (
    ApprovalDispatchConflictError,
    ControlPlaneStore,
)
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
def approve_run(
    run_id: str,
    req: ApproveRequest,
    principal_id: str | None = Header(default=None, alias="X-Principal-ID"),
    principal_type: str | None = Header(default=None, alias="X-Principal-Type"),
    trace_id: str | None = Header(default=None, alias="X-Trace-ID"),
) -> dict:
    """
    Persist a human approver's decision for a single pending policy decision and dispatch the associated task.
    
    Returns:
        result (dict): A payload containing:
            - `approval_id`: the created approval's identifier
            - `decision_id`: the policy decision identifier from the request
            - `task_id`: the task identifier from the request
            - `status`: the approval dispatch status, always `"dispatched"`
    """
    if not principal_id or not principal_type:
        raise HTTPException(status_code=401, detail="authenticated_principal_required")
    if principal_type != "human":
        raise HTTPException(status_code=403, detail="human_approver_required")
    if not trace_id:
        raise HTTPException(status_code=400, detail="trace_id_required")

    row = cp_store.get_run(run_id=run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run_not_found")

    task = cp_store.get_task(task_id=req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    if task["run_id"] != run_id:
        raise HTTPException(status_code=409, detail="approval_task_mismatch")
    if cp_store.get_approval_for_decision(decision_id=req.decision_id):
        raise HTTPException(status_code=409, detail="approval_already_recorded")
    if task["status"] != "awaiting_approval":
        raise HTTPException(status_code=409, detail="task_not_awaiting_approval")

    decision = cp_store.get_policy_decision(decision_id=req.decision_id)
    if (
        not decision
        or decision["run_id"] != run_id
        or decision["task_id"] != req.task_id
    ):
        raise HTTPException(status_code=409, detail="approval_decision_mismatch")
    if decision["decision"] != "pending_approval":
        raise HTTPException(status_code=409, detail="decision_not_awaiting_approval")
    if decision["action_type"] != req.action_type:
        raise HTTPException(status_code=409, detail="approval_action_mismatch")
    if req.expires_at <= int(time.time()):
        raise HTTPException(status_code=409, detail="approval_expired")

    try:
        approval = cp_store.create_approval_and_dispatch(
            run_id=run_id,
            task_id=req.task_id,
            action_type=req.action_type,
            decision_id=req.decision_id,
            approver_id=principal_id,
            expires_at=req.expires_at,
            note=req.note,
            trace_id=trace_id,
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="approval_already_recorded") from exc
    except ApprovalDispatchConflictError as exc:
        raise HTTPException(status_code=409, detail="task_not_awaiting_approval") from exc

    logger.info(
        "control_plane: approval_recorded approval=%s decision=%s task=%s run=%s approver=%s trace=%s",
        approval.approval_id,
        req.decision_id,
        req.task_id,
        run_id,
        principal_id,
        trace_id,
    )
    return {
        "approval_id": approval.approval_id,
        "decision_id": req.decision_id,
        "task_id": req.task_id,
        "status": "dispatched",
    }


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
def dispatch_task(task_id: str) -> dict:
    """Dispatch a pending task directly."""
    task = cp_store.get_task(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    if task["status"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Task is not in pending state: {task['status']}",
        )

    cp_store.update_task_status(task_id=task_id, status="dispatched")

    logger.info(
        "control_plane: task_dispatched task=%s run=%s",
        task_id,
        task["run_id"],
    )
    return {
        "task_id": task_id,
        "status": "dispatched",
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
