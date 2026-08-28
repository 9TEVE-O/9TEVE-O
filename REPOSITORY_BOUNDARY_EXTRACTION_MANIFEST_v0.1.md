# REPOSITORY_BOUNDARY_EXTRACTION_MANIFEST_v0.1

**Status:** MANIFEST COMPLETE — NO EXTRACTION EXECUTION AUTHORISED  
**Repository:** `9TEVE-O/9TEVE-O`  
**Frozen source commit:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Parent:** `REPOSITORY_BOUNDARY_MIGRATION_v0.1.md`  
**PR classification:** `REPOSITORY_BOUNDARY_PR_CLASSIFICATION_v0.1.md`  
**Evidence Auditor decision:** `EVIDENCE_AUDITOR_OWNERSHIP_DECISION_v0.1.md`  
**Manifest date:** 2026-08-09

## Purpose

Define the exact extraction boundary for the three executable destination repositories without creating repositories, moving files, deleting duplicates, changing PR state, or redesigning application behaviour.

Destinations:

1. `evidence-first-portfolio`
2. `able-to-answer`
3. `ai-workflow-evidence-auditor`

The frozen source tree is authoritative for extraction. Open PR branches are not migration inputs.

## Cross-cutting rules

- Preserve application behaviour during extraction.
- Do not copy mixed root directories wholesale where this manifest specifies subpath splits.
- Do not carry stale `9TEVE-OS` architecture documents into a destination as current authority.
- Do not carry the root-integrated Evidence Auditor implementation into the portfolio.
- Do not run the Evidence Auditor live evaluation during migration validation.
- Do not remove source/profile files until the corresponding destination has passed its minimum validation gate.
- Preserve Git history where practical, but content ownership takes precedence over retaining the current monorepo shape.

---

# 1. `evidence-first-portfolio`

## 1.1 Exact source paths to preserve

Copy these frozen source paths into the destination root, preserving relative paths unless a transformation is stated below:

### Application

- `app/`
- `components/`
- `data/`

### Portfolio library

- `lib/ai-contracts.ts`
- `lib/analytics.ts`
- `lib/openai.ts`
- `lib/portfolio-data.ts`

### Portfolio tests

- `lib/__tests__/ai-contracts.test.ts`
- `lib/__tests__/analytics.test.ts`
- `lib/__tests__/openai.test.ts`
- `lib/__tests__/portfolio-data.test.ts`
- `tests/openai.test.ts`

### Build and test configuration

- `eslint.config.mjs`
- `next-env.d.ts`
- `next.config.ts`
- `postcss.config.js`
- `tailwind.config.ts`
- `tsconfig.json`
- `vitest.config.ts`

### Package metadata

- `package.json` — transform as specified in §1.2.

### GitHub automation

- `.github/workflows/codeql-debug.yml` — portfolio-owned JavaScript/TypeScript diagnostic workflow. Preserve as a manual workflow; do not copy it to the auditor merely because the auditor is also TypeScript.

## 1.2 Required transformations

### `lib/`

Do **not** copy these Evidence Auditor residues:

- `lib/evidence-auditor/`
- `lib/__tests__/evidence-auditor.test.ts`

All other listed portfolio library/test files above are preserved.

### `tests/`

Root `tests/` is mixed ownership. Preserve only:

- `tests/openai.test.ts`

Do not copy Python tests into the portfolio.

### `package.json`

Start from the frozen root `package.json` and make only these boundary changes:

- retain package name `evidence-first-portfolio`;
- retain `dev`, `build`, `lint`, `typecheck`, `test`, and `test:watch` scripts;
- remove the `audit:evidence` script;
- retain `openai` because `lib/openai.ts` and the portfolio API routes use it;
- retain the existing Next.js/React/TypeScript/Vitest/ESLint/PostCSS/Tailwind dependency set;
- do not add Evidence Auditor dependencies or commands.

### `.env.example`

Reconstruct a portfolio-only `.env.example` from the root mixed file with only:

```text
ATA_OPENAI_API_KEY=
ATA_OPENAI_BASE_URL=https://api.openai.com/v1
ATA_OPENAI_MODEL=gpt-4o-mini
```

The implementation may continue to accept legacy unprefixed OpenAI environment variables as a compatibility fallback; the documented destination contract remains the `ATA_OPENAI_*` variables already used by the current portfolio code.

Do not copy Able to Answer `ATA_DB_*` / chunk / GitHub-search settings or Evidence Auditor prompt variables.

### `.gitignore`

Reconstruct a portfolio-specific ignore file from the current mixed root file. Minimum retained rules:

```text
node_modules/
.env
.env.local
.env.*.local
.next/
tsconfig.tsbuildinfo
*.log
.DS_Store
Thumbs.db
package-lock.json
```

This preserves current repository behaviour; changing lock-file policy is outside this migration.

### `.github/`

Do not copy the current `.github/` directory wholesale.

- preserve `.github/workflows/codeql-debug.yml` in the portfolio;
- do not copy `.github/workflows/ci.yml` or `control_pack_validation.yml` — they are Python/Able to Answer workflows;
- do not copy `fork_manager.yml`, `governance_sync.yml`, or `review_automation.yml` — they belong to profile/control operations;
- do not copy the current `.github/copilot-instructions.md` or `PULL_REQUEST_TEMPLATE.md` because both are explicitly Able to Answer/Python-specific.

A portfolio CI workflow may be created during extraction implementation, but its scope must be limited to the existing package commands below and must not introduce feature work.

### `docs/`

Do not copy root `docs/` into the portfolio.

- `docs/evidence-auditor.md` is superseded by the standalone auditor package;
- `docs/agent-review-policy-v1.md` is account/profile-control policy;
- `docs/scale-stack.md` and `docs/threat-model/STRIDE.md` describe the older `9TEVE-OS` architecture and remain archival history, not portfolio authority.

### `scripts/`

Copy no root `scripts/` files into the portfolio.

In particular, `scripts/audit-evidence.ts` is superseded by the standalone auditor CLI.

### README

Do **not** copy the root `README.md`; it is the GitHub public profile README.

Create a destination-local README during extraction containing only the portfolio purpose, existing run/build/test commands, environment variables, and repository boundary. This is migration metadata, not application redesign.

## 1.3 Minimum validation gate

From the extracted portfolio root:

```bash
npm install
npm run lint
npm run typecheck
npm test
npm run build
```

Acceptance:

- all commands exit successfully;
- no test imports `lib/evidence-auditor/`;
- no package script references `scripts/audit-evidence.ts`;
- no Python/Able to Answer path is required by the app, tests, or build.

---

# 2. `able-to-answer`

## 2.1 Exact source paths to preserve

### Application source

- `src/able_to_answer/` in full.

### Contracts/specifications

- `specs/action-envelope.json`
- `specs/control-plane.openapi.yaml`
- `specs/policy-schema.json`
- `specs/telemetry-contract.md`

### Python tests

Preserve exactly:

