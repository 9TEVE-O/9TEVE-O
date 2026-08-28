import { z } from "zod";

const NonEmptyString = z.string().trim().min(1);

export const EvidenceItemSchema = z.object({
  evidence_id: NonEmptyString,
  title: NonEmptyString,
  evidence_type: z.enum(["policy", "procedure", "ticket", "log", "dataset", "email", "approval", "contract", "regulation", "source_document", "other"]),
  authority_level: z.enum(["primary", "secondary", "informal", "unknown"]),
  source_reference: NonEmptyString,
  date: NonEmptyString.nullable(),
  excerpt_or_summary: NonEmptyString,
  known_limitations: z.string().nullable(),
}).strict();

export const AuditInputSchema = z.object({
  workflow_id: NonEmptyString,
  workflow_name: NonEmptyString,
  workflow_text: NonEmptyString,
  controlled_evidence_set: z.array(EvidenceItemSchema).min(1),
  review_context: z.object({
    requester: NonEmptyString.nullable(),
    domain: NonEmptyString.nullable(),
    decision_to_support: NonEmptyString.nullable(),
    applicable_policies: z.array(NonEmptyString),
    known_constraints: z.array(NonEmptyString),
  }).strict(),
}).strict().superRefine(({ controlled_evidence_set }, context) => {
  const seen = new Set<string>();
  controlled_evidence_set.forEach(({ evidence_id }, index) => {
    if (seen.has(evidence_id)) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: `duplicate evidence_id: ${evidence_id}`,
        path: ["controlled_evidence_set", index, "evidence_id"],
      });
    }
    seen.add(evidence_id);
  });
});

const WorkflowStepSchema = z.object({
  step_id: z.string(), actor: z.string(), action: z.string(), input_or_trigger: z.string(),
  output_or_decision: z.string(), claimed_basis: z.string(),
}).strict();
const MaterialClaimSchema = z.object({ claim_id: z.string(), claim_text: z.string(), location: z.string() }).strict();

export const AuditOutputSchema = z.object({
  workflow_reconstruction: z.object({
    workflow_id: z.string(), workflow_name: z.string(), objective: z.string(), scope_boundary: z.string(),
    reconstructed_steps: z.array(WorkflowStepSchema), decision_points: z.array(z.string()),
    material_claims: z.array(MaterialClaimSchema),
  }).strict(),
  evidence_and_authority_map: z.array(z.object({
    claim_or_step_id: z.string(), evidence_ids: z.array(z.string()),
    evidence_quality: z.enum(["strong", "moderate", "weak", "none"]),
    authority_assessment: z.enum(["clear_authority", "partial_authority", "unclear_authority", "no_authority"]),
    traceability: z.enum(["clear", "partial", "unclear", "absent"]), limitations: z.string(),
  }).strict()),
  unsupported_claim_register: z.array(z.object({
    claim_id: z.string(), claim_text: z.string(),
    status: z.enum(["supported", "partially_supported", "unsupported", "contradicted", "unverifiable", "overstated"]),
    why_not_fully_supported: z.string(), required_evidence: z.string(), risk_if_wrong: z.string(),
  }).strict()),
  reliability_and_governance_risk_register: z.array(z.object({
    risk_id: z.string(),
    category: z.enum(["evidence_quality", "traceability", "reasoning_gap", "procedural_gap", "compliance_or_policy", "operational", "privacy_or_security", "governance"]),
    severity: z.enum(["low", "medium", "high", "critical"]), likelihood: z.enum(["low", "medium", "high"]),
    description: z.string(), affected_claims_or_steps: z.array(z.string()), recommended_mitigation: z.string(),
  }).strict()),
  unresolved_question_register: z.array(z.object({
    question_id: z.string(), question: z.string(), owner_role: z.string(), blocking: z.boolean(), evidence_needed: z.string(),
  }).strict()),
  prioritised_corrective_actions: z.array(z.object({
    priority: z.enum(["p0", "p1", "p2", "p3"]), action: z.string(), rationale: z.string(),
    owner_role: z.string(), acceptance_criteria: z.string(),
  }).strict()),
  decision_ready_review_report: z.object({
    overall_rating: z.enum(["pass", "pass_with_conditions", "needs_revision", "fail"]),
    evidence_strength: z.enum(["strong", "moderate", "weak", "absent"]),
    overall_risk: z.enum(["low", "medium", "high", "critical"]),
    approval_recommendation: z.enum(["approve", "approve_with_conditions", "do_not_approve", "escalate_for_human_review"]),
    executive_summary: z.string(), key_findings: z.array(z.string()), required_conditions: z.array(z.string()),
    auditor_notes: z.string(),
  }).strict(),
}).strict();

export type AuditInput = z.infer<typeof AuditInputSchema>;
export type AuditOutput = z.infer<typeof AuditOutputSchema>;
