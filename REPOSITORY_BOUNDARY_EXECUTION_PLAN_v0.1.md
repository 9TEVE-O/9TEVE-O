# REPOSITORY_BOUNDARY_EXECUTION_PLAN_v0.1

**Status:** PLAN COMPLETE — MIGRATION EXECUTION NOT YET AUTHORISED  
**Source repository:** `9TEVE-O/9TEVE-O`  
**Frozen executable source:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Planning head before this document:** `ebdd550e972afa4685c4353cf60d6259386348ec`  
**Date:** 2026-08-10  
**Parents:**

- `REPOSITORY_BOUNDARY_MIGRATION_v0.1.md`
- `REPOSITORY_BOUNDARY_PR_CLASSIFICATION_v0.1.md`
- `EVIDENCE_AUDITOR_OWNERSHIP_DECISION_v0.1.md`
- `REPOSITORY_BOUNDARY_EXTRACTION_MANIFEST_v0.1.md`
- `PROFILE_CONTROL_DEPENDENCY_BOUNDARY_v0.1.md`

## 1. Goal

Execute the approved repository-boundary separation as a transaction-style migration in which destination repositories are created and validated before any executable source is deleted from `9TEVE-O/9TEVE-O`.

The target ownership model is:

- `9TEVE-O/9TEVE-O` — public profile/control repository;
- `9TEVE-O/evidence-first-portfolio` — Next.js/TypeScript portfolio application;
- `9TEVE-O/able-to-answer` — Python/FastAPI document-intelligence system;
- `9TEVE-O/ai-workflow-evidence-auditor` — standalone TypeScript Evidence Auditor prototype.

This plan is an execution contract. It does not itself create repositories, move files, edit workflows, delete source paths, close PRs, or change repository visibility.

## 2. Preflight evidence

### 2.1 Frozen-source integrity

The executable migration source remains:

`d5f0c5914e891b9d702993db02bd9fea40114d27`

At planning time, `main` was five commits ahead of that source and the only changed files were the five repository-boundary planning/control documents listed above. No executable source file had changed after the freeze.

Execution must repeat this comparison immediately before migration. If any executable, test, package, workflow, fixture, application configuration or instruction file has changed after the frozen source, stop and classify that drift before extraction.

### 2.2 Destination-name check

At planning time:

- `9TEVE-O/evidence-first-portfolio` did not exist;
- `9TEVE-O/able-to-answer` did not exist;
- `9TEVE-O/ai-workflow-evidence-auditor` did not exist.

A separate private repository **does** exist:

`9TEVE-O/LAB-AI-Workflow-Evidence-Auditor`

It is not the extraction destination. It contains a different evidence-review implementation based on review-gate schemas and `src/evaluate-review-gates.js`.

**Invariant:** do not overwrite, rename, merge into, repurpose or delete `9TEVE-O/LAB-AI-Workflow-Evidence-Auditor` during this migration.

## 3. Destination creation and visibility decisions

The migration preserves the current public exposure of the portfolio and Able to Answer source while applying the Evidence Auditor's stated private usage boundary to its future standalone repository.

| Destination | Action | Planned visibility | Basis |
|---|---|---:|---|
| `9TEVE-O/evidence-first-portfolio` | CREATE EMPTY | Public | source is already public and is part of the public professional portfolio |
| `9TEVE-O/able-to-answer` | CREATE EMPTY | Public | source is already public; migration should not silently reduce accessibility |
| `9TEVE-O/ai-workflow-evidence-auditor` | CREATE EMPTY | Private | standalone package explicitly describes itself as private/tool-only; separate from the existing LAB auditor |

Create repositories **empty**: no generated README, licence, `.gitignore`, initial commit or template. The filtered source history must supply the first history.

Private visibility for the new auditor does not make its prior history in the public source repository private. Source cleanup only removes active-tree exposure; historical public commits remain historical public evidence.

## 4. Transaction invariants

