"""Control-plane final audit-pack builder."""

from __future__ import annotations

import json
import time
from typing import Any

SENSITIVE_KEY_PARTS = (
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
)

REDACTED = "[REDACTED]"


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive values while preserving structure."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in SENSITIVE_KEY_PARTS):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_value(item)
        return redacted
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


def _json_loads(raw: str | None, fallback: Any) -> Any:
    if raw is None:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _row_dict(row: Any, keys: list[str]) -> dict[str, Any]:
    return {key: row[key] for key in keys}


def build_control_plane_audit_pack(
    *,
    run: Any,
    tasks: list[Any],
    artifacts: list[Any],
    policy_decisions: list[Any],
    approvals: list[Any],
    published_at: int | None = None,
) -> dict[str, Any]:
    """Build the immutable final audit pack for a terminal control-plane run."""
    task_items = []
    tool_invocations = []
    validation_results = []
    final_outcomes = []
    failures = []
    rollbacks = []
    state_transitions = [
        {
            "entity": "run",
            "entity_id": run["id"],
            "status": run["status"],
            "at": run["created_at"],
        }
    ]

    for task in tasks:
        inputs = redact_value(_json_loads(task["inputs_json"], {}))
        outputs = redact_value(_json_loads(task["outputs_json"], {}))
        item = {
            "task_id": task["id"],
            "type": task["type"],
            "agent_role": task["agent_role"],
            "status": task["status"],
            "created_at": task["created_at"],
            "inputs": inputs,
            "outputs": outputs,
        }
        task_items.append(item)
        state_transitions.append(
            {
                "entity": "task",
                "entity_id": task["id"],
                "status": task["status"],
                "at": task["created_at"],
            }
        )
        tool_invocations.append(
            {
                "task_id": task["id"],
                "action_type": inputs.get("action_type") or task["type"],
                "params": inputs,
                "outcome": outputs,
            }
        )
        if "validation" in outputs:
            validation_results.append(
                {"task_id": task["id"], "validation": outputs["validation"]}
            )
        if "validation_results" in outputs:
            validation_results.append(
                {"task_id": task["id"], "validation": outputs["validation_results"]}
            )
        if task["status"] == "failed" or outputs.get("error") or outputs.get("failure"):
            failures.append(
                {"task_id": task["id"], "status": task["status"], "details": outputs}
            )
        if outputs.get("rollback") or outputs.get("rollback_details"):
            rollbacks.append(
                {
                    "task_id": task["id"],
                    "details": outputs.get("rollback")
                    or outputs.get("rollback_details"),
                }
            )
        if outputs:
            final_outcomes.append(
                {"task_id": task["id"], "status": task["status"], "outputs": outputs}
            )

    non_final_artifacts = [a for a in artifacts if a["type"] != "final_audit_pack"]
    artifact_versions = [
        {
            "artifact_id": artifact["id"],
            "type": artifact["type"],
            "content_hash": artifact["content_hash"],
            "created_at": artifact["created_at"],
        }
        for artifact in non_final_artifacts
    ]

    def artifact_records(record_type: str) -> list[dict[str, Any]]:
        return [
            {
                "artifact_id": artifact["id"],
                "content_hash": artifact["content_hash"],
                "created_at": artifact["created_at"],
                "content": redact_value(_json_loads(artifact["content_json"], {})),
            }
            for artifact in non_final_artifacts
            if artifact["type"] == record_type
        ]

    approval_items = [
        {
            "approval_id": approval["id"],
            "run_id": approval["run_id"],
            "task_id": approval["task_id"],
            "action_type": approval["action_type"],
            "decision_id": approval["decision_id"],
            "approver_id": approval["approver_id"],
            "created_at": approval["created_at"],
            "expires_at": approval["expires_at"],
            "note": approval["note"],
            "trace_id": approval["trace_id"],
        }
        for approval in approvals
    ]
    trace_ids = sorted(
        {approval["trace_id"] for approval in approvals if approval["trace_id"]}
    )

    policy_items = [
        _row_dict(
            decision,
            [
                "id",
                "run_id",
                "task_id",
                "created_at",
                "action_type",
                "decision",
                "reason",
            ],
        )
        for decision in policy_decisions
    ]

    stored_tool_invocations = artifact_records("tool_invocation") + artifact_records(
        "tool-invocation"
    )
    runtime_state = artifact_records("runtime_state") + artifact_records(
        "runtime-state"
    )
    evaluations = artifact_records("evaluation")
    deployment_readiness = artifact_records("deployment_readiness") + artifact_records(
        "deployment-readiness"
    )

    return {
        "schema_version": "control-plane-audit-pack.v1",
        "created_at": published_at or int(time.time()),
        "run": {
            "run_id": run["id"],
            "tenant_id": run["tenant_id"],
            "project_id": run["project_id"],
            "status": run["status"],
            "created_at": run["created_at"],
            "policy_profile_id": run["policy_profile_id"],
        },
        "requirement_intent_summary": {
            "goal": run["goal"],
            "inputs": redact_value(_json_loads(run["inputs_json"], {})),
            "repo_refs": _json_loads(run["repo_refs_json"], []),
            "budget": {"tokens": run["budget_tokens"], "time_s": run["budget_time_s"]},
        },
        "selected_artifact_versions": artifact_versions,
        "plan_and_state_transitions": {
            "plan": [
                task for task in task_items if task["type"] in {"plan", "planning"}
            ],
            "state_transitions": state_transitions,
        },
        "redacted_tool_invocations": stored_tool_invocations + tool_invocations,
        "policy_decisions": policy_items,
        "human_approvals": approval_items,
        "validation_results": validation_results,
        "monitoring_trace_ids": trace_ids,
        "runtime_state_records": runtime_state,
        "evaluation_records": evaluations,
        "deployment_readiness_records": deployment_readiness,
        "final_response_or_action_outcome": (
            final_outcomes[-1] if final_outcomes else {"status": run["status"]}
        ),
        "failure_and_rollback_details": {
            "failures": failures,
            "rollbacks": rollbacks,
        },
    }
