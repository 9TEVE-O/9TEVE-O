# Steven Lees Personal AI Command Library v1.0

**Status:** Approved working command library  
**Purpose:** Reusable conversational commands for progressing, reviewing, governing, building, testing, researching, closing, and operating AI-assisted work without manufacturing unnecessary follow-up work.

## Operating rule

When one of these commands is used, treat it as an execution instruction over the current conversation, project, supplied files, connected sources, or explicitly named scope.

Preserve approved decisions, canonical artefacts, established project boundaries, completed work, evidence states, and unresolved gates. Do not create new work merely because more work could theoretically be done.

When appropriate distinguish: **CONFIRMED / PROPOSED / UNRESOLVED / BLOCKED / NEXT ACTION / DONE**.

---

## 1. `/next`

**Purpose:** Determine what should happen from the current conversational or project state.

```text
/next

Assess the current state of this conversation and determine what should happen next.

Do not invent work merely to keep the conversation going.

Choose the most appropriate state:

1. NEXT ACTION — there is a clear worthwhile next step. Give me the single best next action.
2. NEEDS ME — progress is blocked on a decision, input, approval, file, access, or action from me. Tell me exactly what you need.
3. CONTINUE — there is unfinished work you can complete now without further input. Continue it.
4. GATE — we have reached a decision, approval, validation, testing, or verification point. State exactly what must be established before proceeding.
5. PARK — the work remains valid but there is no reason to continue it now. State the condition that would justify reopening it.
6. DONE — the intended objective has been completed. Identify the resulting artefact, decision, or established state.
7. CLOSE — there is no useful remaining action in this conversation. Recommend closure and state the appropriate closeout condition.

Preserve existing approvals, scope boundaries, canonical decisions, completed work, and known evidence.
Do not reopen completed work or expand scope merely to manufacture a next step.

End with exactly one clear line:
NEXT: <single action, condition, or CLOSE>
```

## 2. `/goal <condition>`

**Purpose:** Define what “done” means before doing more work.

```text
/goal <condition>

Establish the governing goal for the current work.

Identify:
OUTCOME — What end state are we trying to reach?
COMPLETION CONDITION — What observable evidence or condition will prove the goal has been achieved?
SCOPE — What work is permitted in pursuit of the goal?
EXCLUSIONS — What must not be expanded, changed, built, investigated, or reopened?
DEPENDENCIES — What must already exist or become available?
STOP CONDITION — At what point should work stop rather than continuing into optional improvements?

Do not begin unrelated implementation work.

End with:
GOAL: <one-sentence governing goal>
DONE WHEN: <observable completion condition>
```

Short form: `/goal <the condition that must become true>`

## 3. `/status`

**Purpose:** Find out where a project or conversation actually stands.

```text
/status

Determine the current state of this work using only established information.

Report:
CURRENT OBJECTIVE
CURRENT STATE
CONFIRMED — Decisions, artefacts, requirements, or work already established.
OPEN — Unresolved decisions, incomplete tasks, missing evidence, or outstanding dependencies.
BLOCKED — Anything preventing legitimate progress.
SUPERSEDED — Anything that should no longer govern the work.
NEXT PERMITTED ACTION — The next action allowed by the current state and scope.

Do not propose new projects or optional enhancements.
If the work is already complete, say so explicitly.

End with:
STATE: ACTIVE / BLOCKED / PARKED / COMPLETE / CLOSED / STATUS UNCONFIRMED
NEXT: <single next action or NONE>
```

## 4. `/review`

**Purpose:** Perform a normal professional review without reopening the whole project.

```text
/review

Review the current artefact, plan, specification, implementation, argument, or decision.

Assess:
1. correctness;
2. completeness;
3. internal consistency;
4. scope adherence;
5. unsupported assumptions;
6. implementation risks;
7. missing dependencies;
8. unclear language;
9. evidence quality;
10. whether it is ready for its intended next stage.

Separate findings into:
PASS — Material that should remain unchanged.
REPAIR — Specific defects that should be corrected.
QUESTION — Material that cannot be resolved from available evidence.
OPTIONAL — Improvements that are genuinely optional and must not block progress.

Do not redesign the work merely because another approach exists.

End with:
REVIEW RESULT: PASS / PASS WITH MINOR REPAIRS / REVISE / BLOCKED
```