1. The frozen source commit is the only executable migration input.
2. Open PR branches are not migration inputs.
3. No source executable path is deleted until all destination validation gates pass.
4. No destination may depend on another destination merely because the original repository mixed them.
5. No destination extraction may overwrite an existing repository with unrelated history.
6. No force-push is permitted to an existing populated repository.
7. Evidence Auditor live/billable commands are not migration validation commands.
8. Destination transformation commits may change repository-boundary metadata and mixed-path configuration only; they may not redesign application behaviour.
9. Source cleanup occurs on a dedicated branch and through a bounded PR, not as a sequence of direct destructive edits to `main`.
10. Failure of any validation gate stops forward deletion. Additive destination repositories may remain for diagnosis; source remains authoritative until final cutover.

## 5. History-preserving extraction method

Use disposable local clones and `git filter-repo` or an equivalently auditable history-filtering tool.

For each destination:

1. clone `9TEVE-O/9TEVE-O` into a fresh temporary directory;
2. create a local `migration-source` branch at exactly `d5f0c5914e891b9d702993db02bd9fea40114d27`;
3. filter only `refs/heads/migration-source` using the exact preserve set in `REPOSITORY_BOUNDARY_EXTRACTION_MANIFEST_v0.1.md`;
4. for the auditor, rename `ai-workflow-evidence-auditor/` to repository root during filtering;
5. inspect the resulting tree before adding a destination remote;
6. rename the filtered branch to `main` only after the tree matches the manifest;
7. push the filtered history to the corresponding empty destination;
8. record the destination extraction-tip SHA before any boundary-repair commit.

Conceptual command shape:

```bash
git clone <source> <temporary-directory>
cd <temporary-directory>
git switch --detach d5f0c5914e891b9d702993db02bd9fea40114d27
git switch -c migration-source
git filter-repo --force --refs refs/heads/migration-source <exact --path set> [--path-rename old/:new/]
git branch -M main
git remote remove origin
git remote add destination <empty-destination-url>
git push -u destination main
```

The actual `--path` arguments must be generated directly from the extraction manifest rather than improvised during execution.

If `git filter-repo` is unavailable, stop. Do not substitute copy/paste into a fresh unrelated history unless preserving history has been explicitly waived.

## 6. Transaction sequence

### T0 — Revalidate source and destination preconditions

Before any repository creation:

- compare `d5f0c591…` to then-current `main`;
- confirm post-freeze changes are migration-control documents only;
- repeat the three exact destination-name searches;
- confirm `LAB-AI-Workflow-Evidence-Auditor` remains separate and untouched;
- capture source `main` SHA and frozen source SHA in an execution record.

**Checkpoint G0:** PASS only if there is no unclassified executable drift and no destination-name collision.

Failure action: stop. No repository creation.

---

### T1 — Create the three empty destination repositories

Create exactly:

1. `9TEVE-O/evidence-first-portfolio` — public;
2. `9TEVE-O/able-to-answer` — public;
3. `9TEVE-O/ai-workflow-evidence-auditor` — private.

Do not initialise them with generated files.

Record repository IDs, URLs, visibility and empty/default-branch state.

**Checkpoint G1:** all three exact destinations exist with the planned visibility and contain no unrelated initial content.

Failure action: stop before extraction. Do not alter source.

---

### T2 — Extract and validate `ai-workflow-evidence-auditor`

Use the complete frozen subtree:

`ai-workflow-evidence-auditor/`

Rebase the subtree to repository root with history preserved.

Do not import:

- root `lib/evidence-auditor/`;
- root `lib/__tests__/evidence-auditor.test.ts`;
- root `fixtures/evidence-auditor/`;
- root `scripts/audit-evidence.ts`;
- root `docs/evidence-auditor.md`;
- root package or environment residue.

#### First post-extraction transformation

**None required.** The standalone subtree is already self-contained. The extracted filtered-history tip should be validated before any optional CI or repository metadata is added.

#### Validation G-AUDITOR

```bash
npm install
npm test
npm run build
```

Additional assertions:

- no import reaches the source profile repository;
- no Able to Answer path is present;
- no portfolio `app/`, `components/`, root `lib/` or root package residue is present;
- `fixtures/eval-001.input.json` matches the standalone frozen fixture;
- `npm run audit` is not executed;
- `npm run eval:live` is not executed.

Record extraction-tip SHA and validation output.

Failure action: stop. Do not delete any auditor source/residue from `9TEVE-O/9TEVE-O`.

