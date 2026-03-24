# 9TEVE-O Setup Plan

> Governance-grade personal infrastructure — AI tooling, automation pipelines, and integrations for the 9TEVE-O profile.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done — fully configured and live |
| 🔄 | In Progress — work underway, PR open or partially configured |
| 📋 | Planned — scoped, not yet started |

---

## 1. GitHub Profile

**Repo:** [`9TEVE-O/9TEVE-O`](https://github.com/9TEVE-O/9TEVE-O)

| Item | Status | Notes |
|------|--------|-------|
| Profile README — modern layout, bio, skills | 🔄 | [PR #35](https://github.com/9TEVE-O/9TEVE-O/pull/35) / [PR #36](https://github.com/9TEVE-O/9TEVE-O/pull/36) open for review |
| GitHub Stats badges (github-readme-stats) | 🔄 | Included in PR #35/#36 — dark theme, private commits |
| Top Languages card | 🔄 | Included in PR #35/#36 |
| Featured Projects table | 🔄 | 6 projects showcased: AI-Policy-Terms-Analyzer, SpiderID_APP, DeepResearch, Waver, personaplex, clawdbot-formal-models |
| Shields.io tech-stack badges | 🔄 | AI/ML, Automation, Web Performance, Security categories |
| Setup Status section → SETUP_PLAN.md | 🔄 | This PR |

---

## 2. MCP Servers

**Repo:** [`9TEVE-O/everything-claude-code`](https://github.com/9TEVE-O/everything-claude-code)

| Item | Status | Notes |
|------|--------|-------|
| ruflo MCP server — initial setup | ✅ | [PR #1](https://github.com/9TEVE-O/everything-claude-code/pull/1) merged |
| Claude Code integration config | ✅ | MCP server wired into Claude Code via `everything-claude-code` |
| Additional MCP servers (e.g. filesystem, fetch, git) | 📋 | Evaluate and add as needed |
| MCP server health checks / CI | 📋 | Automated validation of MCP config on push |

---

## 3. Google Drive

**Repo:** [`9TEVE-O/Projects-and-more-`](https://github.com/9TEVE-O/Projects-and-more-)

| Item | Status | Notes |
|------|--------|-------|
| Google Drive sync scripts | ✅ | [PR #13](https://github.com/9TEVE-O/Projects-and-more-/pull/13) — file sync automation |
| OAuth2 credential setup | ✅ | Configured via environment variables; `.env.example` provided |
| n8n webhook trigger for Drive events | ✅ | Trigger fires on file create/update in watched folders |
| Automation docs | ✅ | Integration guide included in PR #13 |
| Scheduled sync (cron / GitHub Actions) | 📋 | Periodic pull of Drive changes to local/repo state |

---

## 4. Slack Integration

**Repo:** [`9TEVE-O/Projects-and-more-`](https://github.com/9TEVE-O/Projects-and-more-)

| Item | Status | Notes |
|------|--------|-------|
| Slack incoming webhook configuration | ✅ | Webhook URL stored in env; notify scripts reference it |
| Google Drive → Slack notifications | ✅ | [PR #13](https://github.com/9TEVE-O/Projects-and-more-/pull/13) — Drive events surfaced in Slack channel |
| n8n workflow: Drive event → Slack message | ✅ | Workflow JSON included in PR #13 |
| Slack app / bot token (extended permissions) | 📋 | For richer message formatting, file sharing, slash commands |
| Bi-directional Slack ↔ GitHub notifications | 📋 | PR/issue events → Slack channel |

---

## 5. Automation Stack

| Item | Status | Notes |
|------|--------|-------|
| n8n self-hosted instance | ✅ | Core workflow engine running |
| Webhook endpoints (Drive → n8n → Slack) | ✅ | End-to-end pipeline live |
| Governance sync & reporting pipeline | 🔄 | [PR #33](https://github.com/9TEVE-O/9TEVE-O/pull/33) / [PR #34](https://github.com/9TEVE-O/9TEVE-O/pull/34) — CI workflow for cross-repo governance |
| GitHub Actions: lint + CI enforcement | 🔄 | [PR #31](https://github.com/9TEVE-O/9TEVE-O/pull/31) — repo hardening across all repos |
| Compliance report generation (`generate_compliance_report.py`) | ✅ | Script in `scripts/` |
| Studio → Codex sync (`sync_studio_to_codex.py`) | ✅ | Script in `scripts/` |
| GitHub review bot (`gh_review_bot.py`) | ✅ | Script in `scripts/` |

---

## 6. Upcoming / Planned

| Item | Status | Notes |
|------|--------|-------|
| **GitHub Mobile** app setup | 📋 | Configure notifications, PR reviews on mobile |
| **Slack mobile** app setup | 📋 | Ensure workspace + channels configured on phone |
| Additional MCP servers | 📋 | Candidates: `mcp-server-filesystem`, `mcp-server-fetch`, `mcp-server-git`, `mcp-server-brave-search` |
| Kilo for Slack — expanded workflows | 📋 | Trigger Kilo tasks from Slack messages / threads |
| Automated SETUP_PLAN.md status sync | 📋 | CI job that updates status badges from PR/issue state |
| Personal site / portfolio | 📋 | Static site referencing key projects and this setup |

---

## Reference Links

| Resource | URL |
|----------|-----|
| Profile repo | https://github.com/9TEVE-O/9TEVE-O |
| everything-claude-code | https://github.com/9TEVE-O/everything-claude-code |
| Projects-and-more- | https://github.com/9TEVE-O/Projects-and-more- |
| n8n | https://n8n.io |
| Claude Code MCP docs | https://docs.anthropic.com/en/docs/claude-code/mcp |
| Kilo for Slack | https://kilo.ai/features/slack-integration |

---

*Last updated: 2026-03-24*