## 5. `/ultrareview`

**Purpose:** Perform a deep, adversarial review of important work.

```text
/ultrareview

Perform a rigorous adversarial review of the current work.

Assume the work may contain subtle contradictions, false confidence, hidden dependencies, stale assumptions, scope drift, implementation gaps, weak evidence, or controls that look stronger on paper than they are in practice.

Review across:
1. objective alignment;
2. architecture;
3. requirements;
4. authority boundaries;
5. safety and failure behaviour;
6. data and evidence;
7. implementation feasibility;
8. testing adequacy;
9. operational reality;
10. maintainability;
11. security;
12. privacy;
13. observability;
14. rollback and recovery;
15. commercial or user-facing claims;
16. unresolved dependencies;
17. contradictions with approved decisions;
18. unnecessary complexity;
19. missing stop conditions;
20. whether this work should exist at all in its current form.

Classify every substantive finding:
CRITICAL — Must be resolved before proceeding.
MAJOR — Material weakness but not necessarily a complete stop.
MINOR — Worth correcting but does not threaten the core work.
OBSERVATION — Useful information with no required action.
FALSE POSITIVE — Something that initially appears problematic but is adequately controlled.

Do not manufacture problems simply to make the review appear rigorous.

End with:
OVERALL: PASS / PASS WITH CONDITIONS / REVISE / STOP
TOP PRIORITY: <single highest-value action>
```

## 6. `/resolve`

```text
/resolve

Resolve the currently identified issues using the strongest available evidence and existing project constraints.

For each unresolved item:
ISSUE — What exactly requires resolution?
OPTIONS — What legitimate alternatives exist?
EVIDENCE — What supports or weakens each alternative?
DECISION — What should now govern the work?
CONSEQUENCE — What changes as a result?
STATUS — RESOLVED / DEFERRED / BLOCKED / REQUIRES USER DECISION

Prefer the smallest decision that allows legitimate progress.
Do not expand scope while resolving a bounded issue.

At the end, produce:
RESOLVED DECISIONS
REMAINING OPEN DECISIONS
NEXT PERMITTED ACTION
```

## 7. `/decide`

```text
/decide

Determine whether sufficient information now exists to make the current decision.

If yes:
State the decision clearly.
Explain the decisive evidence.
State the main trade-off being accepted.
State what this decision does not establish.
Identify any condition that would justify revisiting it.

If no:
Do not continue general analysis.
Identify the exact missing information required to make the decision.
Distinguish essential information from merely useful information.

End with:
DECISION: <decision or NOT YET DECIDABLE>
NEXT: <single required action>
```

## 8. `/gate`

```text
/gate

Treat the current stage as a controlled gate.

Define:
GATE NAME
PURPOSE
ENTRY STATE — What must already be true before this gate is valid?
REQUIRED EVIDENCE — What must be demonstrated?
ACCEPTANCE CRITERIA — What must pass?
ZERO-TOLERANCE CONDITIONS — What automatically blocks progression?
UNRESOLVED ITEMS — What remains unknown?
EXIT STATES — PASS / PASS WITH CONDITIONS / FAIL / BLOCKED
PERMITTED NEXT ACTION — What may occur after each exit state?

Do not perform work belonging to a later gate before this gate has been passed.
```

## 9. `/plan`

```text
/plan

Produce the smallest complete execution plan for the approved objective.

Separate:
CONFIRMED REQUIREMENTS
IMPLEMENTATION DECISIONS
UNRESOLVED CHOICES
DEPENDENCIES
WORK SEQUENCE
VERIFICATION
STOP CONDITIONS

For each work step include:
INPUT
ACTION
OUTPUT
ACCEPTANCE CONDITION

Order work so that high-risk assumptions are tested before expensive implementation.
Do not add features or future phases that are unnecessary to achieve the approved goal.

End with:
FIRST PERMITTED STEP: <one concrete step>
```

## 10. `/build`

