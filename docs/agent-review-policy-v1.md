# Agent Review Policy v1

## Purpose
This policy defines how AI agents may participate in pull request review, approval, commenting, commit generation, and merge preparation across repositories under this account.

The goal is not maximum automation. The goal is controlled, low-noise, high-signal automation with clear authority boundaries.

This policy closes the gaps identified in prior review:
- too many bots posting to too many surfaces
- duplicated findings across bots
- status noise mixed with real review signal
- unclear ownership of review, approval, and commit actions
- weak side-effect ranking
- missing terminal semantics and enforcement boundaries
- inconsistent review quality across branch types, quotas, and unsupported files

---

# 1. Core operating model

## 1.1 Single-reviewer principle
Only one AI reviewer should be considered the primary authoritative reviewer for a given repository at a time.

Other bots may be allowed for narrow supporting roles, but they must not duplicate the primary reviewer’s role.

### Allowed pattern
- 1 primary reviewer bot for inline code findings
- optional 1 summary bot for PR summary only
- optional human-invoked helper bots for explicit commands only

### Disallowed pattern
- multiple bots auto-posting review findings on every PR
- multiple bots posting overlapping summaries and review comments by default
- bots posting marketing/status noise that obscures actionable review

---

# 2. Roles by agent

## 2.1 Codex
**Role:** high-signal structural reviewer and targeted code review assistant

**Allowed:**
- inline review comments
- review summary when findings exist
- human-invoked follow-up such as `@codex address that feedback`
- draft implementation suggestions

**Not allowed:**
- automatic approval
- automatic merge
- direct commit to protected/default branch
- review spam when quota is exhausted

**Operational note:** if quota is exhausted, Codex must not be treated as the guaranteed reviewer.

## 2.2 CodeRabbit
**Role:** optional secondary quality gate for walkthroughs, bounded inline findings, and lightweight pre-merge checks

**Allowed:**
- inline review comments
- bounded pre-merge checks
- summary only if configured to avoid noise

**Not allowed:**
- duplicate review role if Codex is primary and already active
- branch-skip noise on every PR
- unsolicited marketing/footer clutter if suppressible in config

**Operational note:** if non-default target branches are common, CodeRabbit must be configured for that pattern or demoted to manual invocation only.

## 2.3 Gemini Code Assist
**Role:** summary or spot-review assistant

**Allowed:**
- PR summary
- explicit command-based review
- inline comments if chosen as primary reviewer in a repo

**Not allowed:**
- duplicating the primary reviewer by default
- posting low-value summary-only comments when another agent already summarised the PR

## 2.4 Copilot reviewer
**Role:** optional helper only

**Allowed:**
- command-based review or suggestion workflows

**Not allowed:**
- primary reviewer role unless performance is proven stable in the repo
- auto-noise when unable to review files

---

# 3. Review surface policy

## 3.1 Preferred review surface
Use **inline review comments** for actionable code findings.

## 3.2 Allowed top-level PR comments
Top-level comments are allowed only for:
- concise review summary
- one-time repository policy reminder
- explicit human-invoked command output
- approval or blocked-state explanation when necessary

## 3.3 Disallowed top-level comment types
Disallow or suppress where possible:
- “review skipped” noise
- unsupported-file spam
- quota/status chatter unless it materially changes the review decision
- marketing or share prompts
- repeated summaries from multiple bots

---

# 4. Side-effect levels
Every agent action must be classified before enablement.

## L0 — Read only
Examples:
- read PR diff
- read comments
- inspect file patch
- inspect checks

**Default:** allowed

## L1 — Analyse / summarise
Examples:
- PR summary
- changelog summary
- risk summary
- review classification

**Default:** allowed if non-duplicative

## L2 — Comment / suggest
Examples:
- inline review comment
- top-level summary comment
- reply to review thread

**Default:** allowed only under surface policy and anti-duplication rules

## L3 — Draft artefact creation
Examples:
- draft PR body update suggestion
- draft issue
- draft follow-up task list
- draft patch proposal

**Default:** allowed with traceability

## L4 — Repository mutation
Examples:
- create branch
- create commit on non-protected branch
- open draft PR
- update docs/config on agent branch

**Default:** human-approved enablement only

## L5 — High-risk mutation
Examples:
- approve PR
- request changes as authoritative gate
- merge PR
- delete files
- change permissions
- modify workflow/security/policy/infrastructure files without explicit human approval

**Default:** blocked

---

# 5. Approval and merge policy

## 5.1 Approval
AI agents may review, classify, and recommend.
They do not hold final approval authority.

### Rule
- Agents may comment
- Agents may recommend approve / request changes / draft follow-up
- Human retains approval authority

## 5.2 Merge
No AI agent may merge by default.

### Rule
- create branch: allowed only for enabled agents
- create PR: allowed only for enabled agents
- merge PR: human approval required
- protected branch mutation: blocked for agents

---

# 6. Review class policy

