import { describe, expect, it } from "vitest";
import fixture from "../fixtures/eval-001.input.json";
import { getEnvironment } from "../src/env.js";
import { AuditInputSchema, AuditOutputSchema } from "../src/schemas.js";

describe("auditor contracts", () => {
  it("accepts the representative bounded evidence fixture", () => {
    expect(AuditInputSchema.parse(fixture).controlled_evidence_set).toHaveLength(4);
  });

  it("rejects unknown input fields and empty evidence sets", () => {
    expect(() => AuditInputSchema.parse({ ...fixture, unexpected: true })).toThrow();
    expect(() => AuditInputSchema.parse({ ...fixture, controlled_evidence_set: [] })).toThrow();
  });

  it("rejects duplicate evidence identifiers", () => {
    const duplicate = {
      ...fixture,
      controlled_evidence_set: [fixture.controlled_evidence_set[0], fixture.controlled_evidence_set[0]],
    };
    expect(() => AuditInputSchema.parse(duplicate)).toThrow("duplicate evidence_id: E-001");
  });

  it("requires the API key and saved prompt reference", () => {
    expect(() => getEnvironment({})).toThrow("OPENAI_API_KEY is required");
    expect(() => getEnvironment({ OPENAI_API_KEY: "test" })).toThrow("OPENAI_AUDITOR_PROMPT_ID is required");
    expect(() => getEnvironment({
      OPENAI_API_KEY: "test",
      OPENAI_AUDITOR_PROMPT_ID: "pmpt_test",
      OPENAI_AUDITOR_PROMPT_VERSION: "latest",
    })).toThrow("must be a numeric version");
  });

  it("defines all seven outputs", () => {
    expect(Object.keys(AuditOutputSchema.shape)).toEqual([
      "workflow_reconstruction", "evidence_and_authority_map", "unsupported_claim_register",
      "reliability_and_governance_risk_register", "unresolved_question_register",
      "prioritised_corrective_actions", "decision_ready_review_report",
    ]);
  });
});
