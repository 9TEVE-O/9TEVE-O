# Threat Model — 9TEVE-OS (STRIDE)

> **Status:** Draft v0.1  
> **Scope:** Control Plane API, Agent Runners, Policy Decision Point, Vault Broker, UI

---

## System Overview

```
[User / UI]
   │ OIDC session / API key
   ▼
[Control Plane API]  ─── mTLS ───► [Agent Runners]
   │                                     │
   ├─► [Policy PDP/PEP]                  ├─► [Mem0 Memory]
   ├─► [Telemetry Spine]                 └─► [Flow Engine]
   └─► [Vault Broker]  ─────────────────────► [External: GitHub, LLMs, SaaS]
```

Trust zones (see ADR-0003):
- **Zone A**: User + UI
- **Zone B**: Control Plane (trusted execution boundary)
- **Zone C**: Agent Runners (sandboxed, ephemeral)
- **Zone D**: Governance + Secrets (high-value, restricted)
- **Zone E**: External Systems (untrusted)

---

## STRIDE Analysis

### S — Spoofing

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Agent identity | A malicious process claims to be a trusted agent | Short-lived signed JWT (≤15 min) issued by Control Plane; mTLS between Control Plane and runners |
| Tenant data | Agent reads another tenant's data | `tenant_id` enforced on every DB query; no cross-tenant reads in storage layer |
| Vault tokens | Agent fabricates a Vault request | Agents never hold Vault tokens; Control Plane mediates all secret access |

### T — Tampering

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Audit pack | Attacker modifies a completed artefact | Artefacts are content-addressed (SHA-256); stored immutably with `INSERT OR IGNORE` |
| Action envelope | Agent alters the envelope to bypass policy | Envelope is constructed by the Control Plane, not by the agent |
| Policy profile | Attacker edits a policy profile to allow denied actions | Policy profiles are server-side; modification requires admin credentials + audit log |

### R — Repudiation

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Policy decision | Actor disputes that a decision was made | Every `evaluate_action` call records a `cp_policy_decisions` row with run_id, task_id, decision, reason |
| Secret access | Actor denies accessing a secret | Every Vault request is logged with `{run_id, agent_id, purpose, policy_decision}` |
| Human approval | Approver denies approving a gated task | `approve_run` records `approved_by` identity; tied to audit log entry |

### I — Information Disclosure

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Source code in agent context | Agent leaks code to an external LLM | Agent Runner network: default deny outbound; allowlist per policy profile |
| Vault secrets | Secret value logged accidentally | Agents receive credential references (`CredentialRef`), not raw values |
| Cross-tenant data | Query returns rows from another tenant | All storage queries filter by `tenant_id`; enforced at the store layer |

### D — Denial of Service

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Control Plane API | Flood of `/v1/runs` requests | Rate limiting at the API gateway; budget enforcement per run |
| Policy PDP | Slow policy evaluation degrades all runs | PDP has a 200 ms p95 SLO; decisions are cacheable by (profile_id, action_type) |
| Vault Broker | Vault unavailable | Runs degrade gracefully to "no-secrets" mode; side-effect tasks remain in `awaiting_approval` |

### E — Elevation of Privilege

| Asset | Threat | Mitigation |
|-------|--------|------------|
| Agent role | `coder` agent claims `planner` privileges | Role is embedded in the signed JWT; Control Plane rejects mismatched claims |
| Policy bypass | Agent calls side-effect actions without a policy check | All task dispatches pass through `evaluate_action`; deny is enforced at the HTTP layer (403) |
| Break-glass | Admin agent reads cross-tenant data in an emergency | Explicit break-glass policy required; every break-glass access is logged and alerted |

---

## Residual Risks

1. **Prompt injection via document content**: Agent may ingest a document that contains adversarial instructions. Mitigation: treat all file contents as data (never execute); review agent system prompts.
2. **Supply-chain risk in upstream forks**: SWE-AF / OpenHands / n8n are third-party projects. Mitigation: pin to known-good commits; run dependency scanning in CI.
3. **LLM hallucination generating insecure code**: The coder agent may produce code with security vulnerabilities. Mitigation: reviewer agent + CodeQL in CI + human approval gate before merge.

---

## Out of Scope (MVP)

- OIDC / SAML integration (stubbed with API key)
- mTLS certificate rotation automation
- Formal TLA+ invariant proofs (tracked in ADR-0005)
