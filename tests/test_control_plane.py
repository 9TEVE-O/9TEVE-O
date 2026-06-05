from __future__ import annotations

import logging
import time

import pytest
from fastapi.testclient import TestClient

from able_to_answer.api.main import app
from able_to_answer.control_plane.storage import ControlPlaneStore
import able_to_answer.control_plane.router as cp_router_module


@pytest.fixture()
def client(tmp_path):
    """Test client backed by a temporary SQLite database."""
    db_path = str(tmp_path / "test_cp.sqlite3")
    test_store = ControlPlaneStore(db_path)
    original_store = cp_router_module.cp_store
    cp_router_module.cp_store = test_store
    yield TestClient(app)
    cp_router_module.cp_store = original_store


# ─────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────

def _create_run(client, *, goal="Implement feature X", tenant_id="tenant_1", policy_profile_id="default"):
    return client.post(
        "/v1/runs",
        json={"tenant_id": tenant_id, "goal": goal, "policy_profile_id": policy_profile_id},
    )


def _create_task(client, run_id, *, task_type="code", agent_role="coder"):
    return client.post(
        f"/v1/runs/{run_id}/tasks",
        json={"type": task_type, "agent_role": agent_role},
    )


def _dispatch(client, task_id, *, action_type="GIT_COMMIT"):
    return client.post(
        f"/v1/tasks/{task_id}/dispatch",
        json={
            "actor": {"agent_id": "agent_1", "role": "coder"},
            "action_type": action_type,
        },
    )


def _dispatch_envelope(
    client,
    task_id,
    run_id,
    *,
    action_type,
    tenant_id="tenant_1",
    policy_profile_id="default",
    envelope_task_id=None,
):
    return client.post(
        f"/v1/tasks/{task_id}/dispatch",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": envelope_task_id or task_id,
                "actor": {"agent_id": "agent_1", "role": "coder"},
                "tenant_id": tenant_id,
                "policy_profile_id": policy_profile_id,
                "requested_action": {"type": action_type, "params": {}},
            }
        },
    )


def _task_status(task_id):
    return cp_router_module.cp_store.get_task(task_id=task_id)["status"]


def _policy_decisions():
    with cp_router_module.cp_store._connect() as con:
        return con.execute("SELECT * FROM cp_policy_decisions ORDER BY created_at").fetchall()


# ─────────────────────────────────────────────────────────
# Runs — happy path
# ─────────────────────────────────────────────────────────