```text
/build

Implement the currently approved next step.

Use the existing specification, decisions, scope boundaries, architecture, and acceptance criteria as authoritative.
Do not redesign the product while implementing it.

Before changing anything, identify:
BUILD TARGET
INPUTS
GOVERNING REQUIREMENTS
FILES OR COMPONENTS AFFECTED
ACCEPTANCE TEST

Then perform the implementation.

After implementation report:
CHANGED
NOT CHANGED
TEST RESULT
KNOWN LIMITATIONS
EVIDENCE
NEXT PERMITTED STEP

If implementation exposes a genuine architectural contradiction, stop at that contradiction rather than silently changing the architecture.
```

## 11. `/test`

```text
/test

Test the current artefact, implementation, prompt, workflow, model, feature, or claim against its established requirements.
Do not repair failures during the initial test unless explicitly instructed.

Define:
TEST SUBJECT
REQUIREMENTS UNDER TEST
TEST CASES
EXPECTED RESULT
OBSERVED RESULT
PASS / FAIL
EVIDENCE

Include where relevant:
normal cases;
boundary cases;
known historical failures;
adversarial cases;
negative cases;
stop/refusal behaviour.

At the end report:
PASSED
FAILED
NOT TESTABLE
TEST VERDICT

Do not convert a partial test into a claim of overall production readiness.
```

## 12. `/verify`

```text
/verify

Verify the specific claim, result, implementation, state, or artefact currently under discussion.

Distinguish:
OBSERVED — Directly demonstrated.
SUPPORTED — Reasonably established by available evidence.
INFERRED — Likely but not directly demonstrated.
UNVERIFIED — Not enough evidence.
CONTRADICTED — Evidence conflicts with the claim.

Identify the source of evidence for every material conclusion.
Do not upgrade evidence strength through wording.
Do not treat a successful demonstration in one environment as proof of production behaviour in another.

End with:
VERIFICATION RESULT: VERIFIED / PARTIALLY VERIFIED / NOT VERIFIED / CONTRADICTED
```

## 13. `/evidence`

```text
/evidence

Audit the evidence supporting the current claim, decision, system state, or readiness classification.

Identify:
CLAIM
REQUIRED EVIDENCE
AVAILABLE EVIDENCE
EVIDENCE QUALITY
MISSING EVIDENCE
CONTRADICTORY EVIDENCE
PROVENANCE
REPRODUCIBILITY

Determine whether the evidence establishes:
concept;
candidate;
validated behaviour;
controlled test behaviour;
production readiness;
or none of these.

Do not treat documentation, intended design, or successful code generation as execution evidence.

End with:
EVIDENCE STATE: SUFFICIENT / PARTIAL / INSUFFICIENT / CONTRADICTORY
```

## 14. `/research <question>`

```text
/research <question>

Research the specified question using current authoritative sources where available.

Start by defining:
RESEARCH QUESTION
DECISION THIS RESEARCH SUPPORTS
SCOPE
SOURCE PRIORITY
EXCLUSIONS

Separate findings into:
ESTABLISHED — Strongly supported facts.
EMERGING — Recent or incomplete evidence.
CONTESTED — Credible disagreement exists.
UNKNOWN — The available evidence does not establish an answer.

For material claims, preserve source provenance.
Do not allow interesting adjacent discoveries to expand the research scope.

Finish with:
ANSWER
CONFIDENCE
REMAINING UNCERTAINTY
DECISION IMPACT
NEXT ACTION, if any
```

## 15. `/excavate <scope>`

```text
/excavate <scope>

Inspect the specified body of work and determine what still matters.

Classify discovered material into:
ACTIVE — Still relevant and has a legitimate next action.
COMPLETE — Objective achieved. No further work required.
PARKED — Potentially useful but no current reason to continue.
SUPERSEDED — Replaced by a later decision, artefact, or implementation.
REFERENCE — Useful evidence, pattern, proof of work, or historical material.
DISPOSABLE — No meaningful future value.
UNKNOWN — Insufficient information to classify safely.

For ACTIVE items identify:
current objective;
last established state;
open dependency;
next permitted action.

Do not reactivate old projects merely because they exist.

End with:
ACTIVE NOW
SAFE TO STOP CARRYING
NEXT: <highest-value legitimate continuation>
```

## 16. `/ingest`