---

### T3 — Extract and repair `able-to-answer`

Filter the exact Able to Answer preserve set in the extraction manifest, including:

- `src/able_to_answer/`;
- `specs/` four listed contracts;
- the nine listed Able to Answer Python tests;
- `AGENTS.md`;
- `CLAUDE.md`;
- `.github/copilot-instructions.md`;
- `.github/PULL_REQUEST_TEMPLATE.md`;
- `.github/workflows/ci.yml`;
- `.github/workflows/control_pack_validation.yml`;
- `pyproject.toml`;
- `Makefile`;
- mixed `.env.example` and `.gitignore` only for immediate boundary reconstruction.

Do not carry `tests/openai.test.ts`, `tests/test_fork_inventory.py` or `tests/test_review_bot.py`.

#### First post-extraction commit

Suggested commit:

`[migration] separate: able-to-answer repository boundary`

Apply exactly the manifest transformations:

- create an Able to Answer-specific `README.md`;
- reconstruct `.env.example` with only Able to Answer document/search variables;
- reconstruct a Python/SQLite `.gitignore`;
- remove `governance` optional dependencies from `pyproject.toml`;
- remove the Ruff exception for `scripts/fork_inventory.py`;
- repair the duplicated `Makefile` `test:` target;
- change Makefile lint to `ruff check src/ tests/`;
- change `.github/workflows/ci.yml` lint to `ruff check src/ tests/`;
- remove stale repository-wide/test-count claims from `AGENTS.md` while preserving Able to Answer-specific instructions;
- do not add portfolio, profile-control or Evidence Auditor dependencies.

#### Validation G-ATA

```bash
python -m pip install -e ".[dev]"
ruff check src/ tests/
python -m pytest tests/ -v
```

Additional assertions:

- pytest collects only Able to Answer tests;
- no Node/Next.js package is required;
- no profile-control script is imported;
- no Evidence Auditor path is present;
- package metadata resolves its destination-local README.

Record extraction-tip SHA, boundary-repair commit SHA and validation output.

Failure action: stop. Source Able to Answer paths and `pyproject.toml` remain untouched.

---

### T4 — Extract and repair `evidence-first-portfolio`

Filter the exact portfolio preserve set in the extraction manifest, including:

- `app/`;
- `components/`;
- `data/`;
- `lib/ai-contracts.ts`;
- `lib/analytics.ts`;
- `lib/openai.ts`;
- `lib/portfolio-data.ts`;
- the four corresponding `lib/__tests__/` files;
- `tests/openai.test.ts`;
- Next.js/TypeScript/Vitest/ESLint/Tailwind/PostCSS configuration;
- root `package.json` for immediate boundary reconstruction;
- `.github/workflows/codeql-debug.yml`.

Do not carry Evidence Auditor library/test/fixture/script residue.

#### First post-extraction commit

Suggested commit:

`[migration] separate: evidence-first-portfolio repository boundary`

Apply exactly the manifest transformations:

- create a portfolio-specific `README.md`;
- reconstruct `.env.example` with the documented `ATA_OPENAI_*` variables only;
- reconstruct the Node/Next `.gitignore`;
- remove `audit:evidence` from `package.json`;
- retain the existing OpenAI dependency used by portfolio code;
- remove all root-integrated Evidence Auditor code/tests/fixtures/scripts from the destination tree;
- do not carry Python/Able to Answer workflows or instructions.

A new portfolio CI workflow is optional during this migration. If created, it may only automate the existing validation commands below; it must not introduce application changes.

#### Validation G-PORTFOLIO

```bash
npm install
npm run lint
npm run typecheck
npm test
npm run build
```

Additional assertions:

- no test imports `lib/evidence-auditor/`;
- no package script references `scripts/audit-evidence.ts`;
- no Python/Able to Answer source is required;
- no profile-control script is required.

Record extraction-tip SHA, boundary-repair commit SHA and validation output.

Failure action: stop. No portfolio source is deleted from the profile repository.

---

### T5 — Repair profile/control Python dependency boundary

