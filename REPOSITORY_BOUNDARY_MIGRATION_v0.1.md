# REPOSITORY_BOUNDARY_MIGRATION_v0.1

**Status:** INVENTORY COMPLETE — NO MIGRATION EXECUTION AUTHORISED  
**Repository:** `9TEVE-O/9TEVE-O`  
**Source branch:** `main`  
**Frozen source commit:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Source commit date:** 2026-08-03  
**Inventory date:** 2026-08-09

## Purpose

Freeze the current top-level repository boundary before any files are moved, deleted, extracted, or redesigned.

This inventory assigns every top-level item in the frozen source tree to exactly one of:

- `PROFILE`
- `PORTFOLIO`
- `ABLE_TO_ANSWER`
- `EVIDENCE_AUDITOR / DECISION REQUIRED`
- `ARCHIVE/REMOVE`

The classification is an ownership map, not permission to execute the migration.

## Controlling boundary

- `9TEVE-O/9TEVE-O` is the public profile/control repository.
- `evidence-first-portfolio` is the intended owner of the Next.js/TypeScript portfolio application.
- `able-to-answer` is the intended owner of the Python/FastAPI document-intelligence system.
- Evidence Auditor ownership remains unresolved.
- No application redesign, feature work, or behaviour change is authorised by this inventory.
- No source item may be moved or deleted until the inventory and mixed-ownership exceptions below have been reviewed.

## Frozen top-level inventory

| # | Top-level item | Type | Classification | Migration note |
|---:|---|---|---|---|
| 1 | `.env.example` | file | EVIDENCE_AUDITOR / DECISION REQUIRED | Mixed environment contract. Contains Able to Answer settings plus Evidence Auditor variables. Do not move wholesale; reconstruct destination-specific examples after ownership is resolved. |
| 2 | `.github/` | directory | PROFILE | Retain the repository-level control container in the profile/control repo, but split internal workflows before cleanup. Python CI belongs with Able to Answer; profile/control automation stays only if still justified. |
| 3 | `.gitignore` | file | PROFILE | Retain a minimal profile/control ignore file. Destination repositories must receive their own stack-specific ignore rules; do not copy the current mixed file blindly. |
| 4 | `ADR/` | directory | ARCHIVE/REMOVE | ADRs describe the earlier `9TEVE-OS` control-plane architecture rather than the new repository boundary. Preserve as archival reference if needed; do not treat as current authority. |
| 5 | `AGENTS.md` | file | ABLE_TO_ANSWER | Explicitly documents the Able to Answer FastAPI/SQLite service and its runtime/test instructions. |
| 6 | `CLAUDE.md` | file | ABLE_TO_ANSWER | Explicit Able to Answer architecture, commands, conventions, test requirements, and security rules. |
| 7 | `FORKS_INVENTORY.md` | file | PROFILE | Auto-generated cross-repository fork/control inventory. Fits the control side of the profile/control repository, subject to later pruning. |
| 8 | `Makefile` | file | ABLE_TO_ANSWER | Python service run/test commands. |
| 9 | `README.md` | file | PROFILE | GitHub profile README and public professional landing content. |
| 10 | `SETUP_PLAN.md` | file | ARCHIVE/REMOVE | Stale March 2026 setup plan. Archive or remove from active authority; do not carry forward as current plan. |
| 11 | `ai-workflow-evidence-auditor/` | directory | EVIDENCE_AUDITOR / DECISION REQUIRED | Standalone Evidence Auditor subproject with its own package, source, tests, fixtures, instructions, and environment example. Ownership must be decided before extraction. |
| 12 | `app/` | directory | PORTFOLIO | Next.js application surface. |
| 13 | `components/` | directory | PORTFOLIO | Next.js/React portfolio components. |
| 14 | `data/` | directory | PORTFOLIO | Portfolio profile, experience, project, and skills data. |
| 15 | `docs/` | directory | ARCHIVE/REMOVE | Mixed legacy/control documentation. Before archiving/removal, preserve `docs/evidence-auditor.md` with the Evidence Auditor decision packet. Do not migrate the directory wholesale. |
| 16 | `eslint.config.mjs` | file | PORTFOLIO | TypeScript/Next.js lint configuration. |
| 17 | `fixtures/` | directory | EVIDENCE_AUDITOR / DECISION REQUIRED | Current root `fixtures/` contains only `fixtures/evidence-auditor/`. This corrects the earlier provisional assumption that root fixtures belonged to Able to Answer. |
| 18 | `lib/` | directory | PORTFOLIO | Primarily portfolio TypeScript helpers and contracts. Exception: `lib/evidence-auditor/` and directly related tests belong with the unresolved Evidence Auditor capability and must be separated before moving `lib/` wholesale. |
| 19 | `next-env.d.ts` | file | PORTFOLIO | Next.js generated type declaration. |
| 20 | `next.config.ts` | file | PORTFOLIO | Next.js configuration. |
| 21 | `package.json` | file | PORTFOLIO | Defines `evidence-first-portfolio` and the Next.js/Vitest toolchain. It also contains Evidence Auditor integration/script residue; reconstruct rather than blindly copy after auditor ownership is decided. |
| 22 | `postcss.config.js` | file | PORTFOLIO | Portfolio CSS build configuration. |
| 23 | `pyproject.toml` | file | ABLE_TO_ANSWER | Declares the `able-to-answer` Python package, dependencies, pytest, and Ruff configuration. |
| 24 | `scripts/` | directory | PROFILE | Primarily cross-repository/profile-control automation (`fork_inventory`, `fork_sync`, compliance/reporting/review/sync scripts). Exception: `scripts/audit-evidence.ts` follows the Evidence Auditor decision. |
| 25 | `specs/` | directory | ABLE_TO_ANSWER | Control-plane schemas/OpenAPI/telemetry contracts correspond to the Python `able_to_answer.control_plane` implementation. |
| 26 | `src/` | directory | ABLE_TO_ANSWER | Python `able_to_answer` application source, including API, ingestion, retrieval, audit, control plane, runtime agent, and related modules. |
| 27 | `tailwind.config.ts` | file | PORTFOLIO | Portfolio Tailwind configuration. |
| 28 | `tests/` | directory | ABLE_TO_ANSWER | Python service and control-plane tests. TypeScript tests live elsewhere. |
| 29 | `tsconfig.json` | file | PORTFOLIO | Root TypeScript configuration for the portfolio codebase. |
| 30 | `vitest.config.ts` | file | PORTFOLIO | Root TypeScript/Vitest test configuration. |