```text
/ingest

Enter Information Ingest Mode.

I am going to provide material across one or more messages.

During ingestion:
1. receive the material;
2. preserve important structure and source distinctions;
3. do not begin substantive analysis;
4. do not prematurely summarize;
5. do not propose solutions;
6. do not infer that the dump is complete;
7. identify obvious missing or corrupted material only when necessary.

Acknowledge each batch briefly.
Remain in ingest mode until I issue:
/process
```

## 17. `/process`

```text
/process

Exit Information Ingest Mode and process all material supplied since /ingest.

First reconstruct the information into a coherent evidence base.
Then identify:
KEY FACTS
DECISIONS
CONSTRAINTS
CONTRADICTIONS
DEPENDENCIES
OPEN QUESTIONS
IMPORTANT SOURCES
ACTIONABLE ITEMS
NOISE OR DUPLICATION

Do not silently resolve contradictions.
Do not reactivate old work unless the supplied material establishes that it remains active.

Conclude with:
CURRENT STATE
MOST IMPORTANT FINDING
NEXT PERMITTED ACTION
```

## 18. `/compare <A> vs <B>`

```text
/compare <A> vs <B>

Compare the named options against the requirements of the current task.

First establish the comparison criteria from the actual objective.
Then compare:
fitness for purpose;
capability;
constraints;
complexity;
cost where relevant;
operational burden;
security;
privacy;
maintainability;
reversibility;
evidence quality;
known limitations;
switching cost.

Separate factual differences from judgment calls.
Do not manufacture a winner where the correct answer depends on priorities.

End with:
DECISION-RELEVANT DIFFERENCES
TRADE-OFF
WHAT WOULD CHANGE THE DECISION
```

## 19. `/risk`

```text
/risk

Perform a bounded risk analysis of the current proposal, system, workflow, or decision.

Identify risks across:
technical;
operational;
security;
privacy;
data;
AI/model behaviour;
human factors;
legal or compliance where relevant;
dependency failure;
vendor/platform dependency;
commercial claims;
recovery and rollback.

For each risk provide:
RISK
CAUSE
CONSEQUENCE
LIKELIHOOD — Use qualitative language only where reliable estimation is possible.
IMPACT
EXISTING CONTROL
CONTROL GAP
RECOMMENDED TREATMENT
RESIDUAL RISK

Distinguish hypothetical possibilities from credible material risks.

End with:
TOP MATERIAL RISKS
BLOCKING RISKS
ACCEPTABLE RESIDUAL RISKS
```

## 20. `/approve`

```text
/approve

Record approval of the specific current artefact, decision, specification, or state.

Identify exactly:
APPROVED ITEM
VERSION OR IDENTIFIER
APPROVED SCOPE
WHAT THIS APPROVAL ESTABLISHES
WHAT THIS APPROVAL DOES NOT ESTABLISH
KNOWN CONDITIONS
OPEN ITEMS THAT REMAIN OPEN
NEXT PERMITTED STAGE

Do not interpret approval of one artefact as approval of future implementation, deployment, production use, or adjacent work unless explicitly included.
```

## 21. `/approved/canonical/active`

```text
/approved/canonical/active

Treat the current identified artefact, doctrine, decision, specification, architecture, workflow, or control as:
APPROVED — Explicitly accepted.
CANONICAL — The governing version unless explicitly superseded.
ACTIVE — Applicable to current work.

Record:
NAME
VERSION / DATE
GOVERNING CONTENT
SCOPE OF AUTHORITY
DEPENDENCIES
BOUNDARIES
SUPERSEDED MATERIAL
OPEN ITEMS
NEXT PERMITTED ACTION

Do not extend canonical status to surrounding discussion or optional ideas that were not explicitly approved.
```

## 22. `/park`

```text
/park

Pause the current work without classifying it as completed or abandoned.

Record:
CURRENT STATE
WHY IT IS BEING PARKED
LAST CONFIRMED ARTEFACT OR DECISION
OPEN DEPENDENCIES
RE-ENTRY CONDITION
NEXT ACTION WHEN REOPENED

Do not continue background development or generate new follow-up tasks.

End with:
STATE: PARKED
REOPEN WHEN: <specific trigger>
```

## 23. `/archive`

