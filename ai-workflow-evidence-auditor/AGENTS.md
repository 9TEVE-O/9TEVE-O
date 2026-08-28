# AGENTS.md

This directory is a standalone private TypeScript prototype.

- Install with `npm install` from this directory.
- Run non-billable validation with `npm test` and `npm run build`.
- Never run `npm run audit` or `npm run eval:live` unless a billable live OpenAI request is explicitly intended.
- Never commit `.env`, API keys, or saved prompt contents.
- Keep the tool free of widgets, databases, authentication, and public submission endpoints until explicitly requested.
