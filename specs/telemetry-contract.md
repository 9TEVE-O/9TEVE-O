# Telemetry Contract

> **Status:** Draft v0.1 — 9TEVE-OS Control Plane

## Overview

Every component in 9TEVE-OS emits structured telemetry events. This document defines the canonical fields, log levels, and trace correlation strategy.

## Structured Log Format

All log lines are JSON-encoded with the following mandatory fields:

| Field          | Type    | Description                                           |
|----------------|---------|-------------------------------------------------------|
| `timestamp`    | string  | ISO 8601 UTC, e.g. `2026-03-03T08:59:00.000Z`        |
| `level`        | string  | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`  |
| `service`      | string  | Emitting service, e.g. `control-plane`, `agent-runner`|
| `trace_id`     | string  | W3C Trace Context trace ID                            |
| `span_id`      | string  | W3C Trace Context span ID                             |
| `tenant_id`    | string  | Tenant / workspace boundary                           |
| `run_id`       | string  | Run identifier (present when inside a run context)    |
| `task_id`      | string  | Task identifier (present when inside a task context)  |
| `message`      | string  | Human-readable log message                            |
| `data`         | object  | Arbitrary structured key-value payload                |

### Example

```json
{
  "timestamp": "2026-03-03T08:59:00.000Z",
  "level": "INFO",
  "service": "control-plane",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "tenant_id": "org-9teve-o",
  "run_id": "run_a1b2c3d4e5f6a7b8",
  "task_id": "task_b1c2d3e4f5a6b7c8",
  "message": "task_dispatched",
  "data": {
    "action_type": "GIT_COMMIT",
    "policy_decision": "allow"
  }
}
```

## Key Events

| Event                | Level   | Emitted by        | Description                                       |
|----------------------|---------|-------------------|---------------------------------------------------|
| `run_created`        | INFO    | control-plane     | A new run was accepted                            |
| `run_cancelled`      | INFO    | control-plane     | A run was cancelled by operator                   |
| `run_approved`       | INFO    | control-plane     | Gated tasks were approved by a human              |
| `task_dispatched`    | INFO    | control-plane     | A task was dispatched (includes policy decision)  |
| `task_completed`     | INFO    | control-plane     | A task reached a terminal state                   |
| `policy_decision`    | INFO    | policy-pdp        | A policy evaluation result was recorded           |
| `policy_denied`      | WARNING | policy-pdp        | An action was denied by the policy profile        |
| `secret_accessed`    | WARNING | vault-broker      | A secret was retrieved (audit trail)              |
| `agent_error`        | ERROR   | agent-runner      | An agent raised an unhandled exception            |

## SLO Targets

| Metric                       | Target            |
|------------------------------|-------------------|
| Control Plane API p99        | < 500 ms          |
| Policy decision p95          | < 200 ms          |
| Dispatch latency p95         | < 2 s             |
| Log ingestion lag            | < 5 s             |

## Trace Propagation

- All inbound HTTP requests to the Control Plane must carry W3C `traceparent` headers.
- The `trace_id` is extracted and forwarded to all downstream calls (agent runners, Vault, LLM APIs).
- If no `traceparent` is present, the Control Plane generates a new one.

## Retention

| Log class         | Retention |
|-------------------|-----------|
| Audit decisions   | 7 years   |
| Run / task logs   | 90 days   |
| Debug traces      | 7 days    |