## 6.1 Auto-review eligible classes
These are appropriate for agent review by default:
- lint and formatting issues
- duplicate or near-duplicate helper code
- dead imports / dead locals
- obvious unused code warnings
- test hygiene suggestions
- API contract drift detection
- logging / observability gaps
- config inconsistency detection
- documentation drift
- simple performance footguns

## 6.2 Draft-PR eligible classes
These may be proposed in a draft PR or patch, not directly merged:
- dead code cleanup
- safe refactors
- test additions
- null/type-safety cleanup
- dependency cleanup
- simple performance cleanup

## 6.3 Human-review-required classes
These must remain human-gated:
- auth and permission logic
- state machine transitions
- approval logic
- external notification/send logic
- billing/payment
- deletion logic
- security-sensitive changes
- infrastructure and deployment policy
- compliance logic
- schema/data migration semantics

---

# 7. Anti-duplication rules

## 7.1 One finding, one owner
If one bot has already posted a materially identical finding, other bots should not restate it.

## 7.2 Summary suppression
If a PR already has one usable summary comment, other summary bots should be disabled or manual-only.

## 7.3 Status suppression
If a bot cannot review due to branch, quota, unsupported files, or config, that status should not flood the main PR discussion unless it changes the review decision.

---

# 8. Branch and trigger policy

## 8.1 Review triggers
Preferred automatic triggers:
- PR opened
- draft marked ready
- significant diff update

Optional manual triggers:
- `@codex review`
- `@codex address that feedback`
- `@coderabbitai review`
- `/gemini review`

## 8.2 Branch compatibility
If a reviewer cannot handle non-default base branches, one of two actions is required:
- configure it properly
- demote it to manual-only

A reviewer that silently or noisily skips common branch patterns must not be treated as required infrastructure.

---

# 9. Runtime control contract for review agents
Every enabled review agent should conceptually expose the following fields, whether via actual implementation or policy mapping:

- `run_status`
- `actor_type`
- `approval_status`
- `allowed_actions`
- `side_effect_level`
- `policy_decision`
- `terminal_reason`
- `wake_event`
- `validator_result`
- `idempotency_key`
- `trace_id`

## 9.1 Terminal semantics
When a review run reaches terminal state, no further unsolicited comments should be posted.

Terminal states include:
- review_completed
- review_skipped
- quota_blocked
- unsupported_diff
- policy_denied

Only explicit human wake events should restart the review agent.

---

# 10. Failure taxonomy
Every meaningful failed or degraded review outcome should map to a clear class:
- `quota_exhausted`
- `branch_policy_skip`
- `unsupported_file_types`
- `duplicate_finding_suppressed`
- `no_actionable_findings`
- `review_surface_denied`
- `policy_denied_high_risk_action`
- `human_review_required`
- `agent_commit_blocked`

This is preferable to vague “review failed” or “unable to review” messaging.

---

# 11. Repository-level default policy
Unless overridden per repository:

## Primary reviewer
Codex or one chosen alternative, but not multiple primary reviewers.

## Secondary reviewers
Manual-only or summary-only.

## Default review actions
- allow L0-L2
- allow L3 if traceable and human-requested
- block L4-L5 unless explicitly enabled

## Merge rule
Never merge without human approval.

## Branch rule
Never write directly to default/protected branch.

## Noise rule
Suppress repeated summaries, skipped-review chatter, and marketing comments where config allows.

---

# 12. Immediate implementation steps

1. Choose one primary reviewer per repo.
2. Demote other bots to summary-only or manual-only.
3. Disable or suppress skipped-review and marketing/status comments where possible.
4. Keep inline comments as the default actionable surface.
5. Block agent approval and merge by default.
6. Allow branch creation and draft PR creation only for low-risk enabled workflows.
7. Add repository labels or metadata for:
   - `AI_REVIEW_PRIMARY`
   - `HUMAN_REVIEW_REQUIRED`
   - `BLOCKED_AGENT_COMMIT`
8. Standardise PR templates so titles and summaries are less generic than “Initial plan”.

---

# 13. Decision for current setup
Based on the recent audit, the current setup behaves like a bot pile-on rather than a controlled review pipeline.

### Therefore
- do not treat all enabled bots as equal reviewers
- do not rely on quota-limited or branch-skipping bots as mandatory gates
- do not allow duplicated comment streams to stand as the permanent workflow

The next correct move is to reduce reviewer count, assign explicit roles, and enforce action boundaries.

---

# Proposed acceptance criteria for Policy v1
- One repo has one primary AI reviewer
- No duplicate summary bots on the same PR by default
- Inline comments are preferred over top-level chatter
- Agent merge remains blocked
- Human approval remains required
- Non-default-branch behaviour is configured or demoted
- Review noise is materially reduced

---

If accepted, next follow-up should convert this into:
1. per-repo reviewer matrix
2. side-effect policy file
3. PR template update
4. bot configuration cleanup checklist
