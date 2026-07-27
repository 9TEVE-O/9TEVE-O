import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ChatCompletionMessageParam } from "openai/resources/chat/completions";

const openAIMocks = vi.hoisted(() => {
  const create = vi.fn();
  const constructor = vi.fn(function () {
    return {
      chat: {
        completions: {
          create,
        },
      },
    };
  });

  return { constructor, create };
});

vi.mock("openai", () => ({
  default: openAIMocks.constructor,
}));

import { createChatCompletion } from "../lib/openai";

const messages: ChatCompletionMessageParam[] = [{ role: "user", content: "Summarize this." }];

function clearOpenAIEnv() {
  delete process.env.ATA_OPENAI_API_KEY;
  delete process.env.ATA_OPENAI_BASE_URL;
  delete process.env.ATA_OPENAI_MODEL;
  delete process.env.OPENAI_API_KEY;
  delete process.env.OPENAI_BASE_URL;
  delete process.env.OPENAI_MODEL;
}

describe("createChatCompletion", () => {
  beforeEach(() => {
    clearOpenAIEnv();
    openAIMocks.create.mockResolvedValue({
      choices: [{ message: { content: "  AI answer  " } }],
    });
  });

  afterEach(() => {
    clearOpenAIEnv();
    vi.clearAllMocks();
  });

  it("returns null without a configured API key", async () => {
    await expect(createChatCompletion(messages)).resolves.toBeNull();

    expect(openAIMocks.constructor).not.toHaveBeenCalled();
    expect(openAIMocks.create).not.toHaveBeenCalled();
  });

  it("uses documented ATA OpenAI settings for the client and model", async () => {
    process.env.ATA_OPENAI_API_KEY = "  ata-key  ";
    process.env.ATA_OPENAI_BASE_URL = "  https://example.test/v1  ";
    process.env.ATA_OPENAI_MODEL = "  ata-model  ";

    await expect(createChatCompletion(messages)).resolves.toBe("AI answer");

    expect(openAIMocks.constructor).toHaveBeenCalledWith({
      apiKey: "ata-key",
      baseURL: "https://example.test/v1",
    });
    expect(openAIMocks.create).toHaveBeenCalledWith({
      model: "ata-model",
      messages,
      temperature: 0.2,
    });
  });

  it("prefers documented ATA settings over legacy unprefixed settings", async () => {
    process.env.ATA_OPENAI_API_KEY = "ata-key";
    process.env.ATA_OPENAI_BASE_URL = "https://example.test/v1";
    process.env.ATA_OPENAI_MODEL = "ata-model";
    process.env.OPENAI_API_KEY = "legacy-key";
    process.env.OPENAI_BASE_URL = "https://legacy.example.test/v1";
    process.env.OPENAI_MODEL = "legacy-model";

    await expect(createChatCompletion(messages)).resolves.toBe("AI answer");

    expect(openAIMocks.constructor).toHaveBeenCalledWith({
      apiKey: "ata-key",
      baseURL: "https://example.test/v1",
    });
    expect(openAIMocks.create).toHaveBeenCalledWith({
      model: "ata-model",
      messages,
      temperature: 0.2,
    });
  });

  it("falls back to legacy unprefixed settings", async () => {
    process.env.OPENAI_API_KEY = "  legacy-key  ";
    process.env.OPENAI_BASE_URL = "  https://legacy.example.test/v1  ";
    process.env.OPENAI_MODEL = "  legacy-model  ";

    await expect(createChatCompletion(messages)).resolves.toBe("AI answer");

    expect(openAIMocks.constructor).toHaveBeenCalledWith({
      apiKey: "legacy-key",
      baseURL: "https://legacy.example.test/v1",
    });
    expect(openAIMocks.create).toHaveBeenCalledWith({
      model: "legacy-model",
      messages,
      temperature: 0.2,
    });
  });
});