def test_create_run(client):
    resp = _create_run(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["run_id"].startswith("run_")


def test_get_run(client):
    run_id = _create_run(client).json()["run_id"]
    resp = client.get(f"/v1/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["status"] == "pending"
    assert data["tenant_id"] == "tenant_1"
    assert data["goal"] == "Implement feature X"
    assert data["policy_profile_id"] == "default"
    assert "created_at" in data


def test_create_run_with_budget(client):
    resp = client.post(
        "/v1/runs",
        json={
            "tenant_id": "t1",
            "goal": "goal",
            "budget": {"tokens": 100000, "time_s": 3600},
        },
    )
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]
    run = client.get(f"/v1/runs/{run_id}").json()
    assert run["run_id"] == run_id


# ─────────────────────────────────────────────────────────
# Runs — edge cases
# ─────────────────────────────────────────────────────────

def test_get_run_not_found(client):
    resp = client.get("/v1/runs/run_doesnotexist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "run_not_found"


def test_create_run_empty_goal_rejected(client):
    resp = client.post("/v1/runs", json={"tenant_id": "t1", "goal": ""})
    assert resp.status_code == 422


def test_cancel_run(client):
    run_id = _create_run(client).json()["run_id"]
    resp = client.post(f"/v1/runs/{run_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Verify status persisted
    run = client.get(f"/v1/runs/{run_id}").json()
    assert run["status"] == "cancelled"


def test_cancel_run_not_found(client):
    resp = client.post("/v1/runs/run_doesnotexist/cancel")
    assert resp.status_code == 404


def test_cancel_already_cancelled_run_returns_409(client):
    run_id = _create_run(client).json()["run_id"]
    client.post(f"/v1/runs/{run_id}/cancel")
    resp = client.post(f"/v1/runs/{run_id}/cancel")
    assert resp.status_code == 409


# ─────────────────────────────────────────────────────────
# Tasks — happy path
# ─────────────────────────────────────────────────────────

def test_create_and_list_tasks(client):
    run_id = _create_run(client).json()["run_id"]
    task_resp = _create_task(client, run_id)
    assert task_resp.status_code == 201
    data = task_resp.json()
    assert data["task_id"].startswith("task_")
    assert data["run_id"] == run_id
    assert data["status"] == "pending"
    assert data["type"] == "code"
    assert data["agent_role"] == "coder"

    list_resp = client.get(f"/v1/runs/{run_id}/tasks")
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == data["task_id"]


def test_dispatch_task_allowed(client):
    """Allowed shorthand requests are recorded and dispatched."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch(client, task_id)

    assert resp.status_code == 200
    assert resp.json()["status"] == "dispatched"
    assert resp.json()["policy_decision"] == "allow"
    assert _task_status(task_id) == "dispatched"
    assert _policy_decisions()[0]["decision"] == "allow"


def test_dispatch_task_denied(client):
    """Denied envelope requests are recorded and remain pending."""
    run_id = _create_run(client, policy_profile_id="strict").json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(
        client, task_id, run_id, action_type="GIT_PUSH", policy_profile_id="strict"
    )

    assert resp.status_code == 403
    assert resp.json()["detail"]["policy_decision"] == "deny"
    assert _task_status(task_id) == "pending"
    assert _policy_decisions()[0]["decision"] == "deny"


def test_dispatch_task_approval_required(client):
    """Approval-required envelope requests are recorded and await approval."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(client, task_id, run_id, action_type="GIT_PUSH")

    assert resp.status_code == 200
    assert resp.json()["status"] == "awaiting_approval"
    assert resp.json()["policy_decision"] == "pending_approval"
    assert _task_status(task_id) == "awaiting_approval"
    assert _policy_decisions()[0]["decision"] == "pending_approval"


def test_dispatch_task_mismatched_tenant(client):
    """An envelope cannot cross the run's stored tenant boundary."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(
        client, task_id, run_id, action_type="GIT_COMMIT", tenant_id="tenant_2"
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "dispatch_tenant_id_mismatch"
    assert _task_status(task_id) == "pending"
    assert _policy_decisions() == []


def test_dispatch_task_mismatched_run(client):
    """An envelope cannot claim a run other than the task's parent run."""
    run_id = _create_run(client).json()["run_id"]
    other_run_id = _create_run(client, goal="Other run").json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(client, task_id, other_run_id, action_type="GIT_COMMIT")

    assert resp.status_code == 403
    assert resp.json()["detail"] == "dispatch_run_id_mismatch"
    assert _task_status(task_id) == "pending"
    assert _policy_decisions() == []


def test_dispatch_task_mismatched_task(client):
    """An envelope cannot claim a task other than the path task."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(
        client, task_id, run_id, action_type="GIT_COMMIT", envelope_task_id="task_other"
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "dispatch_task_id_mismatch"
    assert _task_status(task_id) == "pending"
    assert _policy_decisions() == []


def test_dispatch_task_mismatched_policy_profile(client):
    """An envelope cannot override the run's stored policy profile."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = _dispatch_envelope(
        client, task_id, run_id, action_type="GIT_COMMIT", policy_profile_id="strict"
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "dispatch_policy_profile_id_mismatch"
    assert _task_status(task_id) == "pending"
    assert _policy_decisions() == []


def test_dispatch_task_policy_evaluation_failure_defaults_to_deny(client, monkeypatch):
    """Evaluation failures fail closed, are recorded, and remain pending."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    def fail_evaluation(_envelope):
        raise RuntimeError("policy backend unavailable")

    monkeypatch.setattr(cp_router_module, "evaluate_action", fail_evaluation)
    resp = _dispatch(client, task_id)

    assert resp.status_code == 403
    assert resp.json()["detail"]["policy_decision"] == "deny"
    assert _task_status(task_id) == "pending"
    decisions = _policy_decisions()
    assert decisions[0]["decision"] == "deny"
    assert decisions[0]["reason"] == "Policy evaluation failed; defaulting to deny."


def _create_pending_approval(client, run_id, task_id, *, action_type="GIT_PUSH"):
    """
    Mark the specified task as awaiting human approval and create a corresponding pending policy decision in the test control plane store.
    
    Parameters:
        action_type (str): The type of action that requires approval (defaults to "GIT_PUSH").
    
    Returns:
        dict: The persisted policy decision record for the pending approval.
    """
    cp_router_module.cp_store.update_task_status(task_id=task_id, status="awaiting_approval")
    return cp_router_module.cp_store.record_policy_decision(
        run_id=run_id,
        task_id=task_id,
        action_type=action_type,
        decision="pending_approval",
        reason="requires human approval",
    )


def _approval_request(task_id, decision_id, *, action_type="GIT_PUSH", expires_at=None):
    """
    Builds a JSON-like approval request payload for tests.
    
    Parameters:
        task_id (str): ID of the task the approval pertains to.
        decision_id (str): ID of the policy decision the approval corresponds to.
        action_type (str, optional): Action type for the approval (defaults to "GIT_PUSH").
        expires_at (int | None, optional): Unix timestamp when the approval expires; if omitted, defaults to now + 300 seconds.
    
    Returns:
        dict: A mapping with keys:
            - "task_id": the provided task_id
            - "decision_id": the provided decision_id
            - "action_type": the provided or default action_type
            - "expires_at": expiration timestamp (int)
            - "note": a short note string ("reviewed")
    """
    return {
        "task_id": task_id,
        "decision_id": decision_id,
        "action_type": action_type,
        "expires_at": expires_at or int(time.time()) + 300,
        "note": "reviewed",
    }


def _human_headers(**overrides):
    """
    Return default HTTP headers that represent a human principal, with optional overrides.
    
    Parameters:
        **overrides: Mapping[str, str]
            Header names and values to merge into and override the defaults.
    
    Returns:
        dict: A mapping of header names to values containing the defaults
        ("X-Principal-ID": "alice", "X-Principal-Type": "human", "X-Trace-ID": "trace-123")
        with any provided overrides applied.
    """
    return {
        "X-Principal-ID": "alice",
        "X-Principal-Type": "human",
        "X-Trace-ID": "trace-123",
        **overrides,
    }


def test_approve_run_requires_authenticated_identity(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)

    resp = client.post(
        f"/v1/runs/{run_id}/approve",
        json=_approval_request(task_id, decision_id),
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "authenticated_principal_required"


def test_approve_run_rejects_mismatched_task(client):
    """
    Verifies that approving a run fails when the provided approval decision does not belong to the task being approved.
    
    Sets up a run with two tasks, records a pending approval linked to the first task, marks the second task as awaiting approval, and posts an approval request referencing the second task but the decision ID for the first; expects an HTTP 409 with detail "approval_decision_mismatch".
    """
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    other_task_id = _create_task(client, run_id, task_type="review").json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)
    cp_router_module.cp_store.update_task_status(
        task_id=other_task_id, status="awaiting_approval"
    )

    resp = client.post(
        f"/v1/runs/{run_id}/approve",
        json=_approval_request(other_task_id, decision_id),
        headers=_human_headers(),
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "approval_decision_mismatch"


def test_approve_run_rejects_duplicate_approval(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)
    payload = _approval_request(task_id, decision_id)

    assert client.post(
        f"/v1/runs/{run_id}/approve", json=payload, headers=_human_headers()
    ).status_code == 200
    resp = client.post(
        f"/v1/runs/{run_id}/approve", json=payload, headers=_human_headers()
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "approval_already_recorded"


def test_approve_run_rejects_expired_approval(client):
    """
    Verify that submitting an approval for a pending decision that has an expired `expires_at` is rejected.
    
    Posts an approval request with `expires_at` set to a past timestamp and asserts the API responds with HTTP 409 and a JSON `detail` of `"approval_expired"`.
    """
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)

    resp = client.post(
        f"/v1/runs/{run_id}/approve",
        json=_approval_request(task_id, decision_id, expires_at=int(time.time()) - 1),
        headers=_human_headers(),
    )

    assert resp.status_code == 409
    assert resp.json()["detail"] == "approval_expired"


def test_approve_run_rejects_agent_principal(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)

    resp = client.post(
        f"/v1/runs/{run_id}/approve",
        json=_approval_request(task_id, decision_id),
        headers=_human_headers(**{"X-Principal-Type": "agent"}),
    )

    assert resp.status_code == 403
    assert resp.json()["detail"] == "human_approver_required"


def test_approve_run_persists_human_approval_and_emits_audit_event(client, caplog):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    decision_id = _create_pending_approval(client, run_id, task_id)

    with caplog.at_level(logging.INFO):
        resp = client.post(
            f"/v1/runs/{run_id}/approve",
            json=_approval_request(task_id, decision_id),
            headers=_human_headers(),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_id"] == decision_id
    assert data["task_id"] == task_id
    assert data["status"] == "dispatched"
    approval = cp_router_module.cp_store.get_approval(approval_id=data["approval_id"])
    assert approval.approver_id == "alice"
    assert approval.decision_id == decision_id
    assert approval.trace_id == "trace-123"
    assert cp_router_module.cp_store.get_task(task_id=task_id)["status"] == "dispatched"
    assert data["approval_id"] in caplog.text
    assert decision_id in caplog.text


def test_complete_task(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    # Dispatch first
    _dispatch(client, task_id)

    # Complete
    resp = client.post(
        f"/v1/tasks/{task_id}/complete",
        json={"outputs": {"pr_url": "https://github.com/org/repo/pull/1"}, "status": "completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


# ─────────────────────────────────────────────────────────
# Tasks — edge cases
# ─────────────────────────────────────────────────────────

def test_create_task_run_not_found(client):
    resp = client.post(
        "/v1/runs/run_doesnotexist/tasks",
        json={"type": "plan", "agent_role": "planner"},
    )
    assert resp.status_code == 404


def test_list_tasks_run_not_found(client):
    resp = client.get("/v1/runs/run_doesnotexist/tasks")
    assert resp.status_code == 404


def test_dispatch_task_not_found(client):
    resp = client.post(
        "/v1/tasks/task_doesnotexist/dispatch",
        json={
            "actor": {"agent_id": "agent_1", "role": "coder"},
            "action_type": "GIT_COMMIT",
        },
    )
    assert resp.status_code == 404


def test_dispatch_already_dispatched_task_returns_409(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    _dispatch(client, task_id)
    resp = _dispatch(client, task_id)
    assert resp.status_code == 409


def test_complete_task_not_found(client):
    resp = client.post(
        "/v1/tasks/task_doesnotexist/complete",
        json={"status": "completed"},
    )
    assert resp.status_code == 404


def test_complete_pending_task_returns_409(client):
    """Cannot complete a task that was never dispatched."""
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]
    resp = client.post(f"/v1/tasks/{task_id}/complete", json={"status": "completed"})
    assert resp.status_code == 409


# ─────────────────────────────────────────────────────────
# Artifacts
# ─────────────────────────────────────────────────────────

def test_list_artifacts_empty(client):
    run_id = _create_run(client).json()["run_id"]
    resp = client.get(f"/v1/runs/{run_id}/artifacts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_artifact_not_found(client):
    resp = client.get("/v1/artifacts/artifact_doesnotexist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "artifact_not_found"


def test_list_artifacts_run_not_found(client):
    resp = client.get("/v1/runs/run_doesnotexist/artifacts")
    assert resp.status_code == 404


def test_artifact_created_via_store_appears_in_list(client, tmp_path):
    """Artifacts created directly on the store appear in the API listing."""
    run_id = _create_run(client).json()["run_id"]

    # Create artifact via store (simulating internal agent output)
    artifact_id = cp_router_module.cp_store.create_artifact(
        run_id=run_id,
        artifact_type="audit_pack",
        content={"plan": "...", "diffs": [], "decisions": []},
    )

    resp = client.get(f"/v1/runs/{run_id}/artifacts")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["artifact_id"] == artifact_id
    assert items[0]["type"] == "audit_pack"

    detail_resp = client.get(f"/v1/artifacts/{artifact_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["content"]["plan"] == "..."


# ─────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────

def test_get_policy_profile_default(client):
    resp = client.get("/v1/policies/default")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_id"] == "default"
    assert "GIT_PUSH" in data["require_approval_for"]
    assert data["deny_action_types"] == []


def test_get_policy_profile_strict(client):
    resp = client.get("/v1/policies/strict")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_id"] == "strict"
    assert "GIT_PUSH" in data["deny_action_types"]


def test_get_policy_profile_not_found(client):
    resp = client.get("/v1/policies/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "policy_profile_not_found"


def test_evaluate_policy_allow(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = client.post(
        "/v1/policies/evaluate",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": task_id,
                "actor": {"agent_id": "agent_1", "role": "coder"},
                "tenant_id": "tenant_1",
                "policy_profile_id": "default",
                "requested_action": {"type": "GIT_COMMIT", "params": {}},
            }
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "allow"
    assert data["policy_profile_id"] == "default"


def test_evaluate_policy_pending_approval(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = client.post(
        "/v1/policies/evaluate",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": task_id,
                "actor": {"agent_id": "agent_1", "role": "coder"},
                "tenant_id": "tenant_1",
                "policy_profile_id": "default",
                "requested_action": {"type": "GIT_PUSH", "params": {}},
            }
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "pending_approval"


def test_evaluate_policy_deny_on_unknown_profile(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = client.post(
        "/v1/policies/evaluate",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": task_id,
                "actor": {"agent_id": "a", "role": "coder"},
                "tenant_id": "t",
                "policy_profile_id": "unknown_profile",
                "requested_action": {"type": "GIT_COMMIT", "params": {}},
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "deny"


def test_evaluate_policy_deny_strict_side_effect(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = client.post(
        "/v1/policies/evaluate",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": task_id,
                "actor": {"agent_id": "a", "role": "coder"},
                "tenant_id": "t",
                "policy_profile_id": "strict",
                "requested_action": {"type": "DEPLOY", "params": {}},
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "deny"


def test_evaluate_policy_permissive_allows_side_effect(client):
    run_id = _create_run(client).json()["run_id"]
    task_id = _create_task(client, run_id).json()["task_id"]

    resp = client.post(
        "/v1/policies/evaluate",
        json={
            "envelope": {
                "run_id": run_id,
                "task_id": task_id,
                "actor": {"agent_id": "a", "role": "coder"},
                "tenant_id": "t",
                "policy_profile_id": "permissive",
                "requested_action": {"type": "DEPLOY", "params": {}},
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json()["decision"] == "allow"


# ─────────────────────────────────────────────────────────
# Unit tests for policy module
# ─────────────────────────────────────────────────────────

from able_to_answer.control_plane.policy import evaluate_action, get_policy_profile, BUILTIN_PROFILES
from able_to_answer.control_plane.models import ActionEnvelope, Actor, RequestedAction, Budget


def _envelope(action_type: str, profile: str = "default") -> ActionEnvelope:
    return ActionEnvelope(
        run_id="run_test",
        task_id="task_test",
        actor=Actor(agent_id="agent_1", role="coder"),
        tenant_id="tenant_1",
        policy_profile_id=profile,
        requested_action=RequestedAction(type=action_type),
    )


def test_policy_get_profile_returns_none_for_unknown():
    assert get_policy_profile("nonexistent") is None


def test_policy_get_profile_returns_builtin():
    for pid in ("default", "strict", "permissive"):
        profile = get_policy_profile(pid)
        assert profile is not None
        assert profile.profile_id == pid


def test_policy_evaluate_unknown_profile_denies():
    decision, reason = evaluate_action(_envelope("GIT_COMMIT", "ghost"))
    from able_to_answer.control_plane.models import PolicyDecision
    assert decision == PolicyDecision.deny
    assert "ghost" in reason


def test_policy_evaluate_non_side_effect_allowed():
    from able_to_answer.control_plane.models import PolicyDecision
    decision, _ = evaluate_action(_envelope("READ_FILE", "default"))
    assert decision == PolicyDecision.allow


def test_policy_evaluate_side_effect_pending_approval_default():
    from able_to_answer.control_plane.models import PolicyDecision
    decision, _ = evaluate_action(_envelope("GIT_PUSH", "default"))
    assert decision == PolicyDecision.pending_approval


def test_policy_evaluate_side_effect_denied_strict():
    from able_to_answer.control_plane.models import PolicyDecision
    decision, _ = evaluate_action(_envelope("DEPLOY", "strict"))
    assert decision == PolicyDecision.deny


def test_policy_evaluate_side_effect_allowed_permissive():
    from able_to_answer.control_plane.models import PolicyDecision
    decision, _ = evaluate_action(_envelope("SECRET_ACCESS", "permissive"))
    assert decision == PolicyDecision.allow


# ─────────────────────────────────────────────────────────
# Unit tests for ControlPlaneStore
# ─────────────────────────────────────────────────────────

from able_to_answer.control_plane.storage import ControlPlaneStore


def test_store_create_and_get_run(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    run_id = store.create_run(tenant_id="t1", goal="test goal")
    assert run_id.startswith("run_")
    row = store.get_run(run_id=run_id)
    assert row is not None
    assert row["goal"] == "test goal"
    assert row["status"] == "pending"


def test_store_get_run_not_found(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    assert store.get_run(run_id="run_doesnotexist") is None


def test_store_update_run_status(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    run_id = store.create_run(tenant_id="t1", goal="g")
    assert store.update_run_status(run_id=run_id, status="cancelled")
    row = store.get_run(run_id=run_id)
    assert row["status"] == "cancelled"


def test_store_update_run_status_missing_run(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    assert not store.update_run_status(run_id="run_missing", status="cancelled")


def test_store_create_and_list_tasks(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    run_id = store.create_run(tenant_id="t1", goal="g")
    task_id = store.create_task(run_id=run_id, task_type="code", agent_role="coder")
    assert task_id.startswith("task_")
    tasks = store.list_tasks(run_id=run_id)
    assert len(tasks) == 1
    assert tasks[0]["id"] == task_id


def test_store_create_artifact_idempotent(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "db.sqlite3"))
    run_id = store.create_run(tenant_id="t1", goal="g")
    content = {"key": "value"}
    a1 = store.create_artifact(run_id=run_id, artifact_type="audit_pack", content=content)
    a2 = store.create_artifact(run_id=run_id, artifact_type="audit_pack", content=content)
    assert a1 == a2  # same content → same id (INSERT OR IGNORE)