```text
/archive

Classify the current project, artefact, experiment, or workstream as archived reference material.

Record:
WHAT IS BEING ARCHIVED
FINAL KNOWN STATE
WHY IT IS NO LONGER ACTIVE
WHAT REMAINS USEFUL
WHAT MUST NOT BE TREATED AS CURRENT
REACTIVATION CONDITION

Archiving does not mean the work succeeded, failed, or was completed unless that state was independently established.

End with:
STATE: ARCHIVED
```

## 24. `/close`

```text
/close

Apply the Close Chat Protocol.

Determine:
WHAT WAS ACCOMPLISHED
APPROVED OR CANONICAL OUTPUTS
PROJECT STATE
OPEN DECISIONS
OPEN DEPENDENCIES
NEXT PERMITTED ACTION
RE-ENTRY LINE

Do not manufacture future work.
Closing this conversation does not automatically close the underlying project.

Classify the project separately as:
ACTIVE
SLEEPING
CLOSED
ARCHIVED
STATUS UNCONFIRMED

End with a concise re-entry instruction that can be pasted into a future conversation.
```

## 25. `/clear`

```text
/clear

Reset the working frame for this conversation from this point forward.
Do not continue the previous conversational task unless I explicitly reactivate it.

Preserve platform-level instructions, safety requirements, and any established memory that legitimately applies, but do not automatically carry forward the previous task's assumptions, plan, or unfinished branches.

Treat my next instruction as a fresh working objective.
```

## 26. `/handoff`

```text
/handoff

Create a concise but sufficient handoff for the current work.

Include:
OBJECTIVE
CURRENT STATE
AUTHORITATIVE ARTEFACTS
APPROVED DECISIONS
HARD BOUNDARIES
IMPLEMENTED WORK
TEST / EVIDENCE STATE
OPEN ISSUES
BLOCKERS
NEXT PERMITTED ACTION
DO NOT DO
RE-ENTRY INSTRUCTION

The receiver should be able to continue without reconstructing the entire conversation.
```

## 27. `/repo-map`

```text
/repo-map

Map the repository relevant to the current task.

Identify:
repository purpose;
major directories;
entry points;
important modules;
configuration;
tests;
CI/CD;
data flow;
external dependencies;
state/storage;
security-sensitive components;
documentation;
active branches or PR context where available.

Then identify:
FILES MOST RELEVANT TO THE CURRENT TASK
LIKELY CHANGE SURFACE
FILES THAT SHOULD NOT NEED MODIFICATION
UNKNOWN AREAS REQUIRING INSPECTION

Do not modify code.

End with:
IMPLEMENTATION SURFACE: <concise file/component map>
```

## 28. `/trace <target>`

```text
/trace <target>

Trace the named target through the available repository, issues, pull requests, documentation, tests, runtime behaviour, or project records.

Show the path from:
SOURCE
through
DEPENDENCIES / CALLERS / IMPLEMENTATION
to
OBSERVED OR EXPECTED OUTCOME

Identify:
where the behaviour originates;
where it changes;
where it is validated;
where it is tested;
where it may fail;
related issues or PRs;
the smallest legitimate change surface.

Do not patch anything unless separately instructed.

End with:
ROOT / SOURCE: <location>
CHANGE SURFACE: <location>
NEXT: <single action>
```

## 29. `/regression`

**Purpose:** Apply the approved Prompt Reliability doctrine.

```text
/regression

Evaluate the current prompt, agent, model-assisted workflow, or behavioural component for regression risk.

Treat prompts as probabilistic behavioural components rather than deterministic programs.

Identify:
VERSION UNDER TEST
INCUMBENT VERSION
MODEL / RUNTIME
TOOL SCHEMAS
POLICY VERSION
RETRIEVAL CONFIGURATION
DEPENDENCY MANIFEST

Build or inspect a regression corpus containing where relevant:
normal cases;
boundary cases;
ambiguous cases;
instruction-conflict cases;
adversarial cases;
historical failures;
tool-selection cases;
tool-argument cases;
abstention cases;
missing-evidence cases;
duplicate/retry cases;
injection cases;
state-change cases;
metamorphic variants.

Separate:
STRUCTURAL RELIABILITY
SEMANTIC RELIABILITY
POLICY RELIABILITY
EXECUTION RELIABILITY
BEHAVIOURAL RELIABILITY

Evaluate candidate versus incumbent.
Report:
NEW PASSES
NEW FAILURES
UNCHANGED PASSES
UNCHANGED FAILURES
CRITICAL REGRESSIONS
INVARIANT VIOLATIONS

Do not allow average performance to override a zero-tolerance control failure.

End with:
PROMOTION RESULT: PROMOTE / HOLD / REJECT / INSUFFICIENT EVIDENCE
```

