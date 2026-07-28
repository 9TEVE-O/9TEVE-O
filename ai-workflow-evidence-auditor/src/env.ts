import { existsSync } from "node:fs";
import { loadEnvFile } from "node:process";
import { z } from "zod";

if (existsSync(".env")) loadEnvFile(".env");

const EnvironmentSchema = z.object({
  OPENAI_API_KEY: z
    .string({ required_error: "OPENAI_API_KEY is required" })
    .trim()
    .min(1, "OPENAI_API_KEY is required"),
  OPENAI_AUDITOR_PROMPT_ID: z
    .string({ required_error: "OPENAI_AUDITOR_PROMPT_ID is required" })
    .trim()
    .min(1, "OPENAI_AUDITOR_PROMPT_ID is required"),
  OPENAI_AUDITOR_PROMPT_VERSION: z
    .string({ required_error: "OPENAI_AUDITOR_PROMPT_VERSION is required" })
    .trim()
    .regex(/^\d+$/, "OPENAI_AUDITOR_PROMPT_VERSION must be a numeric version"),
  OPENAI_MODEL: z.string().trim().min(1).default("gpt-5.5"),
});

export type AppEnvironment = z.infer<typeof EnvironmentSchema>;

export function getEnvironment(environment: NodeJS.ProcessEnv = process.env): AppEnvironment {
  return EnvironmentSchema.parse(environment);
}
