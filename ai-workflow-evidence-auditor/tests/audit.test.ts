import { describe, expect, it, vi } from "vitest";
import fixture from "../fixtures/eval-001.input.json";
import { auditWorkflowEvidence } from "../src/audit.js";
import { AuditInputSchema, AuditOutputSchema } from "../src/schemas.js";

const report = AuditOutputSchema.parse({
  workflow_reconstruction: { workflow_id: fixture.workflow_id, workflow_name: fixture.workflow_name, objective: "Review renewal", scope_boundary: "Controlled evidence only", reconstructed_steps: [], decision_points: [], material_claims: [] },
  evidence_and_authority_map: [], unsupported_claim_register: [], reliability_and_governance_risk_register: [],
  unresolved_question_register: [], prioritised_corrective_actions: [],
  decision_ready_review_report: { overall_rating: "needs_revision", evidence_strength: "weak", overall_risk: "high", approval_recommendation: "do_not_approve", executive_summary: "Evidence is incomplete.", key_findings: [], required_conditions: [], auditor_notes: "Bounded review." },
});

describe("auditWorkflowEvidence", () => {
  it("uses the versioned prompt, structured output, and disabled storage", async () => {
    const parse = vi.fn().mockResolvedValue({ output_parsed: report });
    const client = { responses: { parse } } as never;
    await expect(auditWorkflowEvidence(AuditInputSchema.parse(fixture), {
      OPENAI_API_KEY: "test", OPENAI_AUDITOR_PROMPT_ID: "pmpt_test", OPENAI_AUDITOR_PROMPT_VERSION: "3", OPENAI_AUDITOR_MODEL: "gpt-5.5",
    }, client)).resolves.toEqual(report);
    expect(parse).toHaveBeenCalledWith(expect.objectContaining({
      model: "gpt-5.5", store: false,
      prompt: expect.objectContaining({ id: "pmpt_test", version: "3" }),
      text: { format: expect.objectContaining({ type: "json_schema", strict: true }) },
    }));
    const request = parse.mock.calls[0][0];
    expect(JSON.parse(request.prompt.variables.audit_input_json)).toEqual(fixture);
  });

  it("fails when no parsed output is returned", async () => {
    const client = { responses: { parse: vi.fn().mockResolvedValue({ output_parsed: null }) } } as never;
    await expect(auditWorkflowEvidence(AuditInputSchema.parse(fixture), {
      OPENAI_API_KEY: "test", OPENAI_AUDITOR_PROMPT_ID: "pmpt_test", OPENAI_AUDITOR_PROMPT_VERSION: "1", OPENAI_AUDITOR_MODEL: "gpt-5.5",
    }, client)).rejects.toThrow("no parsed audit output");
  });

  it("rejects invalid input before making an API request", async () => {
    const parse = vi.fn();
    const client = { responses: { parse } } as never;
    const invalidInput = { ...fixture, controlled_evidence_set: [] };

    await expect(auditWorkflowEvidence(invalidInput as never, {
      OPENAI_API_KEY: "test",
      OPENAI_AUDITOR_PROMPT_ID: "pmpt_test",
      OPENAI_AUDITOR_PROMPT_VERSION: "1",
      OPENAI_AUDITOR_MODEL: "gpt-5.5",
    }, client)).rejects.toThrow();
    expect(parse).not.toHaveBeenCalled();
  });
});