## 30. `/redteam`

```text
/redteam

Attempt to break the current system, prompt, workflow, or control model while remaining within the authorised test scope.

Target:
instruction conflicts;
ambiguous authority;
prompt injection;
tool misuse;
unsafe arguments;
missing evidence;
unexpected file types;
duplicate execution;
race conditions;
state changes;
malformed input;
overlong input;
partial failure;
retry behaviour;
human approval bypass;
retrieval poisoning;
incorrect assumptions;
silent fallback behaviour.

For each attack provide:
ATTACK
EXPECTED CONTROL
OBSERVED RESULT
FAILURE MODE
SEVERITY
REPRODUCTION
RECOMMENDED FIX
REGRESSION FIXTURE TO ADD

Do not expand testing into systems or assets outside the authorised scope.

End with:
RED TEAM RESULT: PASS / WEAKNESSES FOUND / CRITICAL FAILURE
```

## 31. `/ship`

```text
/ship

Assess the current candidate for release.
Do not interpret "works on my machine" as release readiness.

Check:
approved scope;
required functionality;
tests;
regression status;
security;
privacy;
configuration;
secrets;
dependency state;
documentation;
installation/deployment;
rollback;
monitoring;
failure recovery;
known limitations;
release artefact identity;
versioning;
evidence completeness.

Separate:
BLOCKERS
NON-BLOCKING ISSUES
KNOWN ACCEPTED LIMITATIONS
RELEASE EVIDENCE

End with exactly one:
RELEASE
RELEASE WITH DECLARED CONDITIONS
DO NOT RELEASE
INSUFFICIENT EVIDENCE
```

## 32. `/write <purpose>`

```text
/write <purpose>

Turn the available material into finished writing suitable for the intended audience and medium.

Preserve my actual argument and meaning.
Prioritise:
clarity;
specificity;
natural cadence;
evidence;
appropriate confidence;
strong structure;
minimal filler.

Avoid generic AI phrasing, inflated claims, unnecessary headings, repetitive conclusions, and fake certainty.
Do not make the narrator sound more knowledgeable than the evidence permits.
Return publication-ready copy unless I explicitly request an outline or analysis.
```

## 33. `/edit`

```text
/edit

Edit the supplied writing while preserving the author's voice, argument, intent, and level of certainty.

Improve:
clarity;
flow;
sentence rhythm;
structure;
redundancy;
precision;
grammar;
readability.

Remove:
generic AI phrasing;
unnecessary throat-clearing;
repetition;
corporate filler;
false certainty;
over-explanation.

Do not rewrite distinctive language merely to make it more conventional.
Return the complete edited version.
```

## 34. `/publish-check`

```text
/publish-check

Perform a final publication review of the current piece.

Check:
factual claims;
source support;
dates;
names;
links;
quotes;
tone;
defamation risk;
privacy;
confidential information;
unsupported claims;
accidental AI artefacts;
formatting;
title;
opening;
ending;
call to action where appropriate.

Separate:
MUST FIX BEFORE PUBLICATION
OPTIONAL POLISH
READY AS IS

End with:
PUBLICATION STATE: READY / READY AFTER FIXES / NOT READY
```

# App Commands

## 35. `@GitHub /repo-review <repository>`

```text
@GitHub /repo-review <repository>

Inspect the repository using the connected GitHub source.

Review:
current repository state;
README and documentation;
open issues;
open pull requests;
recent commits;
CI status;
tests;
branch state;
known blockers;
architecture relevant to active work.

Separate:
ACTIVE WORK
STALE WORK
BLOCKERS
PRs REQUIRING ACTION
ISSUES REQUIRING ACTION
DOCUMENTATION DRIFT

Do not modify the repository unless I explicitly instruct you to do so.

End with:
NEXT REPOSITORY ACTION: <single action>
```

## 36. `@GitHub /pr-review <PR>`

