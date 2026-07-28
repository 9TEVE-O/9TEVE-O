# AI Workflow Evidence Auditor

Private, tool-only prototype for reviewing one bounded AI-assisted workflow against a controlled evidence set. It produces a workflow reconstruction, evidence and authority map, unsupported-claim register, reliability and governance risk register, unresolved-question register, prioritised corrective actions, and decision-ready report.

The prototype intentionally has no widget, database, authentication system, public submission endpoint, or external evidence retrieval.

## Requirements

- Node.js 22.6 or later (the CLI uses Node's TypeScript type stripping)
- An OpenAI API key
- A saved, versioned OpenAI Platform prompt

## Saved prompt

Create the auditor prompt in the OpenAI Platform rather than copying it into this repository. The prompt must accept `{{audit_input_json}}` and instruct the model to:

- treat that value as the complete bounded review package;
- use only the supplied controlled evidence;
- never invent evidence, citations, records, or approvals; and
- populate all seven report sections defined by the response schema.

Keep the prompt ID and immutable version together so an evaluation can be reproduced.

## Configure

```bash
cp .env.example .env
export OPENAI_API_KEY="..."
export OPENAI_AUDITOR_PROMPT_ID="pmpt_..."
export OPENAI_AUDITOR_PROMPT_VERSION="1"
export OPENAI_AUDITOR_MODEL="gpt-5.5" # optional; this is the default
```

The CLI reads process environment variables; it does not load `.env` automatically. Never commit an API key.

## Validate locally

These checks do not call OpenAI:

```bash
npm test -- lib/__tests__/evidence-auditor.test.ts
npm run typecheck
```

## Run the representative evaluation

The following command makes one billable Responses API request and prints the JSON report to standard output:

```bash
npm run audit:evidence -- fixtures/evidence-auditor/eval-001.input.json
```

The request sets `store: false`. The tool validates the input locally, passes it to the saved prompt as `audit_input_json`, and requests strict JSON-schema output. Review output with a human before using it for a consequential decision.
