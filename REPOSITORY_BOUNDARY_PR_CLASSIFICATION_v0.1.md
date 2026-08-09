# REPOSITORY_BOUNDARY_PR_CLASSIFICATION_v0.1

**Status:** CLASSIFICATION COMPLETE — NO PR STATE CHANGES AUTHORISED  
**Repository:** `9TEVE-O/9TEVE-O`  
**Parent:** `REPOSITORY_BOUNDARY_MIGRATION_v0.1.md`  
**Frozen migration source:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Classification date:** 2026-08-09

## Purpose

Classify every open pull request that remains attached to `9TEVE-O/9TEVE-O` against the frozen repository-boundary decision before any migration, merge, closure, or retargeting action.

Allowed classifications:

- `RETAIN` — remains valid work for the profile/control repository.
- `RETARGET` — still-valid work belongs in one of the extracted destination repositories.
- `SUPERSEDE` — useful intent or changes are already represented by current repository state or later work; preserve history but do not carry the PR forward as active work.
- `CLOSE` — work is outside the declared repository boundary and should not be carried forward unless explicitly reactivated.

This document records classification only. It does not merge, close, retarget, edit, or comment on any pull request.

## Open PR inventory

Five open PRs were identified. Four were returned by the normal open-PR search. PR #80 is bot-authored and remained open even though it was omitted from that result, so it is included explicitly.

| PR | Title | Primary ownership | Classification | Reason |
|---:|---|---|---|---|
| #86 | Add AI helpers, portfolio data types, analytics, and update ESLint/.gitignore | PORTFOLIO | SUPERSEDE | The portfolio AI contracts/helpers represented by the PR are already present on current `main` (including `lib/ai-contracts.ts`). Migration should carry the current frozen tree, not revive an older divergent PR. |
| #84 | Fix review-blocking settings validation tests | ABLE_TO_ANSWER | SUPERSEDE | The PR currently has an empty patch against its base branch and targets `copilot/update-all-repositories`, not `main`. Its repair intent is already represented by later/current Able to Answer state. |
| #80 | CodeRabbit Generated Unit Tests: Add unit tests for PR changes | ABLE_TO_ANSWER | SUPERSEDE | Test-only generated work from an older branch. Equivalent settings-validation coverage is already present in current tests, including validation-order coverage. Do not make this old bot branch authoritative during extraction. |
| #72 | Add Safe Intake Codex task brief | OUTSIDE CURRENT BOUNDARY | CLOSE | Adds a new top-level `10_TOOLS_MCP/SAFE_INTAKE_CODEX_SETUP/` tree that is absent from the frozen source inventory and is not assigned to PROFILE, PORTFOLIO, ABLE_TO_ANSWER, or EVIDENCE_AUDITOR. Carrying it forward would reopen an unrelated repository boundary. |
| #60 | Policy-evaluated task dispatch with envelope/shorthand support and tests | ABLE_TO_ANSWER | SUPERSEDE | The policy-gated dispatch model and tests represented by this PR are already present in current `main`. Extraction should preserve current Able to Answer state instead of carrying the old PR forward. |

## Classification totals

| Classification | Count |
|---|---:|
| RETAIN | 0 |
| RETARGET | 0 |
| SUPERSEDE | 4 |
| CLOSE | 1 |
| **Total** | **5** |

## Evidence notes

- PR #84 returns no changed files / no patch against its current base.
- Current `main` contains the policy-gated dispatch validation language and tests associated with PR #60.
- Current `main` contains the portfolio AI contract symbols associated with PR #86.
- Current `main` contains settings validation-order test coverage overlapping PR #80.
- PR #72 proposes a top-level tree that does not exist in the frozen 30-item migration inventory.

## Operational consequence

No open PR needs to be merged before repository extraction.

The migration source remains the frozen current-tree state, not any open PR branch. PR history can be retained as historical provenance, but none of these branches should become the migration authority.

## Gate status

PR classification: **PASSED**.  
PR state mutation: **NOT PERFORMED**.  
Repository extraction: **STILL BLOCKED** pending Evidence Auditor ownership resolution.

## Next gated action

Resolve the Evidence Auditor ownership boundary. Determine which implementation is authoritative among:

- `ai-workflow-evidence-auditor/` standalone project;
- root `lib/evidence-auditor/` and related tests;
- root `fixtures/evidence-auditor/`;
- `scripts/audit-evidence.ts`;
- `docs/evidence-auditor.md`;
- root environment/package integration.

Produce one explicit decision: `STANDALONE REPOSITORY`, `PORTFOLIO-OWNED CAPABILITY`, `ABLE_TO_ANSWER-OWNED CAPABILITY`, or `ARCHIVE/REMOVE DUPLICATE`. Do not extract files until that decision is recorded.