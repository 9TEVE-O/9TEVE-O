"""SQLite-backed storage for the Control Plane (runs, tasks, artifacts, policy decisions)."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Any

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
  archived_at INTEGER,
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
"""


def _now_ts() -> int:
    return int(time.time())


def _make_id(prefix: str, payload: str) -> str:
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


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
            task_columns = {
                row["name"] for row in con.execute("PRAGMA table_info(cp_tasks)").fetchall()
            }
            if "archived_at" not in task_columns:
                con.execute("ALTER TABLE cp_tasks ADD COLUMN archived_at INTEGER")
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

    def list_tasks(self, *, run_id: str, include_archived: bool = False) -> list[sqlite3.Row]:
        with self._connect() as con:
            archived_filter = "" if include_archived else " AND archived_at IS NULL"
            return con.execute(
                f"SELECT * FROM cp_tasks WHERE run_id = ?{archived_filter} ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()

    def archive_code_tasks(self, *, run_id: str, stale_before: int | None = None) -> list[str]:
        """Archive a run's terminal code tasks and optionally unfinished stale code tasks."""
        ts = _now_ts()
        eligibility = "status IN ('completed', 'failed')"
        params: list[Any] = []
        if stale_before is not None:
            eligibility += " OR created_at < ?"
            params.append(stale_before)

        with self._connect() as con:
            rows = con.execute(
                f"""
                SELECT id FROM cp_tasks
                WHERE run_id = ? AND type = 'code' AND archived_at IS NULL AND ({eligibility})
                ORDER BY created_at ASC
                """,
                [run_id, *params],
            ).fetchall()
            task_ids = [row["id"] for row in rows]
            if task_ids:
                placeholders = ", ".join("?" for _ in task_ids)
                con.execute(
                    f"UPDATE cp_tasks SET archived_at = ? WHERE id IN ({placeholders})",
                    [ts, *task_ids],
                )
                con.commit()
        return task_ids

    def list_awaiting_approval_tasks(self, *, run_id: str) -> list[sqlite3.Row]:
        with self._connect() as con:
            return con.execute(
                "SELECT * FROM cp_tasks WHERE run_id = ? AND status = 'awaiting_approval' AND archived_at IS NULL",
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
