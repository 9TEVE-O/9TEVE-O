export interface AuditorEnvironment {
  apiKey: string;
  promptId: string;
  promptVersion: string;
  model: string;
}

type EnvironmentSource = Record<string, string | undefined>;

function required(env: EnvironmentSource, name: string): string {
  const value = env[name]?.trim();
  if (!value) throw new Error(`${name} is required`);
  return value;
}

export function getAuditorEnvironment(env: EnvironmentSource = process.env): AuditorEnvironment {
  return {
    apiKey: required(env, "OPENAI_API_KEY"),
    promptId: required(env, "OPENAI_AUDITOR_PROMPT_ID"),
    promptVersion: required(env, "OPENAI_AUDITOR_PROMPT_VERSION"),
    model: env.OPENAI_AUDITOR_MODEL?.trim() || "gpt-5.5",
  };
}
