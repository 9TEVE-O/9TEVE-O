import OpenAI from "openai";
import type { ResponseCreateParamsNonStreaming } from "openai/resources/responses/responses";
import { getAuditorEnvironment, type AuditorEnvironment } from "./env.ts";
import {
  auditOutputJsonSchema,
  parseAuditInput,
  type AuditInput,
  type AuditOutput,
} from "./schemas.ts";

export async function auditWorkflowEvidence(
  input: AuditInput,
  environment: AuditorEnvironment = getAuditorEnvironment(),
): Promise<AuditOutput> {
  const validatedInput = parseAuditInput(input);
  const client = new OpenAI({ apiKey: environment.apiKey });

  const request = {
    model: environment.model,
    prompt: {
      id: environment.promptId,
      version: environment.promptVersion,
      variables: { audit_input_json: JSON.stringify(validatedInput, null, 2) },
    },
    text: {
      format: {
        type: "json_schema",
        name: "ai_workflow_evidence_audit",
        strict: true,
        schema: auditOutputJsonSchema,
      },
    },
    store: false,
  };

  // The installed v4 SDK predates reusable prompt typings, but its Responses
  // transport forwards these current API fields and supplies the output_text helper.
  const response = await client.responses.create(
    request as unknown as ResponseCreateParamsNonStreaming,
  );

  if (!response.output_text) {
    throw new Error("OpenAI Responses API returned no output_text");
  }

  try {
    return JSON.parse(response.output_text) as AuditOutput;
  } catch (error) {
    throw new Error("OpenAI Responses API returned invalid JSON", { cause: error });
  }
}
