# Ending Vibe-Based AI: Building Deterministic Evaluation Gates for Production LLMs

**Steven Lees**  
**Published:** 10 September 2026

A developer changes a system prompt to make an LLM less verbose. The outputs look better. Five manual tests pass. The pull request is merged.

Three weeks later, someone discovers the change increased malformed JSON responses in a production workflow.

Nothing crashed. The model still sounded competent. The regression was sitting inside behaviour nobody had bothered to turn into a test.

This is where a lot of LLM prototypes stop behaving like production software.

Production AI needs a release contract: measurable conditions that every candidate version has to satisfy before it is allowed to ship.

The model itself does not need to become deterministic.

The deployment decision does.

## Turn behavioural failures into testable properties

LLM regressions tend to look a little different from conventional software failures.

Schema degradation might mean machine-readable JSON suddenly arrives inside Markdown fences. Required fields disappear. Enum values drift. A numeric value wanders outside its allowed range.

Fact-to-inference drift happens when a retrieval workflow starts supplementing supplied evidence with plausible model knowledge, or an inference that sounds perfectly reasonable but isn't actually supported by the source.

Instruction dropping is exactly what it sounds like. Longer or conflicting inputs cause secondary requirements, citation rules, escalation conditions or output constraints to quietly disappear.

Manual prompt testing can find examples of all of these.

What it cannot reliably establish is whether the changed workflow still sits inside its production contract.

The engineering response is fairly straightforward: turn the behaviour you require into properties you can actually test.

## Build the cheapest reliable gate first

A practical evaluation architecture should use the least expensive, least uncertain method capable of establishing the property being tested.

These are method classes, not mandatory sequential stages for every property. Assign each declared property the least expensive, least uncertain valid method capable of establishing it. Escalate only when the result remains unresolved, and only to another valid method for that same property.

Conceptually, the available methods might look like this:

```text
Candidate workflow
Tier 1: Contract validation
JSON Schema / Pydantic
Tier 2: Deterministic bounds
Regex / ranges / arithmetic
Tier 3: Semantic comparison
Pinned embeddings / metrics
Tier 4: Probabilistic judge
Versioned bounded rubric
 |
DETERMINISTIC RELEASE POLICY
PASS
FAIL
INDETERMINATE
```

The distinction here matters.

Tiers 1 and 2 can evaluate suitable properties deterministically. Tiers 3 and 4 may introduce model-dependent or probabilistic behaviour.

The release policy can still be deterministic because the disposition of those results is defined in advance.

A probabilistic evaluator returning 1 does not magically become deterministic because we've wrapped it in a pipeline. But a release policy that says exactly what happens when that evaluator returns 1, 0 or an unstable result can be deterministic.

That is the boundary worth controlling.

## Build a regression fixture from real failures

Start with a version-controlled fixture representing the behaviour that actually matters.

Each case should identify:

```text
fixture_id
input
source_context
required_properties
prohibited_properties
expected_schema
evaluation_method
failure_consequence
```

Populate it from three places:

- normal production behaviour;
- adversarial and boundary conditions;
- exact replays of production failures that escaped.

The number of fixtures isn't the important bit. Picking 50 or 500 cases because it feels benchmark-shaped doesn't make the suite representative.

Coverage should follow known risks.

And when a new production regression escapes the gate, keep it. Turn it into a fixture and leave it there.

Over time, the suite becomes a cumulative record of behaviour the system is no longer permitted to forget.

## Enforce machine contracts without repairing failures

Suppose the workflow promises raw JSON:

```json
{
  "decision": "APPROVED",
  "confidence": 0.82,
  "risk_factors": []
}
```

Test that contract directly:

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ProductionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal[
        "APPROVED",
        "REJECTED",
        "REQUIRES_REVIEW",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str]

def validate_raw_output(raw_output: str) -> ProductionPayload:
    return ProductionPayload.model_validate_json(raw_output)
