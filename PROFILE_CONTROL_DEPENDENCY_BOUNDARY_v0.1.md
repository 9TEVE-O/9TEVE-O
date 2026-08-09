# PROFILE_CONTROL_DEPENDENCY_BOUNDARY_v0.1

**Status:** BOUNDARY COMPLETE — NO WORKFLOW OR PACKAGING CHANGES EXECUTED  
**Repository:** `9TEVE-O/9TEVE-O`  
**Frozen source commit:** `d5f0c5914e891b9d702993db02bd9fea40114d27`  
**Parent:** `REPOSITORY_BOUNDARY_EXTRACTION_MANIFEST_v0.1.md`  
**Date:** 2026-08-10

## Goal

Define the smallest independent dependency and installation contract required by the profile/control repository for:

- `.github/workflows/fork_manager.yml`
- `.github/workflows/governance_sync.yml`
- `.github/workflows/review_automation.yml`

The result must remove their dependency on the Able to Answer `pyproject.toml` without redesigning the workflows or application capabilities.

## Decision

The profile/control repository does **not** require a Python package.

It should not retain, copy, or reconstruct the Able to Answer `pyproject.toml` merely to support profile/control scripts.

The profile/control runtime dependency contract is a plain requirements file containing only the third-party libraries actually imported by the retained profile/control scripts:

`requirements-profile-control.txt`

```text
requests>=2.31,<3
notion-client>=2.2,<3
```

For local/offline validation of the retained profile/control unit tests, use a separate development requirements file:

`requirements-profile-control-dev.txt`

```text
-r requirements-profile-control.txt
pytest>=8,<9
```

No editable install (`pip install -e .`) is required for the three workflows.

## Evidence by workflow

### 1. `fork_manager.yml`

Retained scripts:

- `scripts/fork_inventory.py`
- `scripts/fork_sync.py`

Both scripts use only the Python standard library for their own execution. They import modules such as `json`, `logging`, `os`, `subprocess`, `urllib`, `dataclasses`, `datetime`, `pathlib` and typing primitives. They do not import Able to Answer code or a third-party Python package.

Therefore the current workflow step:

```text
pip install -e "." -q
```

is unnecessary and should be removed when implementation is authorised.

The fork workflow's external command execution against cloned repositories (`npm`, `pip`, `pytest`, `cargo`, and similar tools) is behaviour of `fork_sync.py`, not a Python package dependency of the profile repository itself.

### 2. `review_automation.yml`

Retained script:

- `scripts/gh_review_bot.py`

The script uses only the Python standard library, including `json`, `logging`, `os`, `sys`, `urllib` and typing primitives.

The current workflow already runs the script directly and does not install the root package.

Therefore no runtime package installation step is required for `review_automation.yml`.

### 3. `governance_sync.yml`

Retained scripts:

- `scripts/sync_studio_to_codex.py`
- `scripts/generate_compliance_report.py`

Third-party imports actually required by these scripts are:

- `requests` — used directly by `sync_studio_to_codex.py`;
- `notion_client` — imported lazily when Notion integration is exercised by either governance script.

The scripts do not import Able to Answer modules.

`python-dotenv` is not imported by either retained governance script and is therefore excluded from the profile/control dependency contract.

When implementation is authorised, each current governance workflow step using:

```text
pip install -e ".[governance]"
```

should become:

```text
python -m pip install -r requirements-profile-control.txt
```

No Able to Answer package installation should occur in the profile/control repository.

## File ownership contract

### Retain in the profile/control repository

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
- `FORKS_INVENTORY.md`

### Add during authorised implementation

- `requirements-profile-control.txt`
- `requirements-profile-control-dev.txt`

### Do not retain for profile/control dependency purposes

- Able to Answer `pyproject.toml`
- Able to Answer `Makefile`
- Able to Answer `src/able_to_answer/`
- Able to Answer Python tests
- Able to Answer `.github/workflows/ci.yml`
- Able to Answer `.github/workflows/control_pack_validation.yml`

## Exact workflow install transformations

| Workflow | Current dependency behaviour | Target dependency behaviour |
|---|---|---|
| `fork_manager.yml` | `pip install -e "." -q` in fork jobs | **No profile Python dependency install** |
| `review_automation.yml` | no package install | **No change required** |
| `governance_sync.yml` | `pip install -e ".[governance]"` | `python -m pip install -r requirements-profile-control.txt` |

These are implementation instructions only. This document does not edit the workflows.

## Validation contract

Before removing Able to Answer packaging from the profile repository, the profile/control boundary should pass the following non-network validation from a clean Python environment:

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

Acceptance:

- requirements install succeeds without installing Able to Answer;
- all five retained scripts compile;
- the retained profile/control unit tests pass;
- no retained profile/control script imports `able_to_answer`;
- no retained profile/control workflow invokes `pip install -e .` or `pip install -e ".[governance]"` after implementation;
- `pyproject.toml` can be removed from the profile repository after Able to Answer extraction without breaking these three workflows' Python dependency resolution.

## Residual data dependency — not a packaging dependency

`generate_compliance_report.py` currently reads a SQLite database selected by `ATA_DB_PATH`, defaulting to `able_to_answer.sqlite3`, and queries the `audits` table.

This is a **data/schema input dependency**, not a Python packaging dependency.

The dependency-boundary decision therefore separates two claims:

1. **Python packaging independence:** resolved by the requirements-file contract in this document.
2. **Compliance-report data-source independence:** not resolved by this document.

Do not copy Able to Answer source or packaging back into the profile repository to satisfy this data dependency.

A later bounded decision may either:

- provide the compliance report with an explicit external audit-data input;
- redefine the report against a profile-owned data source; or
- retire the report if the old governance integration is no longer active.

No such redesign is authorised here.

## Additional post-extraction review item

`gh_review_bot.py` currently contains path classifications that name Able to Answer-specific files such as `pyproject.toml`, `src/able_to_answer/core/config.py`, and `src/able_to_answer/control_plane/policy.py`.

Those strings do not create a Python dependency, so they do not block packaging separation. After repository extraction, however, the review policy path set should be re-baselined against the final profile/control repository tree rather than retaining stale Able to Answer path semantics.

That is a bounded review-policy cleanup, not part of this dependency contract.

## Gate result

Profile/control packaging boundary: **RESOLVED**.  
Profile/control Python package required: **NO**.  
Runtime third-party dependencies: **`requests`, `notion-client` only**.  
Development-only dependency for retained tests: **`pytest`**.  
Able to Answer editable install required: **NO**.  
Workflow edits: **NOT PERFORMED**.  
Requirements files: **NOT CREATED**.  
Able to Answer extraction: **NOT PERFORMED**.

## Next gated action

Prepare `REPOSITORY_BOUNDARY_EXECUTION_PLAN_v0.1` as a transaction-style migration sequence using the frozen source and the completed manifests.

It should specify:

1. destination repository creation/visibility decisions;
2. history-preserving extraction method for each destination;
3. exact first commits/transformations from the extraction manifest;
4. profile-control dependency repair from this document;
5. validation checkpoints before any source deletion;
6. source/profile cleanup only after all destination gates pass;
7. final link/instruction repair and independent boundary verification.

Do not create destination repositories, edit workflows, remove packaging, delete source paths, or close PRs during the execution-plan pass.