## Classification totals

| Classification | Count |
|---|---:|
| PROFILE | 5 |
| PORTFOLIO | 12 |
| ABLE_TO_ANSWER | 7 |
| EVIDENCE_AUDITOR / DECISION REQUIRED | 3 |
| ARCHIVE/REMOVE | 3 |
| **Total** | **30** |

## Mixed-ownership exceptions that block blind moves

The following top-level items cannot be copied wholesale even though they have a primary classification:

1. `.env.example` — Able to Answer and Evidence Auditor configuration are mixed.
2. `.github/` — Python CI and profile/control automation share one container.
3. `.gitignore` — stack-specific rules must be reconstructed per destination.
4. `docs/` — Evidence Auditor documentation is embedded among legacy/control documents.
5. `lib/` — portfolio helpers coexist with `lib/evidence-auditor/`.
6. `package.json` — portfolio package metadata contains Evidence Auditor script/integration residue.
7. `scripts/` — profile/control automation coexists with `audit-evidence.ts`.

These exceptions must be resolved at subpath level before any destructive cleanup of the source repository.

## Evidence Auditor boundary

Evidence Auditor currently exists in more than one shape:

- standalone `ai-workflow-evidence-auditor/` project;
- root `fixtures/evidence-auditor/`;
- root `lib/evidence-auditor/` plus related tests;
- root `scripts/audit-evidence.ts`;
- `docs/evidence-auditor.md`;
- Evidence Auditor variables in root `.env.example`;
- Evidence Auditor script/integration residue in root `package.json`.

No destination is selected in v0.1. The next migration phase must decide whether the standalone subproject is authoritative, whether the root integration is a duplicate/adapter, and which exact artefacts constitute the preserved capability.

## Acceptance record

Inventory completeness condition: **PASSED**.

All 30 top-level items present at frozen source commit `d5f0c5914e891b9d702993db02bd9fea40114d27` have exactly one top-level classification.

Migration execution condition: **NOT AUTHORISED BY THIS DOCUMENT**.

No file move, deletion, repository extraction, PR closure/retargeting, application refactor, or Evidence Auditor ownership decision is performed by v0.1.

## Next gated action

Classify the existing open pull requests against this frozen ownership map as `RETAIN`, `RETARGET`, `SUPERSEDE`, or `CLOSE`, without merging or closing them during the classification pass. After that, resolve the Evidence Auditor ownership boundary before any file extraction begins.
