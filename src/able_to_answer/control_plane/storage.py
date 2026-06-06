"""SQLite-backed storage for the Control Plane (runs, tasks, artifacts, policy decisions)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any

from able_to_answer.control_plane.audit_pack import build_control_plane_audit_pack

CP_SCHEMA = """
CREATE TABLE IF NOT EXISTS cp_runs (
  id                TEXT PRIMARY KEY,
  created_at        INTEGER NOT NULL,
  tenant_id         TEXT NOT NULL,
  project_id        TEXT,
  goal              TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'pending',
  policy_profile_id TEXT NOT NULL DEFAULT 'default',
  inputs_json       TEXT NOT NULL DEFAULT '{}',
  repo_refs_json    TEXT NOT NULL DEFAULT '[]',
  budget_tokens     INTEGER,
  budget_time_s     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_cp_runs_tenant ON cp_runs(tenant_id);

CREATE TABLE IF NOT EXISTS cp_tasks (
  id          TEXT PRIMARY KEY,
  run_id      TEXT NOT NULL,
  created_at  INTEGER NOT NULL,
  status      TEXT NOT NULL DEFAULT 'pending',
  type        TEXT NOT NULL,
  agent_role  TEXT,
  inputs_json TEXT NOT NULL DEFAULT '{}',
  outputs_json TEXT,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_cp_tasks_run ON cp_tasks(run_id);

CREATE TABLE IF NOT EXISTS cp_artifacts (
  id           TEXT PRIMARY KEY,
  run_id       TEXT NOT NULL,
  created_at   INTEGER NOT NULL,
  type         TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content_json TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_cp_artifacts_run ON cp_artifacts(run_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cp_final_audit_pack
  ON cp_artifacts(run_id) WHERE type = 'final_audit_pack';

CREATE TABLE IF NOT EXISTS cp_policy_decisions (
  id          TEXT PRIMARY KEY,
  run_id      TEXT NOT NULL,
  task_id     TEXT,
  created_at  INTEGER NOT NULL,
  action_type TEXT NOT NULL,
  decision    TEXT NOT NULL,
  reason      TEXT,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_cp_poldec_run ON cp_policy_decisions(run_id);

CREATE TABLE IF NOT EXISTS cp_approvals (
  id          TEXT PRIMARY KEY,
  run_id      TEXT NOT NULL,
  task_id     TEXT NOT NULL,
  action_type TEXT NOT NULL,
  decision_id TEXT NOT NULL UNIQUE,
  approver_id TEXT NOT NULL,
  created_at  INTEGER NOT NULL,
  expires_at  INTEGER NOT NULL,
  note        TEXT,
  trace_id    TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id),
  FOREIGN KEY(decision_id) REFERENCES cp_policy_decisions(id)
);

CREATE INDEX IF NOT EXISTS idx_cp_approvals_run ON cp_approvals(run_id);
CREATE INDEX IF NOT EXISTS idx_cp_approvals_task ON cp_approvals(task_id);
"""


def _now_ts() -> int:
    return int(time.time())


def _make_id(prefix: str, payload: str) -> str:
    """
    Create a short deterministic identifier by hashing the given payload and prefixing it.
    
    Parameters:
    	prefix (str): String placed before the underscore in the identifier.
    	payload (str): Input string whose SHA-256 digest determines the identifier suffix.
    
    Returns:
    	str: Identifier in the form "<prefix>_<first16hexOfSha256(payload)>".
    """
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


class ApprovalDispatchConflictError(RuntimeError):
    """Raised when an approval cannot dispatch a task from its gated state."""


@dataclass(frozen=True)
class ApprovalRecord:
    """Immutable authorization record for one gated action."""

    approval_id: str
    run_id: str
    task_id: str
    action_type: str
    decision_id: str
    approver_id: str
    timestamp: int
    expiry: int
    note: str | None
    trace_id: str


class ControlPlaneStore:
    """Persistent store for control-plane entities using the same SQLite database."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.executescript(CP_SCHEMA)
            con.commit()

    # ─────────────────────────── Runs ────────────────────────────

    def create_run(
        self,
        *,
        tenant_id: str,
        goal: str,
        project_id: str | None = None,
        inputs: dict[str, Any] | None = None,
        repo_refs: list[str] | None = None,
        policy_profile_id: str = "default",
        budget_tokens: int | None = None,
        budget_time_s: int | None = None,
    ) -> str:
        ts = _now_ts()
        run_id = _make_id("run", f"{tenant_id}:{goal}:{ts}")
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_runs
                (id, created_at, tenant_id, project_id, goal, status, policy_profile_id,
                 inputs_json, repo_refs_json, budget_tokens, budget_time_s)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    ts,
                    tenant_id,
                    project_id,
                    goal,
                    policy_profile_id,
                    json.dumps(inputs or {}),
                    json.dumps(repo_refs or []),
                    budget_tokens,
                    budget_time_s,
                ),
            )
            con.commit()
        return run_id

    def get_run(self, *, run_id: str) -> sqlite3.Row | None:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_runs WHERE id = ?", (run_id,)
            ).fetchone()

    def update_run_status(self, *, run_id: str, status: str) -> bool:
        with self._connect() as con:
            cur = con.execute(
                "UPDATE cp_runs SET status = ? WHERE id = ?", (status, run_id)
            )
            if cur.rowcount > 0 and status in {"completed", "failed", "cancelled"}:
                self._publish_final_audit_pack(con=con, run_id=run_id)
            con.commit()
        return cur.rowcount > 0

    # ─────────────────────────── Tasks ───────────────────────────

    def create_task(
        self,
        *,
        run_id: str,
        task_type: str,
        agent_role: str | None = None,
        inputs: dict[str, Any] | None = None,
    ) -> str:
        ts = _now_ts()
        task_id = _make_id("task", f"{run_id}:{task_type}:{ts}")
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_tasks
                (id, run_id, created_at, status, type, agent_role, inputs_json)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """,
                (task_id, run_id, ts, task_type, agent_role, json.dumps(inputs or {})),
            )
            con.commit()
        return task_id

    def get_task(self, *, task_id: str) -> sqlite3.Row | None:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_tasks WHERE id = ?", (task_id,)
            ).fetchone()

    def update_task_status(
        self,
        *,
        task_id: str,
        status: str,
        outputs: dict[str, Any] | None = None,
    ) -> bool:
        with self._connect() as con:
            if outputs is not None:
                cur = con.execute(
                    "UPDATE cp_tasks SET status = ?, outputs_json = ? WHERE id = ?",
                    (status, json.dumps(outputs), task_id),
                )
            else:
                cur = con.execute(
                    "UPDATE cp_tasks SET status = ? WHERE id = ?", (status, task_id)
                )
            con.commit()
        return cur.rowcount > 0

    def list_tasks(self, *, run_id: str) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_tasks WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()

    def list_awaiting_approval_tasks(self, *, run_id: str) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_tasks WHERE run_id = ? AND status = 'awaiting_approval'",
                (run_id,),
            ).fetchall()

    # ────────────────────────── Artifacts ────────────────────────

    def create_artifact(
        self,
        *,
        run_id: str,
        artifact_type: str,
        content: dict[str, Any],
    ) -> str:
        ts = _now_ts()
        content_json = json.dumps(content, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
        artifact_id = _make_id("artifact", f"{run_id}:{artifact_type}:{content_hash}")
        with self._connect() as con:
            # INSERT OR IGNORE makes create_artifact idempotent: the same
            # content always produces the same artifact_id, so duplicate
            # writes are silently discarded rather than raising a constraint error.
            con.execute(
                """
                INSERT OR IGNORE INTO cp_artifacts
                (id, run_id, created_at, type, content_hash, content_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, run_id, ts, artifact_type, content_hash, content_json),
            )
            con.commit()
        return artifact_id

    def get_artifact(self, *, artifact_id: str) -> sqlite3.Row | None:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()

    def list_artifacts(self, *, run_id: str) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()

    def get_final_audit_pack(self, *, run_id: str) -> sqlite3.Row | None:
        with self._connect() as con:
            return con.execute(
                """
                SELECT * FROM cp_artifacts
                WHERE run_id = ? AND type = 'final_audit_pack'
                ORDER BY created_at ASC LIMIT 1
                """,
                (run_id,),
            ).fetchone()

    # ──────────────────────── Policy Decisions ───────────────────

    def record_policy_decision(
        self,
        *,
        run_id: str,
        task_id: str | None,
        action_type: str,
        decision: str,
        reason: str,
    ) -> str:
        """
        Record a policy decision for a run and return the generated policy-decision id.
        
        Records a decision in the control-plane store's policy decision table. The decision may be associated with a specific task when `task_id` is provided.
        
        Parameters:
            run_id (str): Identifier of the run the decision belongs to.
            task_id (str | None): Identifier of the task this decision pertains to, or `None` if not task-specific.
            action_type (str): The action category the decision addresses (e.g., "dispatch", "approve").
            decision (str): The decision text or outcome.
            reason (str): A human-readable explanation for the decision.
        
        Returns:
            str: The generated policy-decision id (prefixed with "pd_").
        """
        ts = _now_ts()
        pd_id = _make_id("pd", f"{run_id}:{task_id}:{action_type}:{ts}")
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_policy_decisions
                (id, run_id, task_id, created_at, action_type, decision, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pd_id, run_id, task_id, ts, action_type, decision, reason),
            )
            con.commit()
        return pd_id

    def get_policy_decision(self, *, decision_id: str) -> sqlite3.Row | None:
        """
        Retrieve the policy decision row for the given decision id.
        
        Returns:
            sqlite3.Row | None: The matching policy decision row, or `None` if no decision exists with that id.
        """
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_policy_decisions WHERE id = ?", (decision_id,)
            ).fetchone()

    # ────────────────────────── Approvals ─────────────────────────

    def create_approval_and_dispatch(
        self,
        *,
        run_id: str,
        task_id: str,
        action_type: str,
        decision_id: str,
        approver_id: str,
        expires_at: int,
        note: str | None,
        trace_id: str,
    ) -> ApprovalRecord:
        """
        Persist an immutable approval and atomically dispatch the associated gated task.
        
        In a single transaction this inserts an approval record into the approvals table and updates the task's status from "awaiting_approval" to "dispatched". The schema enforces uniqueness of a decision's approval, preventing the same decision from being approved and dispatched multiple times.
        
        Parameters:
            run_id (str): Identifier of the run the approval belongs to.
            task_id (str): Identifier of the gated task to dispatch.
            action_type (str): Action type the approval authorizes.
            decision_id (str): Identifier of the related policy decision.
            approver_id (str): Identifier of the approver.
            expires_at (int): Expiration timestamp for the approval.
            note (str | None): Optional approver note.
            trace_id (str): Correlation trace identifier.
        
        Returns:
            ApprovalRecord: The created approval record.
        
        Raises:
            ApprovalDispatchConflictError: If the task was not transitioned from "awaiting_approval" to "dispatched" (i.e., the update did not affect exactly one row).
        """
        ts = _now_ts()
        approval_id = _make_id(
            "approval", f"{decision_id}:{task_id}:{approver_id}:{trace_id}:{ts}"
        )
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_approvals
                (id, run_id, task_id, action_type, decision_id, approver_id,
                 created_at, expires_at, note, trace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval_id,
                    run_id,
                    task_id,
                    action_type,
                    decision_id,
                    approver_id,
                    ts,
                    expires_at,
                    note,
                    trace_id,
                ),
            )
            dispatched = con.execute(
                """
                UPDATE cp_tasks SET status = 'dispatched'
                WHERE id = ? AND status = 'awaiting_approval'
                """,
                (task_id,),
            )
            if dispatched.rowcount != 1:
                raise ApprovalDispatchConflictError(task_id)
            con.commit()
        return ApprovalRecord(
            approval_id=approval_id,
            run_id=run_id,
            task_id=task_id,
            action_type=action_type,
            decision_id=decision_id,
            approver_id=approver_id,
            timestamp=ts,
            expiry=expires_at,
            note=note,
            trace_id=trace_id,
        )

    def get_approval(self, *, approval_id: str) -> ApprovalRecord | None:
        """
        Fetches the approval record for the given approval id.
        
        Returns:
            ApprovalRecord: The approval record matching `approval_id`, or `None` if no such approval exists.
        """
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM cp_approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        return self._approval_record(row) if row else None

    def get_approval_for_decision(self, *, decision_id: str) -> ApprovalRecord | None:
        """
        Retrieve the approval record associated with a given policy decision id.
        
        Parameters:
            decision_id (str): The policy decision's id to look up.
        
        Returns:
            ApprovalRecord | None: The corresponding ApprovalRecord if one exists, `None` otherwise.
        """
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM cp_approvals WHERE decision_id = ?", (decision_id,)
            ).fetchone()
        return self._approval_record(row) if row else None

    def _publish_final_audit_pack(
        self, *, con: sqlite3.Connection, run_id: str
    ) -> str | None:
        existing = con.execute(
            "SELECT id FROM cp_artifacts WHERE run_id = ? AND type = 'final_audit_pack'",
            (run_id,),
        ).fetchone()
        if existing:
            return existing["id"]

        run = con.execute("SELECT * FROM cp_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return None
        tasks = con.execute(
            "SELECT * FROM cp_tasks WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
        artifacts = con.execute(
            "SELECT * FROM cp_artifacts WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
        policy_decisions = con.execute(
            "SELECT * FROM cp_policy_decisions WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
        approvals = con.execute(
            "SELECT * FROM cp_approvals WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()

        ts = _now_ts()
        content = build_control_plane_audit_pack(
            run=run,
            tasks=tasks,
            artifacts=artifacts,
            policy_decisions=policy_decisions,
            approvals=approvals,
            published_at=ts,
        )
        content_json = json.dumps(content, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
        artifact_id = _make_id("artifact", f"{run_id}:final_audit_pack:{content_hash}")
        con.execute(
            """
            INSERT OR IGNORE INTO cp_artifacts
            (id, run_id, created_at, type, content_hash, content_json)
            VALUES (?, ?, ?, 'final_audit_pack', ?, ?)
            """,
            (artifact_id, run_id, ts, content_hash, content_json),
        )
        row = con.execute(
            "SELECT id FROM cp_artifacts WHERE run_id = ? AND type = 'final_audit_pack'",
            (run_id,),
        ).fetchone()
        return row["id"] if row else artifact_id

    @staticmethod
    def _approval_record(row: sqlite3.Row) -> ApprovalRecord:
        """
        Map a `cp_approvals` database row into an `ApprovalRecord`.
        
        Parameters:
            row (sqlite3.Row): Row from the `cp_approvals` table containing approval columns.
        
        Returns:
            ApprovalRecord: An immutable approval record populated from the row's `id`, `run_id`, `task_id`, `action_type`, `decision_id`, `approver_id`, `created_at` (as `timestamp`), `expires_at` (as `expiry`), `note`, and `trace_id`.
        """
        return ApprovalRecord(
            approval_id=row["id"],
            run_id=row["run_id"],
            task_id=row["task_id"],
            action_type=row["action_type"],
            decision_id=row["decision_id"],
            approver_id=row["approver_id"],
            timestamp=row["created_at"],
            expiry=row["expires_at"],
            note=row["note"],
            trace_id=row["trace_id"],
        )
