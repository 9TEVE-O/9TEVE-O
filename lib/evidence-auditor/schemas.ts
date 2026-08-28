export const evidenceTypes = [
  "policy",
  "procedure",
  "ticket",
  "log",
  "dataset",
  "email",
  "approval",
  "contract",
  "regulation",
  "source_document",
  "other",
] as const;

export const authorityLevels = ["primary", "secondary", "informal", "unknown"] as const;

export interface EvidenceItem {
  evidence_id: string;
  title: string;
  evidence_type: (typeof evidenceTypes)[number];
  authority_level: (typeof authorityLevels)[number];
  source_reference: string;
  date: string | null;
  excerpt_or_summary: string;
  known_limitations: string | null;
}

export interface AuditInput {
  workflow_id: string;
  workflow_name: string;
  workflow_text: string;
  controlled_evidence_set: EvidenceItem[];
  review_context: {
    requester: string | null;
    domain: string | null;
    decision_to_support: string | null;
    applicable_policies: string[];
    known_constraints: string[];
  };
}

export interface AuditOutput {
  workflow_reconstruction: { objective: string; scope_boundary: string; steps: string[] };
  evidence_and_authority_map: Array<{
    claim_or_step: string;
    evidence_ids: string[];
    evidence_quality: "strong" | "moderate" | "weak" | "none";
    traceability: "clear" | "partial" | "unclear" | "absent";
    authority_assessment: string;
  }>;
  unsupported_claim_register: Array<{
    claim: string;
    status: "partially_supported" | "unsupported" | "contradicted" | "unverifiable" | "overstated";
    required_evidence: string;
    risk_if_wrong: string;
  }>;
  reliability_and_governance_risk_register: Array<{
    risk: string;
    severity: "low" | "medium" | "high" | "critical";
    mitigation: string;
  }>;
  unresolved_question_register: Array<{
    question: string;
    blocking: boolean;
    evidence_needed: string;
  }>;
  prioritised_corrective_actions: Array<{
    priority: "p0" | "p1" | "p2" | "p3";
    action: string;
    acceptance_criteria: string;
  }>;
  decision_ready_review_report: {
    overall_rating: "pass" | "pass_with_conditions" | "needs_revision" | "fail";
    overall_risk: "low" | "medium" | "high" | "critical";
    approval_recommendation:
      | "approve"
      | "approve_with_conditions"
      | "do_not_approve"
      | "escalate_for_human_review";
    executive_summary: string;
    key_findings: string[];
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireString(value: unknown, path: string): asserts value is string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${path} must be a non-empty string`);
  }
}

function requireStringArray(value: unknown, path: string): asserts value is string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new Error(`${path} must be an array of strings`);
  }
}

export function parseAuditInput(value: unknown): AuditInput {
  if (!isRecord(value)) throw new Error("audit input must be an object");
  requireString(value.workflow_id, "workflow_id");
  requireString(value.workflow_name, "workflow_name");
  requireString(value.workflow_text, "workflow_text");

  if (!Array.isArray(value.controlled_evidence_set) || value.controlled_evidence_set.length === 0) {
    throw new Error("controlled_evidence_set must contain at least one item");
  }
  for (const [index, item] of value.controlled_evidence_set.entries()) {
    if (!isRecord(item)) throw new Error(`controlled_evidence_set[${index}] must be an object`);
    for (const field of ["evidence_id", "title", "source_reference", "excerpt_or_summary"] as const) {
      requireString(item[field], `controlled_evidence_set[${index}].${field}`);
    }
    if (!evidenceTypes.includes(item.evidence_type as (typeof evidenceTypes)[number])) {
      throw new Error(`controlled_evidence_set[${index}].evidence_type is invalid`);
    }
    if (!authorityLevels.includes(item.authority_level as (typeof authorityLevels)[number])) {
      throw new Error(`controlled_evidence_set[${index}].authority_level is invalid`);
    }
    if (item.date !== null && typeof item.date !== "string") {
      throw new Error(`controlled_evidence_set[${index}].date must be a string or null`);
    }
    if (item.known_limitations !== null && typeof item.known_limitations !== "string") {
      throw new Error(`controlled_evidence_set[${index}].known_limitations must be a string or null`);
    }
  }

  if (!isRecord(value.review_context)) throw new Error("review_context must be an object");
  for (const field of ["requester", "domain", "decision_to_support"] as const) {
    const fieldValue = value.review_context[field];
    if (fieldValue !== null && typeof fieldValue !== "string") {
      throw new Error(`review_context.${field} must be a string or null`);
    }
  }
  requireStringArray(value.review_context.applicable_policies, "review_context.applicable_policies");
  requireStringArray(value.review_context.known_constraints, "review_context.known_constraints");

  return value as unknown as AuditInput;
}

const stringArray = { type: "array", items: { type: "string" } } as const;

export const auditOutputJsonSchema = {
  type: "object",
  additionalProperties: false,
  required: [
    "workflow_reconstruction",
    "evidence_and_authority_map",
    "unsupported_claim_register",
    "reliability_and_governance_risk_register",
    "unresolved_question_register",
    "prioritised_corrective_actions",
    "decision_ready_review_report",
  ],
  properties: {
    workflow_reconstruction: objectSchema(["objective", "scope_boundary", "steps"], {
      objective: { type: "string" }, scope_boundary: { type: "string" }, steps: stringArray,
    }),
    evidence_and_authority_map: arraySchema(objectSchema(
      ["claim_or_step", "evidence_ids", "evidence_quality", "traceability", "authority_assessment"],
      {
        claim_or_step: { type: "string" }, evidence_ids: stringArray,
        evidence_quality: enumSchema(["strong", "moderate", "weak", "none"]),
        traceability: enumSchema(["clear", "partial", "unclear", "absent"]),
        authority_assessment: { type: "string" },
      },
    )),
    unsupported_claim_register: arraySchema(objectSchema(
      ["claim", "status", "required_evidence", "risk_if_wrong"],
      {
        claim: { type: "string" },
        status: enumSchema(["partially_supported", "unsupported", "contradicted", "unverifiable", "overstated"]),
        required_evidence: { type: "string" }, risk_if_wrong: { type: "string" },
      },
    )),
    reliability_and_governance_risk_register: arraySchema(objectSchema(
      ["risk", "severity", "mitigation"],
      { risk: { type: "string" }, severity: enumSchema(["low", "medium", "high", "critical"]), mitigation: { type: "string" } },
    )),
    unresolved_question_register: arraySchema(objectSchema(
      ["question", "blocking", "evidence_needed"],
      { question: { type: "string" }, blocking: { type: "boolean" }, evidence_needed: { type: "string" } },
    )),
    prioritised_corrective_actions: arraySchema(objectSchema(
      ["priority", "action", "acceptance_criteria"],
      { priority: enumSchema(["p0", "p1", "p2", "p3"]), action: { type: "string" }, acceptance_criteria: { type: "string" } },
    )),
    decision_ready_review_report: objectSchema(
      ["overall_rating", "overall_risk", "approval_recommendation", "executive_summary", "key_findings"],
      {
        overall_rating: enumSchema(["pass", "pass_with_conditions", "needs_revision", "fail"]),
        overall_risk: enumSchema(["low", "medium", "high", "critical"]),
        approval_recommendation: enumSchema(["approve", "approve_with_conditions", "do_not_approve", "escalate_for_human_review"]),
        executive_summary: { type: "string" }, key_findings: stringArray,
      },
    ),
  },
} as const;

function enumSchema(values: readonly string[]) {
  return { type: "string", enum: values } as const;
}

function arraySchema(items: object) {
  return { type: "array", items } as const;
}

function objectSchema(required: readonly string[], properties: object) {
  return { type: "object", additionalProperties: false, required, properties } as const;
}
