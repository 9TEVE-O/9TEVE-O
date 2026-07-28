import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { getEnvironment, type AppEnvironment } from "./env.js";
import { AuditInputSchema, AuditOutputSchema, type AuditInput, type AuditOutput } from "./schemas.js";

export async function auditWorkflowEvidence(
  input: AuditInput,
  environment: AppEnvironment = getEnvironment(),
  client: OpenAI = new OpenAI({ apiKey: environment.OPENAI_API_KEY }),
): Promise<AuditOutput> {
  const validatedInput = AuditInputSchema.parse(input);
  const response = await client.responses.parse({
    model: environment.OPENAI_AUDITOR_MODEL,
    prompt: {
      id: environment.OPENAI_AUDITOR_PROMPT_ID,
      version: environment.OPENAI_AUDITOR_PROMPT_VERSION,
      variables: { audit_input_json: JSON.stringify(validatedInput, null, 2) },
    },
    text: { format: zodTextFormat(AuditOutputSchema, "ai_workflow_evidence_audit") },
    store: false,
  });

  if (!response.output_parsed) {
    throw new Error("OpenAI Responses API returned no parsed audit output");
  }
  return response.output_parsed;
}