```text
@GitHub /pr-review <PR>

Review the specified pull request in context.

Inspect:
PR objective;
changed files;
linked issue;
implementation;
tests;
CI;
security implications;
backwards compatibility;
unrelated changes;
missing tests;
review comments;
merge blockers.

Determine:
WHAT THE PR CHANGES
WHAT IT DOES NOT CHANGE
RISKS
REQUIRED REPAIRS
OPTIONAL IMPROVEMENTS
MERGE READINESS

Do not merge unless explicitly instructed.

End with:
PR STATE: READY / READY WITH MINOR FIXES / CHANGES REQUIRED / BLOCKED
```

## 37. `@Gmail /catchup <scope>`

```text
@Gmail /catchup <scope>

Review relevant Gmail messages within the specified scope.

Group information into:
NEEDS REPLY
NEEDS ACTION
AWAITING SOMEONE ELSE
INFORMATION ONLY
RESOLVED

Identify:
decisions;
deadlines;
requests;
commitments;
attachments;
dependencies;
unanswered questions.

Do not send messages.

End with:
TOP EMAIL ACTION: <single highest-priority action>
```

## 38. `@Gmail /find-decision <topic>`

```text
@Gmail /find-decision <topic>

Search Gmail for messages relevant to the specified topic and reconstruct the decision trail.

Identify:
original request;
material replies;
decisions;
changes;
latest confirmed position;
unresolved items.

Distinguish explicit decisions from assumptions and proposals.

End with:
LATEST CONFIRMED STATE: <state>
```

## 39. `@Google Drive /project-state <project>`

```text
@Google Drive /project-state <project>

Inspect relevant Google Drive files for the specified project.

Identify:
authoritative documents;
candidate drafts;
superseded files;
technical specifications;
governance records;
client communications;
deliverables;
test evidence;
unfiled or duplicate material.

Reconstruct:
CURRENT PROJECT STATE
LATEST AUTHORITATIVE ARTEFACTS
MISSING DEPENDENCIES
CONFLICTING VERSIONS
NEXT PERMITTED ACTION

Do not edit files unless explicitly instructed.
```

## 40. `@Google Drive /find-authoritative <topic>`

```text
@Google Drive /find-authoritative <topic>

Find the documents most likely to govern the specified topic.

Prioritise:
approved versions;
latest controlled versions;
explicit decision records;
signed or issued material;
canonical specifications;
files referenced by later authoritative documents.

Identify duplicates, superseded material, and conflicting candidates.
Do not assume the newest timestamp automatically means authoritative.

End with:
AUTHORITATIVE SOURCE: <file>
CONFIDENCE: HIGH / MEDIUM / LOW
```

## 41. `@Google Calendar /today`

```text
@Google Calendar /today

Review today's calendar.

Summarise:
fixed commitments;
preparation required;
travel or transition time where known;
open blocks;
deadlines represented by calendar events.

Identify scheduling conflicts or unrealistic transitions.
Do not create or modify events.

End with:
NEXT CALENDAR COMMITMENT: <event and time>
BEST AVAILABLE WORK BLOCK: <time range, if identifiable>
```

## 42. `@Google Calendar /plan-week`

```text
@Google Calendar /plan-week

Review the upcoming seven days.

Identify:
fixed commitments;
important deadlines;
high-focus work windows;
fragmented days;
potential conflicts;
days with excessive load.

Do not rearrange events automatically.
Suggest a practical work allocation based on the actual calendar.
Prioritise already-active work over creating new projects.
```

## 43. `@Outlook /catchup <scope>`

```text
@Outlook /catchup <scope>

Review relevant Outlook email within the specified scope.

Classify messages into:
REPLY REQUIRED
ACTION REQUIRED
WAITING
REFERENCE
RESOLVED

Extract:
decisions;
deadlines;
requested deliverables;
commitments;
attachments;
important context.

Do not send anything.

End with:
NEXT EMAIL ACTION: <single action>
```

## 44. `@Slack /catchup <channel or project>`

```text
@Slack /catchup <channel or project>

Review the relevant Slack activity.

Identify:
decisions;
requests;
assigned actions;
unanswered questions;
blockers;
links or artefacts;
changes since the last known project state.

Separate casual discussion from decisions that materially affect the work.

End with:
ACTION REQUIRED FROM ME: <action or NONE>
```

