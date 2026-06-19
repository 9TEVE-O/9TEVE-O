# Codex Task 001 — Safe Intake README Scaffold

Version: v0.1
Status: task brief draft
Approval state: not executed
Executor: Codex
Reviewer: Steven Lees
Control reviewer: ChatGPT
Primary artefact: GLM-5.2 Safe Intake Operating Guide — 2026-06-19

## Objective

Create a README scaffold for a Safe Intake repository that explains the privacy-first intake workflow without processing raw sensitive data.

## Operating Boundary

This is a Codex setup workflow. GLM-5.2 is not replacing Codex.

- GLM-5.2 prepares reviewed build inputs.
- Codex executes controlled repository and build tasks from narrow task briefs.
- The Google Doc remains the authority log, operating manual, and session memory unless Steven Lees explicitly ratifies another artefact as canonical.
- Steven Lees remains the operator and decision owner.
- ChatGPT remains the librarian and control-boundary reviewer.

## Core Invariant

Raw or unreviewed sensitive content must not enter AI systems before human review and approval.

The critical boundary is not extraction alone. The critical boundary is indexing and downstream use.

## Scope

### In Scope

- Create or update `README.md` structure for a Safe Intake repository.
- Add a clear privacy warning.
- Explain the local-first / no-model-first intake pattern.
- Describe the human review gate before model use, indexing, or downstream processing.
- Add a minimum test checklist for the README scaffold.
- Keep the README as a scaffold only; do not implement ingestion, redaction, indexing, or model calls.

### Out of Scope

- Production deployment.
- Hosted model calls.
- Processing real sensitive documents.
- Implementing extraction, redaction, retrieval, audit, or persistence code.
- Adding dependencies, services, databases, queues, or infrastructure.
- Treating this draft task brief as ratified project canon.

## Required README Sections

The README scaffold should include these sections:

1. Project purpose.
2. Privacy-first warning.
3. Local-first / no-model-first workflow.
4. Human review and approval gate.
5. Approved derivative concept.
6. Blocked data classes for hosted model calls.
7. Audit trail expectations.
8. Minimum test checklist.
9. Current non-goals.
10. Approval status.

## Blocked Data Classes

The README must state that these data classes are blocked from hosted model calls unless reviewed, redacted, approved, and transformed into an approved derivative:

- Raw personal identifying information.
- Raw financial records.
- Raw health or medical records.
- Raw legal documents containing private party details.
- Secrets, credentials, tokens, or authentication material.
- Private communications not explicitly approved for model processing.
- Any document where the operator is unsure whether it contains sensitive material.

## Acceptance Criteria

- A README scaffold exists and is reviewable as plain Markdown.
- The README makes the no-raw-sensitive-content boundary explicit.
- The README distinguishes extraction from indexing and downstream use.
- The README states that hosted model calls require prior human review and approval.
- The README includes an approval status marker so an agent can visibly report progress if approval state is missing.
- The README does not include real sensitive content, example secrets, or production configuration.
- No application code, dependencies, or service configuration are changed.

## Validation Steps

Run the following checks after the README scaffold is created:

```bash
git diff -- README.md
python3 -m pytest tests/ -v
```

If the target repository has no Python test suite, replace the pytest command with the narrowest available repository validation command and record that substitution in the PR notes.

## Execution Notes

- Prefer the smallest safe README-only change.
- Do not infer approval where it is missing.
- If approval state is missing, add or preserve a visible `Approval state` line instead of proceeding as approved.
- Do not process, summarize, embed, or upload raw sensitive materials.
