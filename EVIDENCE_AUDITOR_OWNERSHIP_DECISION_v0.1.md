# EVIDENCE_AUDITOR_OWNERSHIP_DECISION_v0.1

**Status:** DECISION COMPLETE — EXTRACTION NOT YET AUTHORISED  
**Decision:** `STANDALONE REPOSITORY`  
**Repository:** `9TEVE-O/9TEVE-O`  
**Parent:** `REPOSITORY_BOUNDARY_MIGRATION_v0.1.md`  
**PR classification parent:** `REPOSITORY_BOUNDARY_PR_CLASSIFICATION_v0.1.md`  
**Frozen migration source:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Decision date:** 2026-08-09

## Goal

Resolve the Evidence Auditor ownership boundary before any repository extraction begins.

Exactly one permitted ownership status must be selected:

- `STANDALONE REPOSITORY`
- `PORTFOLIO-OWNED CAPABILITY`
- `ABLE_TO_ANSWER-OWNED CAPABILITY`
- `ARCHIVE/REMOVE DUPLICATE`

## Decision

**Selected status: `STANDALONE REPOSITORY`.**

The authoritative capability boundary is the self-contained project currently located at:

`ai-workflow-evidence-auditor/`

This directory should become the source package for a future dedicated Evidence Auditor repository. This decision does not create that repository, change repository visibility, copy files, delete duplicates, or authorise extraction.

## Basis

### 1. Explicit standalone intent

`ai-workflow-evidence-auditor/AGENTS.md` explicitly states that the directory is a standalone private TypeScript prototype and provides independent install, test, build and live-run boundaries.

### 2. Independent package boundary

The directory has its own:

- `package.json`
- `.env.example`
- `.gitignore`
- `AGENTS.md`
- `README.md`
- `src/`
- `tests/`
- `fixtures/`
- `tsconfig.json`

Its package is named `ai-workflow-evidence-auditor`, has its own runtime and development dependencies, and exposes its own build, test, audit and optional live-evaluation commands.

### 3. The standalone implementation is the later hardened form

The initial root-integrated Evidence Auditor prototype was added in commit `b9dff4c3b1c48d2ee1e6d439b6df3d6612f84181`.

The next auditor change, commit `71950d5cdb67ff6169849c5610a7313c2b6d0fd9` (`Harden auditor input validation`), created the self-contained `ai-workflow-evidence-auditor/` package.

That later package:

- uses OpenAI SDK 6 rather than relying on the root portfolio's OpenAI SDK 4 compatibility workaround;
- uses Zod-native input and output schemas;
- uses parsed structured output rather than manually parsing `output_text` JSON;
- rejects unknown fields, blank required values and duplicate evidence identifiers;
- has dedicated offline tests plus an explicitly separated optional live evaluation;
- carries a richer representative fixture than the earlier root-integrated copy.

The sequence and content show evolution from root integration to standalone hardened package.

### 4. Capability semantics do not belong to the portfolio

The Evidence Auditor reviews a bounded AI-assisted workflow against controlled evidence. Its core objects are workflow reconstruction, evidence and authority, unsupported claims, reliability/governance risk, unresolved questions, corrective actions and a decision-ready review report.

Those semantics are general workflow-review semantics. They are not presentation, portfolio data, recruiter Q&A, analytics or personal-site functionality.

Therefore `PORTFOLIO-OWNED CAPABILITY` is rejected.

### 5. Capability semantics do not belong to Able to Answer

Able to Answer is a Python/FastAPI document-intelligence system with ingestion, retrieval, answering, audit and control-plane components.

The Evidence Auditor is a separate TypeScript tool with its own OpenAI Responses API contract, saved prompt, schema and test harness. It does not require Able to Answer ingestion, retrieval, SQLite, FastAPI or control-plane runtime to operate.

Therefore `ABLE_TO_ANSWER-OWNED CAPABILITY` is rejected.

### 6. The capability itself is not a duplicate to discard

The root-integrated implementation is duplicate/residual, but the standalone package represents a coherent independently testable capability.

Therefore `ARCHIVE/REMOVE DUPLICATE` is rejected as the ownership status for the capability as a whole.

## Authoritative preservation set

When extraction is later authorised, preserve the contents of the frozen source path:

`ai-workflow-evidence-auditor/`

including its:

- source;
- schemas;
- environment contract;
- fixture(s);
- offline tests;
- optional live evaluation boundary;
- package metadata;
- TypeScript configuration;
- README and agent instructions.

The frozen source commit remains `d5f0c5914e891b9d702993db02bd9fea40114d27` unless a later explicit migration decision supersedes it.

## Root-integrated residue map

The following paths are no longer authoritative implementations once the standalone package is selected. They should be treated as migration residue and removed from destination repositories only after successful standalone extraction and validation:

| Current path | Disposition after successful extraction |
|---|---|
| `lib/evidence-auditor/` | REMOVE DUPLICATE from portfolio destination |
| `lib/__tests__/evidence-auditor.test.ts` and directly related root tests | REMOVE DUPLICATE from portfolio destination |
| `fixtures/evidence-auditor/` | REMOVE DUPLICATE from source/profile and portfolio migration sets |
| `scripts/audit-evidence.ts` | REMOVE DUPLICATE from profile/control scripts |
| `docs/evidence-auditor.md` | ARCHIVE IN GIT HISTORY; do not carry as active profile documentation unless rewritten as a link to the standalone repository |
| root `.env.example` Evidence Auditor variables | REMOVE from profile/Able to Answer examples; standalone environment contract owns them |
| root `package.json` `audit:evidence` script and Evidence Auditor-only dependency/integration residue | REMOVE during portfolio cleanup if no longer required by other portfolio features |

These are cleanup instructions, not permission to delete files now.

## Visibility boundary

The standalone README and agent instructions call the prototype `private`, but the current source is located in a public repository.

This decision does **not** infer or change repository visibility. Visibility must be chosen explicitly when the standalone repository is created. Until then, `private` should be understood as the tool's intended usage boundary, not evidence that the current source is private.

## Rejected alternatives

| Alternative | Decision |
|---|---|
| `PORTFOLIO-OWNED CAPABILITY` | REJECTED — coupling exists because the first prototype was embedded in the portfolio package, not because the capability belongs to portfolio semantics. |
| `ABLE_TO_ANSWER-OWNED CAPABILITY` | REJECTED — separate runtime, language, package, schema and workflow purpose. |
| `ARCHIVE/REMOVE DUPLICATE` | REJECTED for the capability — only the root-integrated copies are duplicate residue. |

## Gate result

Evidence Auditor ownership: **RESOLVED**.  
Selected status: **STANDALONE REPOSITORY**.  
Authoritative source boundary: **`ai-workflow-evidence-auditor/` at frozen migration source**.  
Extraction execution: **NOT PERFORMED**.  
Deletion/cleanup: **NOT PERFORMED**.

The Evidence Auditor ownership blocker on repository-boundary planning is now closed.

## Next gated action

Prepare an extraction manifest for the three executable destinations without moving files:

1. `evidence-first-portfolio`
2. `able-to-answer`
3. `ai-workflow-evidence-auditor`

For each destination, list the exact source paths to preserve, mixed-path transformations required for `.github/`, `.gitignore`, `.env.example`, `docs/`, `lib/`, `scripts/` and package metadata, and the minimum validation commands that must pass after extraction.

Do not create repositories, move files, delete duplicates, close PRs or begin application refactoring during the manifest pass.