- `tests/test_api.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `tests/test_control_plane.py`
- `tests/test_github_search.py`
- `tests/test_runtime_persistence.py`
- `tests/test_suggest_upgrades.py`
- `tests/test_telemetry.py`
- `tests/test_units.py`

Do not copy:

- `tests/openai.test.ts` — portfolio;
- `tests/test_fork_inventory.py` — profile/control automation;
- `tests/test_review_bot.py` — profile/control automation.

### Python project metadata

- `pyproject.toml` — transform as specified in §2.2.
- `Makefile` — transform as specified in §2.2.

### Project instructions

- `AGENTS.md` — preserve Able to Answer guidance, but remove stale repository-wide/test-count assertions during extraction.
- `CLAUDE.md` — preserve Able to Answer-specific architecture/instructions.
- `.github/copilot-instructions.md` — preserve; it explicitly identifies `9TEVE-O / able-to-answer` and the Python/FastAPI stack.
- `.github/PULL_REQUEST_TEMPLATE.md` — preserve; its validation commands and conventions are Python/Able to Answer-specific.

### GitHub automation

- `.github/workflows/ci.yml`
- `.github/workflows/control_pack_validation.yml`

Both require boundary transformations below.

## 2.2 Required transformations

### `pyproject.toml`

Start from the frozen file and apply only these ownership corrections:

- retain `[project]`, core FastAPI/Uvicorn/Pydantic/python-multipart dependencies, `dev` dependencies, project script, build-system, setuptools, pytest and Ruff configuration;
- remove the `governance` optional-dependency group because it exists for profile/control scripts, not Able to Answer runtime code;
- remove the Ruff per-file ignore for `scripts/fork_inventory.py`;
- retain `readme = "README.md"` only after creating an Able to Answer-specific destination README; do not copy the public profile README.

### `Makefile`

The frozen Makefile contains a duplicated `test:` target and its lint target references mixed root `scripts/`.

Reconstruct minimally as:

- `install` → `pip install -e ".[dev]"`;
- `run` → existing Uvicorn command;
- one `test` target → `python -m pytest tests/ -v`;
- `lint` → `ruff check src/ tests/`.

Do not preserve the duplicate `test:` definition or a reference to profile/control scripts.

### `.env.example`

Reconstruct an Able to Answer-only file from the mixed root file with:

```text
ATA_DB_PATH=able_to_answer.sqlite3
ATA_CHUNK_SIZE_CHARS=1200
ATA_CHUNK_OVERLAP_CHARS=200
ATA_MAX_CONTEXT_CHUNKS=6
ATA_MAX_ANSWER_CHARS=1800
ATA_GITHUB_TOKEN=
```

Do not include portfolio `ATA_OPENAI_*` variables or Evidence Auditor prompt variables unless later evidence shows Able to Answer runtime code requires them.

### `.gitignore`

Reconstruct a Python-specific file from the current mixed root rules. Minimum retained categories:

- Python caches/bytecode;
- build/distribution/egg metadata;
- `.pytest_cache/`, coverage outputs and profiling outputs;
- `.env` and virtual-environment directories;
- logs/temp files;
- SQLite database/WAL/SHM files;
- IDE/OS noise.

Do not carry Next.js `.next/`, `tsconfig.tsbuildinfo`, or Node-only rules unless independently required later.

### `.github/workflows/ci.yml`

Preserve the existing Python 3.12 install/test flow but change:

```text
ruff check src/ scripts/ tests/
```

to:

```text
ruff check src/ tests/
```

because no profile/control `scripts/` directory belongs in Able to Answer.

Retain:

```text
pip install -e ".[dev]"
python -m pytest tests/ -v
```

### `.github/workflows/control_pack_validation.yml`

Preserve as an Able to Answer validation workflow because it installs the Python package and executes the repository pytest suite. After extraction it must resolve only the Able to Answer project and tests; no profile/control paths may be required.

### `docs/`

Do not copy the root `docs/` directory into Able to Answer during this extraction.

`docs/scale-stack.md` and `docs/threat-model/STRIDE.md` contain historical `9TEVE-OS` architecture claims that are broader than the current Able to Answer repository and reference archived ADR/setup authority. Preserve them in source Git history rather than promoting them into the new repository as current design documents.

### `scripts/`

Copy no root `scripts/` directory into Able to Answer. Current root scripts are profile/control automation or Evidence Auditor residue.

### README

Do not copy the root profile README.

Create an Able to Answer-specific README from the existing package purpose and current `AGENTS.md` / `CLAUDE.md` operational facts. The README must answer:

- what Able to Answer owns;
- how to install/run/test it;
- what work does not belong in the repository.

## 2.3 Minimum validation gate

From the extracted Able to Answer root:

```bash
python -m pip install -e ".[dev]"
ruff check src/ tests/
python -m pytest tests/ -v
```

Acceptance:

- all commands exit successfully;
- pytest collects only Able to Answer tests;
- no test imports `scripts/fork_inventory.py` or `scripts/gh_review_bot.py`;
- no Node/Next.js path is required;
- package metadata no longer points at the public profile README.

---

# 3. `ai-workflow-evidence-auditor`

## 3.1 Authoritative source boundary

The authoritative source is the complete frozen subtree:

`ai-workflow-evidence-auditor/`

Rebase its contents one directory level upward into the destination repository root when extraction is authorised.

Preserve exactly:

- `ai-workflow-evidence-auditor/.env.example` → `.env.example`
- `ai-workflow-evidence-auditor/.gitignore` → `.gitignore`
- `ai-workflow-evidence-auditor/AGENTS.md` → `AGENTS.md`
- `ai-workflow-evidence-auditor/README.md` → `README.md`
- `ai-workflow-evidence-auditor/package.json` → `package.json`
- `ai-workflow-evidence-auditor/tsconfig.json` → `tsconfig.json`
- `ai-workflow-evidence-auditor/fixtures/eval-001.input.json` → `fixtures/eval-001.input.json`
- `ai-workflow-evidence-auditor/src/audit.ts` → `src/audit.ts`
- `ai-workflow-evidence-auditor/src/env.ts` → `src/env.ts`
- `ai-workflow-evidence-auditor/src/index.ts` → `src/index.ts`
- `ai-workflow-evidence-auditor/src/schemas.ts` → `src/schemas.ts`
- `ai-workflow-evidence-auditor/tests/audit.test.ts` → `tests/audit.test.ts`
- `ai-workflow-evidence-auditor/tests/fixture.test.ts` → `tests/fixture.test.ts`
- `ai-workflow-evidence-auditor/tests/live-eval.test.ts` → `tests/live-eval.test.ts`

## 3.2 Required transformations

No application-code transformation is required for the initial extraction.

Do **not** supplement the destination with these older root-integrated copies:

- `lib/evidence-auditor/`
- `lib/__tests__/evidence-auditor.test.ts`
- `fixtures/evidence-auditor/`
- `scripts/audit-evidence.ts`
- `docs/evidence-auditor.md`
- root Evidence Auditor environment variables;
- root `package.json` `audit:evidence` integration.

Those paths are migration residue and become cleanup candidates only after the standalone destination validates successfully.

### `.github/`

There is no authoritative `.github/` subtree inside the standalone source package. Do not infer ownership of the root portfolio CodeQL workflow.

If CI is added during extraction implementation, the minimum CI behaviour must be exactly the non-billable validation commands below. CI must not run `npm run audit` or `npm run eval:live` with secrets by default.

### Visibility

Repository visibility remains a separate explicit decision. The package describes itself as private, but the source currently resides in a public repository. This manifest does not change visibility.

## 3.3 Minimum validation gate

From the extracted auditor root:

```bash
npm install
npm test
npm run build
```

Acceptance:

- all non-live tests pass;
- TypeScript build/type-check passes;
- no root portfolio or Able to Answer path is imported;
- input fixture remains `fixtures/eval-001.input.json` from the standalone package;
- `npm run audit` and `npm run eval:live` are **not** run as migration acceptance tests because they can make billable live API requests.

---

# 4. Mixed root-path disposition matrix

| Current source path | Portfolio | Able to Answer | Evidence Auditor | Remains profile/control / archive |
|---|---|---|---|---|
| `.env.example` | reconstruct `ATA_OPENAI_*` only | reconstruct `ATA_*` document/search settings only | use standalone `.env.example` | remove mixed source copy only after destinations validate |
| `.gitignore` | reconstruct Node/Next subset | reconstruct Python/SQLite subset | use standalone `.gitignore` | retain/reconstruct minimal profile ignore |
| `.github/PULL_REQUEST_TEMPLATE.md` | no | preserve | no | no |
| `.github/copilot-instructions.md` | no | preserve | standalone `AGENTS.md` governs | no |
| `.github/workflows/ci.yml` | no | preserve + remove `scripts/` lint path | no | no |
| `.github/workflows/control_pack_validation.yml` | no | preserve | no | no |
| `.github/workflows/codeql-debug.yml` | preserve | no | no inferred transfer | no |
| `.github/workflows/fork_manager.yml` | no | no | no | PROFILE |
| `.github/workflows/governance_sync.yml` | no | no | no | PROFILE |
| `.github/workflows/review_automation.yml` | no | no | no | PROFILE |
| `docs/` | none | none | use standalone README/docs only | archive/control; root auditor doc becomes residue |
| `lib/` | preserve portfolio files/tests only | no | no | root auditor subdir becomes residue |
| `scripts/` | none | none | standalone `src/index.ts` is CLI | Python control scripts remain PROFILE; `audit-evidence.ts` residue |
| `tests/` | `tests/openai.test.ts` | listed Python product tests | standalone tests only | `test_fork_inventory.py`, `test_review_bot.py` remain PROFILE |
| `package.json` | preserve minus `audit:evidence` | n/a | standalone package | no root package after portfolio extraction |
| `pyproject.toml` | n/a | preserve minus profile `governance` extras and profile-script Ruff rule | n/a | profile automation needs separate dependency repair before source removal |

---

# 5. Source/profile dependency blocker discovered during manifesting

The profile/control repository currently retains Python automation:

- `scripts/fork_inventory.py`
- `scripts/fork_sync.py`
- `scripts/generate_compliance_report.py`
- `scripts/gh_review_bot.py`
- `scripts/sync_studio_to_codex.py`
- `tests/test_fork_inventory.py`
- `tests/test_review_bot.py`
- `.github/workflows/fork_manager.yml`
- `.github/workflows/governance_sync.yml`
- `.github/workflows/review_automation.yml`

However, two retained profile workflows currently depend on the root Able to Answer packaging boundary:

- `fork_manager.yml` runs `pip install -e "."`;
- `governance_sync.yml` runs `pip install -e ".[governance]"`;
- the `governance` dependency group is currently declared in `pyproject.toml`, which belongs to Able to Answer after the split.

Therefore source cleanup cannot simply delete/move `pyproject.toml` after extraction without breaking profile-control automation.

**Required pre-cleanup repair:** define a minimal profile-control Python dependency contract (or replace those install steps with explicit script dependencies) before removing the Able to Answer `pyproject.toml` from `9TEVE-O/9TEVE-O`.

This is a repository-boundary repair, not application feature work.

---

# 6. Extraction acceptance sequence

When execution is later authorised:

1. Resolve the profile-control Python dependency blocker in §5.
2. Extract `ai-workflow-evidence-auditor` from its already self-contained subtree.
3. Run the auditor minimum validation gate.
4. Extract `able-to-answer` using the explicit Python test/workflow splits above.
5. Run the Able to Answer minimum validation gate.
6. Extract `evidence-first-portfolio` using the explicit `lib/`, `tests/`, package, environment and GitHub-workflow splits above.
7. Run the portfolio minimum validation gate.
8. Only after all three destinations pass, remove migrated executable code and duplicate auditor residue from `9TEVE-O/9TEVE-O`.
9. Repair the remaining profile README links/instructions and archive stale setup/architecture authority.
10. Close/supersede the already-classified PR queue only after the repository boundaries are stable.

## Manifest gate result

- Destination ownership: **RESOLVED**.
- Exact frozen source paths: **RECORDED**.
- Mixed-path transformations: **RECORDED**.
- Minimum validation gates: **RECORDED**.
- Additional mixed `tests/` ownership discovered and corrected: **RECORDED**.
- Profile-control packaging dependency: **BLOCKER IDENTIFIED**.
- Repository creation: **NOT PERFORMED**.
- File movement/deletion: **NOT PERFORMED**.
- PR mutation: **NOT PERFORMED**.

## Next gated action

Resolve only the profile-control Python dependency blocker created by the split: produce `PROFILE_CONTROL_DEPENDENCY_BOUNDARY_v0.1` that specifies the smallest post-split dependency/install contract required by `fork_manager.yml`, `governance_sync.yml`, and `review_automation.yml` without importing Able to Answer as infrastructure.

Do not create destination repositories or move files until that blocker is closed.