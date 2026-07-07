"""Checkpoint-based runtime resumption and scoped memory persistence."""

from __future__ import annotations

from typing import Any

from able_to_answer.control_plane.storage import (
    ControlPlaneStore,
    ExecutionCheckpoint,
    RuntimeRecord,
)


class RuntimePersistence:
    """Small runtime-facing facade over control-plane persistence primitives."""

    def __init__(self, store: ControlPlaneStore) -> None:
        self.store = store

    def checkpoint(
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
        """Persist a redacted execution checkpoint for later resumption."""
        return self.store.create_execution_checkpoint(
            tenant_id=tenant_id,
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
            state=state,
            classification_tags=classification_tags,
            consent_status=consent_status,
            retention_policy=retention_policy,
            expires_at=expires_at,
        )

    def resume(
        self, *, tenant_id: str, run_id: str, task_id: str
    ) -> ExecutionCheckpoint | None:
        """Return the latest unexpired checkpoint within the requested tenant scope."""
        return self.store.resume_from_checkpoint(
            tenant_id=tenant_id, run_id=run_id, task_id=task_id
        )

    def remember_short_term(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        memory: dict[str, Any],
        classification_tags: list[str] | None = None,
        retention_policy: str = "run_scoped",
        expires_at: int | None = None,
    ) -> str:
        """Store redacted run-scoped working memory."""
        return self.store.save_short_term_memory(
            tenant_id=tenant_id,
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
            memory=memory,
            classification_tags=classification_tags,
            consent_status="not_required",
            retention_policy=retention_policy,
            expires_at=expires_at,
        )

    def remember_durable(
        self,
        *,
        tenant_id: str,
        run_id: str,
        task_id: str,
        trace_id: str,
        memory: dict[str, Any],
        classification_tags: list[str] | None = None,
        consent_status: str,
        retention_policy: str = "user_consented",
        expires_at: int | None = None,
    ) -> str:
        """Store redacted durable memory only when explicit consent is present."""
        return self.store.save_durable_memory(
            tenant_id=tenant_id,
            run_id=run_id,
            task_id=task_id,
            trace_id=trace_id,
            memory=memory,
            classification_tags=classification_tags,
            consent_status=consent_status,
            retention_policy=retention_policy,
            expires_at=expires_at,
        )

    def active_working_memory(
        self, *, tenant_id: str, run_id: str, task_id: str | None = None
    ) -> list[RuntimeRecord]:
        """List unexpired tenant-scoped short-term memory."""
        return self.store.list_short_term_memory(
            tenant_id=tenant_id, run_id=run_id, task_id=task_id
        )