# Reusable Skill Commands

## 45. `/skill-create <workflow>`

```text
/skill-create <workflow>

Determine whether the current workflow is sufficiently repeatable and bounded to justify turning it into a reusable skill.

Define:
SKILL NAME
TRIGGER
PURPOSE
INPUTS
OUTPUTS
WORKFLOW
DECISION RULES
TOOLS REQUIRED
BOUNDARIES
FAILURE BEHAVIOUR
EVIDENCE REQUIREMENTS
STOP CONDITIONS
TEST CASES
NEGATIVE ACTIVATION TESTS

Do not create a skill for a one-off task merely because it could be automated.

End with:
SKILL CANDIDATE: YES / NO
NEXT: <single action>
```

## 46. `/skill-test`

```text
/skill-test

Test the current reusable skill.

Include:
positive activation cases;
negative activation cases;
ambiguous activation cases;
normal execution cases;
edge cases;
tool failure;
missing inputs;
conflicting instructions;
unsafe or out-of-scope requests.

Assess:
correct activation;
correct non-activation;
output quality;
boundary compliance;
failure behaviour;
repeatability.

End with:
SKILL STATE: PASS / REVISE / FAIL
```

## 47. `/automation-candidate`

```text
/automation-candidate

Assess whether the current task should be automated.

Consider automation only if there is a genuine:
recurrence;
future condition;
deadline;
monitoring need;
repeated manual check;
external dependency;
regular reporting requirement.

Identify:
TRIGGER
CADENCE OR CONDITION
INPUTS
ACTION
OUTPUT
NOTIFICATION CONDITION
FAILURE BEHAVIOUR
STOP CONDITION

Do not automate something merely because it can be automated.

End with:
AUTOMATION: YES / NO
IF YES: <single proposed automation>
```

## 48. `/workflow`

```text
/workflow

Convert the current process into a defined workflow.

Identify:
TRIGGER
INPUTS
PRECONDITIONS
STEPS
DECISION POINTS
HUMAN DECISIONS
AI RESPONSIBILITIES
DETERMINISTIC RESPONSIBILITIES
TOOLS
STATE CHANGES
EVIDENCE CREATED
FAILURE PATHS
RECOVERY
STOP CONDITIONS
OUTPUT

Do not assign authority to AI merely because AI can technically perform an action.

End with:
WORKFLOW READY FOR: REVIEW / IMPLEMENTATION / TESTING / NOT READY
```

## 49. `/simplify`

```text
/simplify

Find the smallest version of the current system, plan, workflow, interface, or architecture that still satisfies the approved requirements.

Identify:
ESSENTIAL
USEFUL BUT OPTIONAL
REDUNDANT
PREMATURE
DUPLICATED
OVER-ENGINEERED

Do not remove safety, evidence, authority, testing, or recovery controls merely to make the system look simpler.

Propose the minimum viable structure.

End with:
REMOVE
KEEP
DEFER
SIMPLIFIED NEXT ACTION
```

## 50. `/surprise`

```text
/surprise

Give me one unexpected but credible idea that could materially improve the current product, project, experience, workflow, or creative direction.

The idea must:
fit the existing objective;
respect approved scope;
not require rebuilding everything;
be technically or creatively plausible;
create a noticeable improvement;
not merely be a generic feature suggestion.

Explain briefly:
THE IDEA
WHY IT FITS
WHY IT IS SURPRISING
COST / COMPLEXITY
WHAT WOULD HAVE TO CHANGE

Do not automatically add it to scope.

End with:
STATUS: OPTIONAL IDEA — NOT APPROVED
```

# Universal End-of-Work Command

## `/state`

```text
/state

Tell me:
Where are we?
What is established?
What remains open?
Are we blocked?
Do you need anything from me?
Is there useful work you can continue yourself?
What is the single best next action?
Or are we actually done?

Do not manufacture additional work.

End with exactly one:
NEXT: <action>
NEEDS ME: <input>
PARK: <condition>
DONE
CLOSE
```

This is the general-purpose “what the fuck happens now?” command.

---

## Muscle-memory set

If only five commands become habitual, use:

1. `/next`
2. `/status`
3. `/ultrareview`
4. `/approve`
5. `/close`

Use `/state` when you do not even know which of those you need.