```

Don't strip Markdown fences first.

Don't insert missing fields.

Don't quietly transform almost-valid output into valid output and then congratulate the model for passing.

If raw JSON is the contract, fenced JSON is a regression.

The evaluator's job is to detect the contract violation. Repairing it inside the evaluator destroys the evidence that the violation happened in the first place.

Preserve the raw failure and stop evaluation where the contract requires you to stop.

## Prefer properties over prose matching

Generative systems rarely need to produce one exact sequence of words.

That doesn't make their outputs untestable.

If the output contains financial calculations, independently calculate the totals. If it's a retrieval workflow, verify that the citation identifiers actually exist in the supplied evidence set. If it's a classification task, enforce the permitted enum. If it's structured extraction, compare the required fields.

If the workflow requires escalation under defined uncertainty conditions, test that those conditions actually produce the escalation state.

Every property you can establish in ordinary executable code is one less property that requires semantic judgement.

That helps with cost and speed, but there is a more important reason to do it: semantic judgement introduces additional uncertainty. Avoid introducing that uncertainty where a simpler valid method can establish the property directly.

## Calibrate semantic evaluation instead of inventing thresholds

Some requirements are genuinely semantic. You don't get to regex your way out of all of this.

Embedding similarity can be useful for detecting substantial movement away from accepted examples, for instance, but a threshold such as 0.88 has no universal relationship with correctness.

It is just a number until you establish what it means for your workload.

Treat thresholds as parameters to be calibrated against the system you're actually running.

Separate the evidence into three populations.

Development fixtures are available while prompts, models and orchestration are being changed.

Held-out release fixtures are reserved for evaluating the resulting candidate. Production observations tell you whether benchmark performance actually generalises once the thing leaves the test environment.

Pin embedding models and versions where possible. Record thresholds alongside the benchmark version. Measure false passes and false failures before turning a semantic threshold into a deployment blocker.

Model judges need the same treatment.

Constrain the output. Version the rubric. Pin the model where the platform permits it. Measure repeated-run disagreement.

And if repeated evaluations materially disagree, don't pick whichever answer makes the deployment easier.

The property remains unresolved.

At the release boundary, that means INDETERMINATE.

## Define the success metric before claiming success

Suppose the target is fewer than 1% semantic regressions.

Fine.

One fairly important question comes first: 1% of what?

You need a stable denominator.

Define an evaluation unit as one eligible workflow execution whose required semantic properties can be independently established.

Then measure:

```text
Semantic regression rate
confirmed semantic regressions
------------------------------
eligible evaluated executions
```

Define semantic regression and eligible before you run the benchmark, not after you've seen the numbers.

And don't pool a mountain of unrelated low-risk executions into the denominator because one consequential workflow class is performing badly. You can make a lot of ugly numbers look healthy with a sufficiently convenient denominator.

The <1% requirement remains an acceptance target until measured evidence establishes that you've actually achieved it.

Cost needs the same discipline.

```text
Evaluation token overhead
evaluation-related token consumption
------------------------------------
baseline operational token consumption
```

So the operational requirement might be:

```text
semantic regression rate < 1.0%
AND
evaluation token overhead <= 15%
AND
CI evaluation runtime < 90 seconds
```

Those are acceptance boundaries.

Writing them down doesn't make them properties of the architecture. The system still has to demonstrate that it can meet them.

## Keep expensive evaluation out of the common path

A 90-second CI budget turns evaluation architecture into an optimisation problem fairly quickly.

Run applicable deterministic tests across the fixture first. Fail immediately where the release contract requires it.

Cache invariant artefacts such as reference embeddings. Parallelise independent cases. Invoke probabilistic evaluation only for properties that cannot be established by a less uncertain valid method.

The evaluation workload should narrow as the methods become more expensive and uncertain:

```text
many fixtures
 |
deterministically testable properties
 |
smaller semantic set
 |
probabilistic evaluation where required
 |
unresolved remainder
 |
INDETERMINATE
```

This helps control latency and evaluation token consumption.

More importantly, it stops an expensive model judge from becoming the answer to every testing problem just because you happen to have one.

## Make the release contract explicit

The final CI decision should be boring.

That's a feature.

```text
mandatory deterministic failure
-> FAIL

mandatory semantic failure
-> FAIL

material evaluator disagreement
-> INDETERMINATE

required evidence unavailable
-> INDETERMINATE

all required properties established
-> PASS
```

No evaluator gets to quietly reinterpret that policy.

Missing evidence doesn't become a pass. An ambiguous result doesn't become a pass because somebody wants to deploy before lunch.

A property that cannot be established or violated with sufficient, consistent evidence remains UNRESOLVED.

And unresolved evidence has a defined consequence:

INDETERMINATE. Release not allowed. Additional evidence or human review is required.

A model sounding confident has absolutely nothing to do with whether the release contract has been satisfied.

## Start with one workflow

Take one production workflow and identify its most consequential known failure modes.

Turn everything objectively testable into code. Put those tests in CI. Use semantic evaluation for the properties that genuinely require it rather than reaching for it first.

Then, every time a production regression escapes, capture the failure and make it another permanent test.

The goal isn't to build the perfect evaluation platform.

It's to establish a controlled, reproducible boundary between:

> the model produced an answer

and

> we have sufficient evidence to release this version.

That boundary is where prompt experimentation starts becoming production engineering.
