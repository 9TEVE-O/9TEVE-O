import OpenAI from "openai";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

const DEFAULT_MODEL = "gpt-4o-mini";

function getApiKey(): string | undefined {
  return process.env.ATA_OPENAI_API_KEY?.trim() || undefined;
}

export async function createChatCompletion(messages: ChatCompletionMessageParam[]): Promise<string | null> {
  const apiKey = getApiKey();

  if (!apiKey) {
    return null;
  }

  const client = new OpenAI({
    apiKey,
    baseURL: process.env.ATA_OPENAI_BASE_URL?.trim() || undefined,
  });
  const completion = await client.chat.completions.create({
    model: process.env.ATA_OPENAI_MODEL?.trim() || DEFAULT_MODEL,
    messages,
    temperature: 0.2,
  });

  return completion.choices[0]?.message.content?.trim() || null;
}