Only after G-AUDITOR, G-ATA and G-PORTFOLIO pass, prepare the non-destructive profile/control dependency repair from `PROFILE_CONTROL_DEPENDENCY_BOUNDARY_v0.1.md`.

Add:

`requirements-profile-control.txt`

```text
requests>=2.31,<3
notion-client>=2.2,<3
```

Add:

`requirements-profile-control-dev.txt`

```text
-r requirements-profile-control.txt
pytest>=8,<9
```

Update workflows:

- `fork_manager.yml` — remove both `pip install -e "." -q` profile-package install steps;
- `review_automation.yml` — no package-install change;
- `governance_sync.yml` — replace `pip install -e ".[governance]"` with `python -m pip install -r requirements-profile-control.txt` wherever used.

Do not change script behaviour.

#### Validation G-PROFILE-DEPS

```bash
python -m pip install -r requirements-profile-control-dev.txt
python -m py_compile \
  scripts/fork_inventory.py \
  scripts/fork_sync.py \
  scripts/generate_compliance_report.py \
  scripts/gh_review_bot.py \
  scripts/sync_studio_to_codex.py
python -m pytest tests/test_fork_inventory.py tests/test_review_bot.py -v
```

Additional assertions:

- no retained profile/control script imports `able_to_answer`;
- no retained profile workflow contains `pip install -e .` or `pip install -e ".[governance]"`;
- the profile/control tests pass without installing Able to Answer.

`generate_compliance_report.py` retains its known `ATA_DB_PATH` / `audits`-table data dependency. That is not a packaging blocker and must not be solved by copying Able to Answer code back into the profile repository.

---

### T6 — Aggregate no-delete gate

Before deleting any executable source from `9TEVE-O/9TEVE-O`, assemble one migration evidence record containing:

- frozen source SHA;
- current profile `main` SHA;
- destination repository IDs/URLs/visibility;
- auditor extraction-tip SHA and G-AUDITOR result;
- Able to Answer extraction-tip SHA, boundary-repair SHA and G-ATA result;
- portfolio extraction-tip SHA, boundary-repair SHA and G-PORTFOLIO result;
- profile-control dependency-repair SHA/branch and G-PROFILE-DEPS result;
- explicit confirmation that `LAB-AI-Workflow-Evidence-Auditor` was untouched.

**G-ALL-DESINATIONS:** PASS only if all four validation gates are PASS.

If any result is FAIL, UNKNOWN or NOT RUN, source deletion remains prohibited.

---

### T7 — Source/profile cleanup branch

After G-ALL-DESINATIONS passes, create a dedicated cleanup branch from then-current `9TEVE-O/9TEVE-O:main`, for example:

`repo-boundary/execute-v0.1`

Apply the cleanup as one bounded migration change set.

#### Retain as profile/control ownership

- public profile `README.md`;
- `FORKS_INVENTORY.md`;
- retained profile/control scripts:
  - `scripts/fork_inventory.py`;
  - `scripts/fork_sync.py`;
  - `scripts/generate_compliance_report.py`;
  - `scripts/gh_review_bot.py`;
  - `scripts/sync_studio_to_codex.py`;
- retained profile/control tests:
  - `tests/test_fork_inventory.py`;
  - `tests/test_review_bot.py`;
- `.github/workflows/fork_manager.yml`;
- `.github/workflows/governance_sync.yml`;
- `.github/workflows/review_automation.yml`;
- `docs/agent-review-policy-v1.md` as the current account/profile review-policy reference, subject to the later path re-baseline below;
- repository-boundary decision/manifest/execution records;
- the two new profile-control requirements files.

#### Remove migrated portfolio ownership from the active profile tree

- `app/`;
- `components/`;
- `data/`;
- portfolio `lib/` files/tests;
- `eslint.config.mjs`;
- `next-env.d.ts`;
- `next.config.ts`;
- `package.json`;
- `postcss.config.js`;
- `tailwind.config.ts`;
- `tsconfig.json`;
- `vitest.config.ts`;
- `tests/openai.test.ts`;
- `.github/workflows/codeql-debug.yml`.

#### Remove migrated Able to Answer ownership from the active profile tree

