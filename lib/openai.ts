import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

const DEFAULT_MODEL = "gpt-4o-mini";

function readEnv(name: string): string | undefined {
  return process.env[name]?.trim() || undefined;
}

function getApiKey(): string | undefined {
  return readEnv("ATA_OPENAI_API_KEY") ?? readEnv("OPENAI_API_KEY");
}

function getBaseURL(): string | undefined {
  return readEnv("ATA_OPENAI_BASE_URL") ?? readEnv("OPENAI_BASE_URL");
}

function getModel(): string {
  return readEnv("ATA_OPENAI_MODEL") ?? readEnv("OPENAI_MODEL") ?? DEFAULT_MODEL;
}

export async function createChatCompletion(messages: ChatCompletionMessageParam[]): Promise<string | null> {
  const apiKey = getApiKey();

  if (!apiKey) {
    return null;
  }

  const client = new OpenAI({ apiKey, baseURL: getBaseURL() });
  const completion = await client.chat.completions.create({
    model: getModel(),
    messages,
    temperature: 0.2,
  });

  return completion.choices[0]?.message.content?.trim() || null;
}
