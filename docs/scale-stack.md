# JOGO INC. — Scale Stack

> **Operating philosophy and reference architecture for JOGO INC. / STEVEN LEES.**  
> Every layer below is a constraint system, not a preference list. If a choice violates a constraint, it doesn't ship.

---

## Overview

The Scale Stack is the canonical reference architecture for all products and services built under JOGO INC. It defines seven vertical layers — from orchestration down to observability — each with a fixed purpose, a short approved stack, hard constraints, and a named scale vector. Teams pick technologies from within each layer's approved stack; they do not introduce new layers or bypass constraints without an ADR.

---

## Layers

| Layer | Purpose | Stack | Key Constraints | Scale Vector |
|---|---|---|---|---|
| **Orchestration** | Coordinate multi-agent runs, long-running workflows, and scheduled pipelines | n8n · Prefect · GitHub Actions | • Workflow state is durable and resumable<br>• Side-effect steps require a policy gate (see ADR-0001)<br>• Every run emits a `trace_id` | Horizontal — add worker replicas; no shared mutable state between workers |
| **Agents** | Autonomous task execution (code generation, research, ops) | OpenHands · SWE-AF · custom FastAPI agents | • Agents call tools through the Control Plane only<br>• No direct DB or secret access<br>• Output is an immutable artefact | Stateless — agent containers are ephemeral; scale by spawning more |
| **AI** | Foundation models, embeddings, and inference routing | OpenAI · Anthropic · Hugging Face (local) | • All prompts are logged with `request_id`<br>• No PII in prompt context without explicit consent flag<br>• Model selection is config-driven, not hardcoded | Token throughput — route to cheaper/faster model tier under load |
| **Data** | Persistent storage, vector index, and audit log | SQLite (dev/single-tenant) · Postgres (multi-tenant) · pgvector · Mem0 | • Schema migrations are versioned and reversible<br>• Audit table is append-only (`INSERT`, no `UPDATE`/`DELETE`)<br>• `INSERT OR REPLACE` only on explicitly idempotent paths | Read replicas + connection pooling; vector index sharded by tenant |
| **Frontend** | User-facing interfaces and developer dashboards | Next.js · React · Tailwind CSS | • No client-side secrets<br>• CSP headers enforced at the CDN edge<br>• Core Web Vitals LCP < 2.5 s | CDN edge caching; ISR/SSG for static-heavy pages |
| **Security** | Identity, secrets, policy enforcement, and threat modelling | Vault · OWASP guidelines · GitHub Advanced Security | • Secrets are never committed to source (`.env.example` only)<br>• All inbound data is treated as untrusted<br>• Policy PDP failure defaults to *deny* | N/A — security is a cross-cutting constraint, not a scaling dimension |
| **Observability** | Structured logging, distributed tracing, and alerting | OpenTelemetry · Grafana · Loki · GitHub Actions summaries | • Every log line includes `trace_id`, `run_id`, `tenant_id`<br>• No `print()` in application code — use structured `logger`<br>• Alerts fire before users notice | Log volume — sample debug traces under high load; always keep ERROR/WARN |

---

## Eventing Conventions

All asynchronous communication between layers uses a **Pub/Sub event bus** (Google Cloud Pub/Sub in production; local emulator in dev).

### Topic naming

```
{product}.{event}.{version}
```

| Segment | Example | Rule |
|---------|---------|------|
| `product` | `able-to-answer` | Lowercase, hyphenated product slug |
| `event` | `document.ingested` | Dot-separated noun + past-tense verb |
| `version` | `v1` | Increment only on breaking schema changes |

**Full example:** `able-to-answer.document.ingested.v1`

### Envelope

Every event payload wraps the domain data in a standard envelope:

```json
{
  "trace_id": "<uuid>",
  "run_id": "<uuid>",
  "tenant_id": "<slug>",
  "event": "able-to-answer.document.ingested.v1",
  "occurred_at": "<ISO-8601>",
  "payload": { }
}
```

Consumers **must** validate `trace_id`, `run_id`, and `tenant_id` before processing. Unknown fields in `payload` are ignored, not rejected.

---

## The Mandate

These five rules are non-negotiable. They apply to every layer, every team, every pull request.

| # | Rule | Detail |
|---|------|--------|
| 1 | **Audit everything** | Every agent action, data write, and policy decision produces an immutable audit record. No side effect is silent. |
| 2 | **Policy gates before side effects** | `GIT_PUSH`, `DEPLOY`, `SECRET_ACCESS`, `OUTBOUND_NETWORK`, and `PUBLISH_DOCS` require a Control Plane policy evaluation that returns `ALLOW` before execution. A network timeout or PDP error is treated as `DENY`. |
| 3 | **Stateless agents, durable data** | Agent containers carry no runtime state between invocations. All state lives in the Data layer. This makes horizontal scaling trivial and debugging deterministic. |
| 4 | **Secrets never in source** | No credential, token, key, or internal URL is committed to source control. `.env.example` holds placeholder values only. Vault is the single source of truth for secrets at runtime. |
| 5 | **Observability is not optional** | A feature that cannot be traced, measured, and alerted on is not production-ready. `trace_id` propagation and structured logging are requirements, not nice-to-haves. |

---

## Related documents

- [ADR-0001 — Control Plane Design](../ADR/ADR-0001.md)
- [ADR-0002](../ADR/ADR-0002.md)
- [SETUP_PLAN.md](../SETUP_PLAN.md)
