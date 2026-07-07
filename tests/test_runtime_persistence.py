from __future__ import annotations

import time

import pytest

from able_to_answer.control_plane.storage import (
    ControlPlaneStore,
    DurableMemoryConsentError,
    TenantScopeError,
)
from able_to_answer.runtime_agent import RuntimePersistence


def _run_and_task(
    store: ControlPlaneStore, *, tenant_id: str = "tenant_a"
) -> tuple[str, str]:
    run_id = store.create_run(
        tenant_id=tenant_id, goal=f"runtime {tenant_id} {time.time_ns()}"
    )
    task_id = store.create_task(run_id=run_id, task_type="runtime")
    return run_id, task_id


def test_resume_returns_latest_unexpired_checkpoint(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_id, task_id = _run_and_task(store)

    runtime.checkpoint(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_1",
        state={"step": 1},
    )
    runtime.checkpoint(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_2",
        state={"step": 2},
    )

    resumed = runtime.resume(tenant_id="tenant_a", run_id=run_id, task_id=task_id)

    assert resumed is not None
    assert resumed.sequence == 2
    assert resumed.payload == {"step": 2}
    assert resumed.tenant_id == "tenant_a"


def test_cross_tenant_resume_rejected(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_id, task_id = _run_and_task(store, tenant_id="tenant_a")
    runtime.checkpoint(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_1",
        state={"step": 1},
    )

    with pytest.raises(TenantScopeError):
        runtime.resume(tenant_id="tenant_b", run_id=run_id, task_id=task_id)


def test_expired_memory_is_excluded_and_purgeable(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_id, task_id = _run_and_task(store)
    now = int(time.time())

    runtime.remember_short_term(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_expired",
        memory={"note": "old"},
        expires_at=now - 1,
    )
    runtime.remember_short_term(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_active",
        memory={"note": "active"},
        expires_at=now + 3600,
    )

    active = runtime.active_working_memory(
        tenant_id="tenant_a", run_id=run_id, task_id=task_id
    )

    assert [record.payload for record in active] == [{"note": "active"}]
    assert store.purge_expired_runtime_state(now=now) == 1


def test_durable_memory_requires_explicit_consent(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_id, task_id = _run_and_task(store)

    with pytest.raises(DurableMemoryConsentError):
        runtime.remember_durable(
            tenant_id="tenant_a",
            run_id=run_id,
            task_id=task_id,
            trace_id="trace_no_consent",
            memory={"preference": "concise answers"},
            consent_status="not_required",
        )

    record_id = runtime.remember_durable(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_consented",
        memory={"preference": "concise answers"},
        consent_status="explicit_consented",
    )

    assert record_id.startswith("dm_")
    durable = store.list_durable_memory(tenant_id="tenant_a")
    assert len(durable) == 1
    assert durable[0].consent_status == "explicit_consented"


def test_secret_redaction_and_tool_payload_hash_only(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_id, task_id = _run_and_task(store)

    runtime.checkpoint(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_secret",
        state={"headers": {"Authorization": "Bearer super-secret-token"}, "safe": "ok"},
    )
    tool_id = store.record_tool_result_metadata(
        tenant_id="tenant_a",
        run_id=run_id,
        task_id=task_id,
        trace_id="trace_tool",
        tool_name="search",
        status="ok",
        payload={"unrestricted": "payload", "token": "raw-token"},
        metadata={"summary": "search returned 2 rows", "api_key": "raw-key"},
    )

    resumed = runtime.resume(tenant_id="tenant_a", run_id=run_id, task_id=task_id)
    assert resumed is not None
    assert resumed.redaction_status == "redacted"
    assert resumed.payload["headers"]["Authorization"] == "[REDACTED]"

    with store._connect() as con:
        row = con.execute(
            "SELECT * FROM cp_tool_result_metadata WHERE id = ?",
            (tool_id,),
        ).fetchone()
    row_values = " ".join(str(row[key]) for key in row.keys())
    assert row["payload_hash"]
    assert "unrestricted" not in row.keys()
    assert "raw-token" not in row_values
    assert "raw-key" not in row["metadata_json"]
    assert "[REDACTED]" in row["metadata_json"]


def test_delete_tenant_runtime_state_is_scoped(tmp_path):
    store = ControlPlaneStore(str(tmp_path / "runtime.sqlite3"))
    runtime = RuntimePersistence(store)
    run_a, task_a = _run_and_task(store, tenant_id="tenant_a")
    run_b, task_b = _run_and_task(store, tenant_id="tenant_b")
    runtime.checkpoint(
        tenant_id="tenant_a",
        run_id=run_a,
        task_id=task_a,
        trace_id="ta",
        state={"a": 1},
    )
    runtime.checkpoint(
        tenant_id="tenant_b",
        run_id=run_b,
        task_id=task_b,
        trace_id="tb",
        state={"b": 1},
    )

    assert store.delete_tenant_runtime_state(tenant_id="tenant_a") == 1

    assert runtime.resume(tenant_id="tenant_a", run_id=run_a, task_id=task_a) is None
    assert (
        runtime.resume(tenant_id="tenant_b", run_id=run_b, task_id=task_b) is not None
    )