- `src/`;
- `specs/`;
- Able to Answer Python tests;
- `pyproject.toml`;
- `Makefile`;
- existing Able to Answer `CLAUDE.md`;
- existing Able to Answer content in `AGENTS.md`;
- `.github/copilot-instructions.md`;
- `.github/PULL_REQUEST_TEMPLATE.md`;
- `.github/workflows/ci.yml`;
- `.github/workflows/control_pack_validation.yml`.

Replace root `AGENTS.md` with a minimal profile/control-specific instruction file rather than leaving Able to Answer instructions at repository root.

#### Remove standalone Evidence Auditor source and duplicate residue from the active profile tree

- `ai-workflow-evidence-auditor/`;
- `lib/evidence-auditor/`;
- `lib/__tests__/evidence-auditor.test.ts`;
- `fixtures/evidence-auditor/`;
- `scripts/audit-evidence.ts`;
- `docs/evidence-auditor.md`;
- root Evidence Auditor environment/package residue.

#### Archive/remove stale active authority

Remove from the active tree while preserving Git history:

- `ADR/` legacy `9TEVE-OS` architecture records;
- `SETUP_PLAN.md`;
- `docs/scale-stack.md`;
- `docs/threat-model/`.

#### Reconstruct mixed profile files

- replace root `.gitignore` with a minimal profile/control Python/OS/environment ignore appropriate to the retained scripts/tests;
- remove the mixed root `.env.example` unless a profile-only environment example is separately justified; do not retain Able to Answer, portfolio or auditor variables by inertia.

#### Repair public links

Update the profile README so the relevant project references point to the new repositories:

- Evidence-first portfolio → `9TEVE-O/evidence-first-portfolio`;
- Able to Answer → `9TEVE-O/able-to-answer`;
- Evidence Auditor → `9TEVE-O/ai-workflow-evidence-auditor` only if linking a private repository is useful for the intended audience; otherwise describe it without a dead public link.

Do not alter the separate `LAB-AI-Workflow-Evidence-Auditor` link or identity unless separately authorised.

#### Re-baseline review-bot path semantics

`gh_review_bot.py` currently names Able to Answer-specific sensitive paths. During profile cleanup, remove stale Able to Answer-only path entries and retain only paths that actually exist or are materially sensitive in the final profile/control repository.

This is a path-policy repair caused directly by extraction, not a redesign of approval behaviour.

---

### T8 — Validate the cleaned profile repository before merge

On the cleanup branch:

```bash
python -m pip install -r requirements-profile-control-dev.txt
python -m py_compile \
  scripts/fork_inventory.py \
  scripts/fork_sync.py \
  scripts/generate_compliance_report.py \
  scripts/gh_review_bot.py \
  scripts/sync_studio_to_codex.py
python -m pytest tests/test_fork_inventory.py tests/test_review_bot.py -v
```

Repository-shape assertions:

- no `src/able_to_answer/`;
- no Next.js `app/`, `components/`, portfolio `data/`, package or TypeScript build configuration;
- no active Evidence Auditor implementation or duplicate residue;
- no Able to Answer editable-install dependency in retained workflows;
- no stale `9TEVE-OS` ADR/setup files in the active tree;
- root `AGENTS.md` describes profile/control ownership only;
- profile README links resolve to the intended destinations;
- retained workflows/scripts/tests have clear ownership.

**Checkpoint G-PROFILE-FINAL:** PASS required before cleanup PR merge.

Failure action: do not merge cleanup PR. Destination repositories remain additive and intact; source `main` remains uncut.

---

### T9 — Merge profile cleanup and record cutover

Merge the bounded cleanup PR only after G-PROFILE-FINAL passes.

Record:

- cleanup PR number;
- cleanup merge SHA;
- final profile tree SHA;
- destination final validation SHAs;
- cutover timestamp.

The cleanup merge SHA becomes the active repository-boundary cutover point.

Rollback after this point is a normal revert of the cleanup merge/commit. Do not delete destination repositories as a rollback mechanism.

---

### T10 — Resolve classified stale PRs

Only after the cutover is successful, apply `REPOSITORY_BOUNDARY_PR_CLASSIFICATION_v0.1.md`:

- #86 — close as **SUPERSEDED**;
- #84 — close as **SUPERSEDED**;
- #80 — close as **SUPERSEDED**;
- #72 — **CLOSE** as outside the current repository boundary;
- #60 — close as **SUPERSEDED**.

Do not merge any of them into the cleaned profile repository.

Where practical, add a concise closure comment identifying the relevant destination or frozen/current-tree migration authority so provenance is preserved.

---

### T11 — Independent boundary verification

Perform one final read-only review across all four active repositories.

For each repository, an independent reviewer must be able to answer:

1. **What does this repository own?**
2. **How is it tested?**
3. **What work does not belong here?**

Minimum cross-boundary checks:

#### `9TEVE-O/9TEVE-O`

Owns public profile/control automation only. No executable portfolio, Able to Answer or standalone auditor implementation remains.

#### `evidence-first-portfolio`

Owns Next.js/TypeScript portfolio application only. No Python service or Evidence Auditor implementation remains.

#### `able-to-answer`

Owns Python/FastAPI document intelligence only. No Next.js portfolio or profile-control automation is required.

#### `ai-workflow-evidence-auditor`

Owns the standalone TypeScript Responses API auditor only. No portfolio or Able to Answer runtime dependency is required.

Also confirm the separate private `LAB-AI-Workflow-Evidence-Auditor` remains unchanged and is not accidentally treated as this migration's destination.

**Final gate G-BOUNDARY:** PASS only when all four repositories satisfy the ownership/test/non-ownership questions without relying on historical context from the old mixed repository.

## 7. Rollback model

### Before T9 cleanup merge

Rollback is trivial: stop. The public source repository still contains all original executable paths. Destination repositories are additive copies with filtered history.

### After T9 cleanup merge

Rollback by reverting the bounded cleanup merge/commit in `9TEVE-O/9TEVE-O`.

Do not:

- force-push destination history;
- delete destination repositories to simulate rollback;
- merge stale PRs back into the profile repository;
- restore the old mixed packaging as a shortcut.

The frozen source SHA remains a permanent recovery reference.

## 8. Execution evidence record

Execution should produce a final record containing at minimum:

| Field | Required |
|---|---|
| Frozen source SHA | yes |
| Pre-execution profile `main` SHA | yes |
| Destination repo IDs/visibility | yes |
| Filtered extraction-tip SHAs | yes |
| Destination boundary-repair SHAs | where applicable |
| G-AUDITOR result | yes |
| G-ATA result | yes |
| G-PORTFOLIO result | yes |
| G-PROFILE-DEPS result | yes |
| G-PROFILE-FINAL result | yes |
| Cleanup PR + merge SHA | yes |
| Stale PR closure results | yes |
| G-BOUNDARY independent-review result | yes |
| Confirmation existing LAB auditor untouched | yes |

## 9. Gate summary

| Gate | Meaning | Source deletion allowed? |
|---|---|---:|
| G0 | source/destination preflight clean | No |
| G1 | empty destination repos correctly created | No |
| G-AUDITOR | standalone auditor extracted + validated | No |
| G-ATA | Able to Answer extracted + validated | No |
| G-PORTFOLIO | portfolio extracted + validated | No |
| G-PROFILE-DEPS | profile controls independent of ATA packaging | No |
| G-ALL-DESINATIONS | all destination/dependency gates pass | **Cleanup branch may be prepared** |
| G-PROFILE-FINAL | cleaned profile branch validates | **Cleanup PR may be merged** |
| G-BOUNDARY | independent four-repo boundary verification passes | Migration complete |

## 10. Plan result

Repository-boundary execution sequence: **DEFINED**.  
Frozen source: **UNCHANGED**.  
Destination repositories: **NOT CREATED**.  
Destination visibility: **PLANNED, NOT APPLIED**.  
Extraction: **NOT PERFORMED**.  
Profile workflow repair: **NOT PERFORMED**.  
Source deletion: **NOT PERFORMED**.  
PR closure: **NOT PERFORMED**.

## Next gated action

Execute **T0 only**: repeat the frozen-source drift comparison and exact destination-name/visibility preflight immediately before migration execution, capture the execution preflight record, and stop at G0.

Do not create destination repositories until G0 passes and migration execution is explicitly authorised.