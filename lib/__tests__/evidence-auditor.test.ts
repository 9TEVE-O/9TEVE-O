import { beforeEach, describe, expect, it, vi } from "vitest";
import fixture from "../../fixtures/evidence-auditor/eval-001.input.json";
import { getAuditorEnvironment } from "../evidence-auditor/env";
import {
  auditOutputJsonSchema,
  parseAuditInput,
  type AuditInput,
} from "../evidence-auditor/schemas";

const create = vi.fn();

vi.mock("openai", () => ({
  default: vi.fn(function () {
    return { responses: { create } };
  }),
}));

import { auditWorkflowEvidence } from "../evidence-auditor/audit";

describe("AI Workflow Evidence Auditor", () => {
  beforeEach(() => create.mockReset());

  it("accepts the representative bounded evidence fixture", () => {
    const parsed = parseAuditInput(fixture);
    expect(parsed.workflow_id).toBe("wf-vendor-risk-001");
    expect(parsed.controlled_evidence_set).toHaveLength(3);
  });

  it("rejects an empty controlled evidence set", () => {
    expect(() => parseAuditInput({ ...fixture, controlled_evidence_set: [] })).toThrow(
      "controlled_evidence_set must contain at least one item",
    );
  });

  it("requires all private auditor configuration", () => {
    expect(() => getAuditorEnvironment({})).toThrow("OPENAI_API_KEY is required");
    expect(() => getAuditorEnvironment({ OPENAI_API_KEY: "test" })).toThrow(
      "OPENAI_AUDITOR_PROMPT_ID is required",
    );
  });

  it("sends the saved prompt reference, strict schema, and disables storage", async () => {
    const output = {
      workflow_reconstruction: { objective: "Review renewal", scope_boundary: "Provided evidence", steps: [] },
      evidence_and_authority_map: [], unsupported_claim_register: [],
      reliability_and_governance_risk_register: [], unresolved_question_register: [],
      prioritised_corrective_actions: [],
      decision_ready_review_report: {
        overall_rating: "needs_revision", overall_risk: "high",
        approval_recommendation: "do_not_approve", executive_summary: "Evidence is incomplete.", key_findings: [],
      },
    };
    create.mockResolvedValue({ output_text: JSON.stringify(output) });

    await expect(auditWorkflowEvidence(fixture as AuditInput, {
      apiKey: "test-key", promptId: "pmpt_auditor", promptVersion: "3", model: "gpt-5.5",
    })).resolves.toEqual(output);

    expect(create).toHaveBeenCalledWith(expect.objectContaining({
      model: "gpt-5.5", store: false,
      prompt: expect.objectContaining({ id: "pmpt_auditor", version: "3" }),
      text: { format: expect.objectContaining({ type: "json_schema", strict: true, schema: auditOutputJsonSchema }) },
    }));
  });

  it("fails clearly when the API omits structured output", async () => {
    create.mockResolvedValue({});
    await expect(auditWorkflowEvidence(fixture as AuditInput, {
      apiKey: "test-key", promptId: "pmpt_auditor", promptVersion: "1", model: "gpt-5.5",
    })).rejects.toThrow("returned no output_text");
  });
});
