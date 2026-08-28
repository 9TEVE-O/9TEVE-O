# AI Workflow Evidence Auditor

Private, tool-only TypeScript prototype for reviewing one bounded AI-assisted workflow against a controlled evidence set.

It returns seven structured outputs: workflow reconstruction, evidence and authority map, unsupported-claim register, reliability and governance risk register, unresolved-question register, prioritised corrective actions, and a decision-ready review report.

## Scope

This prototype intentionally has no widget, database, authentication system, public submission configuration, or external evidence retrieval. Human review is required before consequential use.

## Requirements

- Node.js 20.12+
- An OpenAI API key
- A saved, versioned Platform prompt containing the Core Review Prompt

The saved prompt must use `{{audit_input_json}}` as the complete bounded review package, use only the supplied controlled evidence, and never invent sources or approvals. The prompt text is deliberately not duplicated in this repository.

## Setup

```bash
npm install
cp .env.example .env
```

Set `OPENAI_API_KEY`, `OPENAI_AUDITOR_PROMPT_ID`, and `OPENAI_AUDITOR_PROMPT_VERSION` in `.env`. `OPENAI_AUDITOR_MODEL` is optional. Never commit `.env`.

## Test and type-check

These commands do not call the OpenAI API:

```bash
npm test
npm run build
```

## Run

This makes one billable Responses API request and writes the structured report to standard output:

```bash
npm run audit -- fixtures/eval-001.input.json
```

The request uses the saved prompt ID and numeric version, strict Zod-backed structured output, and `store: false`. Input validation rejects empty evidence sets, duplicate evidence identifiers, unknown fields, and blank required values before any API request is made.

## Optional live evaluation

With a configured `.env`, run:

```bash
npm run eval:live
```

The live test is skipped by the normal test suite. Do not enable it in untrusted forks or public CI jobs with secrets.
