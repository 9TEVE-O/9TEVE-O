"""SQLite-backed storage for the Control Plane (runs, tasks, artifacts, policy decisions)."""

from __future__ import annotations

import hashlib
import json
import re
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

# Runtime checkpoint and memory persistence shared metadata columns. Each table keeps
# tenant/run/task/trace scope so recovery, deletion, and retention decisions can be
# made without inspecting record payloads.
RUNTIME_SCHEMA = """
CREATE TABLE IF NOT EXISTS cp_execution_checkpoints (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  sequence            INTEGER NOT NULL,
  state_json          TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_exec_ckpt_scope ON cp_execution_checkpoints(tenant_id, run_id, task_id, sequence DESC);
CREATE INDEX IF NOT EXISTS idx_cp_exec_ckpt_expiry ON cp_execution_checkpoints(expires_at);

CREATE TABLE IF NOT EXISTS cp_conversation_state (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  state_json          TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_conv_state_scope ON cp_conversation_state(tenant_id, run_id, task_id);
CREATE INDEX IF NOT EXISTS idx_cp_conv_state_expiry ON cp_conversation_state(expires_at);

CREATE TABLE IF NOT EXISTS cp_tool_result_metadata (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  tool_name           TEXT NOT NULL,
  status              TEXT NOT NULL,
  payload_hash        TEXT NOT NULL,
  metadata_json       TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_tool_meta_scope ON cp_tool_result_metadata(tenant_id, run_id, task_id);
CREATE INDEX IF NOT EXISTS idx_cp_tool_meta_expiry ON cp_tool_result_metadata(expires_at);

CREATE TABLE IF NOT EXISTS cp_short_term_memory (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  memory_json         TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_st_memory_scope ON cp_short_term_memory(tenant_id, run_id, task_id);
CREATE INDEX IF NOT EXISTS idx_cp_st_memory_expiry ON cp_short_term_memory(expires_at);

CREATE TABLE IF NOT EXISTS cp_durable_memory (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  memory_json         TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_durable_memory_tenant ON cp_durable_memory(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cp_durable_memory_expiry ON cp_durable_memory(expires_at);

CREATE TABLE IF NOT EXISTS cp_artifact_references (
  id                  TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  run_id              TEXT NOT NULL,
  task_id             TEXT NOT NULL,
  trace_id            TEXT NOT NULL,
  classification_tags_json TEXT NOT NULL DEFAULT '[]',
  consent_status      TEXT NOT NULL,
  retention_policy    TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  expires_at          INTEGER,
  redaction_status    TEXT NOT NULL,
  artifact_uri        TEXT NOT NULL,
  artifact_type       TEXT NOT NULL,
  content_hash        TEXT,
  metadata_json       TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY(run_id) REFERENCES cp_runs(id),
  FOREIGN KEY(task_id) REFERENCES cp_tasks(id)
);
CREATE INDEX IF NOT EXISTS idx_cp_artifact_ref_scope ON cp_artifact_references(tenant_id, run_id, task_id);
CREATE INDEX IF NOT EXISTS idx_cp_artifact_ref_expiry ON cp_artifact_references(expires_at);
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


_SECRET_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
}
_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)[^\s,;}]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[^\s,;}]+"),
)
_RUNTIME_TABLES = (
    "cp_execution_checkpoints",
    "cp_conversation_state",
    "cp_tool_result_metadata",
    "cp_short_term_memory",
    "cp_durable_memory",
    "cp_artifact_references",
)


class TenantScopeError(PermissionError):
    """Raised when a runtime record crosses a run or tenant boundary."""


class DurableMemoryConsentError(ValueError):
    """Raised when durable memory is written without explicit consent."""


@dataclass(frozen=True)
class RuntimeRecord:
    """Common persisted runtime metadata plus a redacted record payload."""

    record_id: str
    tenant_id: str
    run_id: str
    task_id: str
    trace_id: str
    classification_tags: list[str]
    consent_status: str
    retention_policy: str
    created_at: int
    expires_at: int | None
    redaction_status: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ExecutionCheckpoint(RuntimeRecord):
    """A resumable runtime execution snapshot."""

    sequence: int


def _redact_string(value: str) -> tuple[str, bool]:
    redacted = value
    changed = False
    for pattern in _SECRET_PATTERNS:
        updated = pattern.sub(r"\1[REDACTED]", redacted)
        changed = changed or updated != redacted
        redacted = updated
    return redacted, changed


def _redact_value(value: Any) -> tuple[Any, bool]:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        changed = False
        for key, item in value.items():
            if key.lower().replace("-", "_") in _SECRET_KEYS:
                redacted[key] = "[REDACTED]"
                changed = True
                continue
            redacted_item, item_changed = _redact_value(item)
            redacted[key] = redacted_item
            changed = changed or item_changed
        return redacted, changed
    if isinstance(value, list):
        items = []
        changed = False
        for item in value:
            redacted_item, item_changed = _redact_value(item)
            items.append(redacted_item)
            changed = changed or item_changed
        return items, changed
    if isinstance(value, str):
        return _redact_string(value)
    return value, False


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _json_loads(value: str) -> Any:
    return json.loads(value) if value else None


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
            con.executescript(RUNTIME_SCHEMA)
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

    # ───────────────── Runtime Checkpoints and Memory ─────────────

    def _assert_runtime_scope(
        self, *, tenant_id: str, run_id: str, task_id: str
    ) -> None:
        run = self.get_run(run_id=run_id)
        task = self.get_task(task_id=task_id)
        if (
            not run
            or not task
            or run["tenant_id"] != tenant_id
            or task["run_id"] != run_id
        ):
            raise TenantScopeError("runtime_scope_mismatch")

    @staticmethod
    def _is_unexpired_clause(now: int) -> str:
        return "(expires_at IS NULL OR expires_at > %d)" % now

    def create_execution_checkpoint(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        state: dict[str, Any],
        sequence: int | None = None,
        classification_tags: list[str] | None = None,
        consent_status: str = "not_required",
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        self._assert_runtime_scope(tenant_id=tenant_id, run_id=run_id, task_id=task_id)
        ts = _now_ts()
        redacted_state, changed = _redact_value(state)
        redaction_status = "redacted" if changed else "clean"
        with self._connect() as con:
            if sequence is None:
                row = con.execute(
                    """
                    SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence
                    FROM cp_execution_checkpoints
                    WHERE tenant_id = ? AND run_id = ? AND task_id = ?
                    """,
                    (tenant_id, run_id, task_id),
                ).fetchone()
                sequence = int(row["next_sequence"])
            checkpoint_id = _make_id(
                "ckpt", f"{tenant_id}:{run_id}:{task_id}:{trace_id}:{sequence}:{ts}"
            )
            con.execute(
                """
                INSERT INTO cp_execution_checkpoints
                (id, tenant_id, run_id, task_id, trace_id, classification_tags_json,
                 consent_status, retention_policy, created_at, expires_at,
                 redaction_status, sequence, state_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint_id,
                    tenant_id,
                    run_id,
                    task_id,
                    trace_id,
                    _json_dumps(classification_tags or []),
                    consent_status,
                    retention_policy,
                    ts,
                    expires_at,
                    redaction_status,
                    sequence,
                    _json_dumps(redacted_state),
                ),
            )
            con.commit()
        return checkpoint_id

    def resume_from_checkpoint(
        self, *, tenant_id: str, run_id: str, task_id: str
    ) -> ExecutionCheckpoint | None:
        self._assert_runtime_scope(tenant_id=tenant_id, run_id=run_id, task_id=task_id)
        now = _now_ts()
        with self._connect() as con:
            row = con.execute(
                f"""
                SELECT * FROM cp_execution_checkpoints
                WHERE tenant_id = ? AND run_id = ? AND task_id = ?
                  AND {self._is_unexpired_clause(now)}
                ORDER BY sequence DESC, created_at DESC
                LIMIT 1
                """,
                (tenant_id, run_id, task_id),
            ).fetchone()
        return self._checkpoint_record(row) if row else None

    def save_conversation_state(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        state: dict[str, Any],
        classification_tags: list[str] | None = None,
        consent_status: str = "not_required",
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        return self._insert_json_runtime_record(
            table="cp_conversation_state",
            prefix="conv",
            json_column="state_json",
            tenant_id=tenant_id,
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
            payload=state,
            classification_tags=classification_tags,
            consent_status=consent_status,
            retention_policy=retention_policy,
            expires_at=expires_at,
        )

    def record_tool_result_metadata(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        tool_name: str,
        status: str,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        classification_tags: list[str] | None = None,
        consent_status: str = "not_required",
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        self._assert_runtime_scope(tenant_id=tenant_id, run_id=run_id, task_id=task_id)
        ts = _now_ts()
        redacted_metadata, changed = _redact_value(metadata or {})
        payload_hash = hashlib.sha256(_json_dumps(payload).encode("utf-8")).hexdigest()
        record_id = _make_id(
            "toolmeta",
            f"{tenant_id}:{run_id}:{task_id}:{tool_name}:{payload_hash}:{ts}",
        )
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_tool_result_metadata
                (id, tenant_id, run_id, task_id, trace_id, classification_tags_json,
                 consent_status, retention_policy, created_at, expires_at,
                 redaction_status, tool_name, status, payload_hash, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    tenant_id,
                    run_id,
                    task_id,
                    trace_id,
                    _json_dumps(classification_tags or []),
                    consent_status,
                    retention_policy,
                    ts,
                    expires_at,
                    "redacted" if changed else "clean",
                    tool_name,
                    status,
                    payload_hash,
                    _json_dumps(redacted_metadata),
                ),
            )
            con.commit()
        return record_id

    def save_short_term_memory(self, **kwargs: Any) -> str:
        return self._insert_json_runtime_record(
            table="cp_short_term_memory",
            prefix="stm",
            json_column="memory_json",
            **kwargs,
        )

    def save_durable_memory(self, **kwargs: Any) -> str:
        if kwargs.get("consent_status") != "explicit_consented":
            raise DurableMemoryConsentError("durable_memory_requires_explicit_consent")
        return self._insert_json_runtime_record(
            table="cp_durable_memory", prefix="dm", json_column="memory_json", **kwargs
        )

    def save_artifact_reference(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        artifact_uri: str,
        artifact_type: str,
        content_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
        classification_tags: list[str] | None = None,
        consent_status: str = "not_required",
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        self._assert_runtime_scope(tenant_id=tenant_id, run_id=run_id, task_id=task_id)
        ts = _now_ts()
        redacted_metadata, changed = _redact_value(metadata or {})
        metadata_hash = hashlib.sha256(
            _json_dumps(redacted_metadata).encode("utf-8")
        ).hexdigest()
        record_id = _make_id(
            "artref",
            f"{tenant_id}:{run_id}:{task_id}:{artifact_uri}:{content_hash}:{metadata_hash}:{ts}",
        )
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO cp_artifact_references
                (id, tenant_id, run_id, task_id, trace_id, classification_tags_json,
                 consent_status, retention_policy, created_at, expires_at,
                 redaction_status, artifact_uri, artifact_type, content_hash, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    tenant_id,
                    run_id,
                    task_id,
                    trace_id,
                    _json_dumps(classification_tags or []),
                    consent_status,
                    retention_policy,
                    ts,
                    expires_at,
                    "redacted" if changed else "clean",
                    artifact_uri,
                    artifact_type,
                    content_hash,
                    _json_dumps(redacted_metadata),
                ),
            )
            con.commit()
        return record_id

    def list_short_term_memory(
        self, *, tenant_id: str, run_id: str, task_id: str | None = None
    ) -> list[RuntimeRecord]:
        return self._list_json_runtime_records(
            table="cp_short_term_memory",
            json_column="memory_json",
            tenant_id=tenant_id,
            run_id=run_id,
            task_id=task_id,
        )

    def list_durable_memory(self, *, tenant_id: str) -> list[RuntimeRecord]:
        return self._list_json_runtime_records(
            table="cp_durable_memory",
            json_column="memory_json",
            tenant_id=tenant_id,
            run_id=None,
            task_id=None,
        )

    def delete_tenant_runtime_state(self, *, tenant_id: str) -> int:
        deleted = 0
        with self._connect() as con:
            for table in _RUNTIME_TABLES:
                cur = con.execute(
                    f"DELETE FROM {table} WHERE tenant_id = ?", (tenant_id,)
                )
                deleted += cur.rowcount
            con.commit()
        return deleted

    def purge_expired_runtime_state(self, *, now: int | None = None) -> int:
        cutoff = _now_ts() if now is None else now
        deleted = 0
        with self._connect() as con:
            for table in _RUNTIME_TABLES:
                cur = con.execute(
                    f"DELETE FROM {table} WHERE expires_at IS NOT NULL AND expires_at <= ?",
                    (cutoff,),
                )
                deleted += cur.rowcount
            con.commit()
        return deleted

    def _insert_json_runtime_record(
        self,
        *,
        table: str,
        prefix: str,
        json_column: str,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        payload: dict[str, Any] | None = None,
        memory: dict[str, Any] | None = None,
        classification_tags: list[str] | None = None,
        consent_status: str = "not_required",
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        self._assert_runtime_scope(tenant_id=tenant_id, run_id=run_id, task_id=task_id)
        ts = _now_ts()
        value = payload if payload is not None else memory
        redacted_value, changed = _redact_value(value or {})
        payload_hash = hashlib.sha256(
            _json_dumps(redacted_value).encode("utf-8")
        ).hexdigest()
        record_id = _make_id(
            prefix,
            f"{tenant_id}:{run_id}:{task_id}:{trace_id}:{table}:{payload_hash}:{ts}",
        )
        with self._connect() as con:
            con.execute(
                f"""
                INSERT INTO {table}
                (id, tenant_id, run_id, task_id, trace_id, classification_tags_json,
                 consent_status, retention_policy, created_at, expires_at,
                 redaction_status, {json_column})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    tenant_id,
                    run_id,
                    task_id,
                    trace_id,
                    _json_dumps(classification_tags or []),
                    consent_status,
                    retention_policy,
                    ts,
                    expires_at,
                    "redacted" if changed else "clean",
                    _json_dumps(redacted_value),
                ),
            )
            con.commit()
        return record_id

    def _list_json_runtime_records(
        self,
        *,
        table: str,
        json_column: str,
        tenant_id: str,
        run_id: str | None,
        task_id: str | None,
    ) -> list[RuntimeRecord]:
        now = _now_ts()
        predicates = ["tenant_id = ?", self._is_unexpired_clause(now)]
        params: list[Any] = [tenant_id]
        if run_id is not None:
            predicates.append("run_id = ?")
            params.append(run_id)
        if task_id is not None:
            predicates.append("task_id = ?")
            params.append(task_id)
        with self._connect() as con:
            rows = con.execute(
                f"SELECT * FROM {table} WHERE {' AND '.join(predicates)} ORDER BY created_at ASC",
                params,
            ).fetchall()
        return [self._runtime_record(row, json_column=json_column) for row in rows]

    @staticmethod
    def _runtime_record(row: sqlite3.Row, *, json_column: str) -> RuntimeRecord:
        return RuntimeRecord(
            record_id=row["id"],
            tenant_id=row["tenant_id"],
            run_id=row["run_id"],
            task_id=row["task_id"],
            trace_id=row["trace_id"],
            classification_tags=_json_loads(row["classification_tags_json"]),
            consent_status=row["consent_status"],
            retention_policy=row["retention_policy"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            redaction_status=row["redaction_status"],
            payload=_json_loads(row[json_column]),
        )

    @staticmethod
    def _checkpoint_record(row: sqlite3.Row) -> ExecutionCheckpoint:
        base = ControlPlaneStore._runtime_record(row, json_column="state_json")
        return ExecutionCheckpoint(**base.__dict__, sequence=row["sequence"])

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
