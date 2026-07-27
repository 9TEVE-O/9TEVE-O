import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// mockCreate must be declared before vi.mock because vi.mock is hoisted
const mockCreate = vi.fn();

vi.mock("openai", () => {
  // Must use `function` (not arrow function) so it can be called with `new`
  const MockOpenAI = vi.fn(function (this: unknown, _opts: unknown) {
    return {
      chat: {
        completions: {
          create: mockCreate,
        },
      },
    };
  });
  return { default: MockOpenAI };
});

import { createChatCompletion } from "../openai";
import OpenAI from "openai";

const MockedOpenAI = vi.mocked(OpenAI);

describe("createChatCompletion", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetAllMocks();
    process.env = { ...originalEnv };
    delete process.env.ATA_OPENAI_API_KEY;
    delete process.env.ATA_OPENAI_BASE_URL;
    delete process.env.ATA_OPENAI_MODEL;
    delete process.env.OPENAI_API_KEY;
    delete process.env.OPENAI_BASE_URL;
    delete process.env.OPENAI_MODEL;
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe("when OPENAI_API_KEY is not set", () => {
    it("returns null without calling the OpenAI SDK", async () => {
      const result = await createChatCompletion([
        { role: "user", content: "Hello" },
      ]);

      expect(result).toBeNull();
      expect(MockedOpenAI).not.toHaveBeenCalled();
      expect(mockCreate).not.toHaveBeenCalled();
    });

    it("returns null when API key is an empty string", async () => {
      process.env.OPENAI_API_KEY = "";

      const result = await createChatCompletion([
        { role: "user", content: "Hello" },
      ]);

      expect(result).toBeNull();
      expect(MockedOpenAI).not.toHaveBeenCalled();
    });

    it("returns null when API key is only whitespace", async () => {
      process.env.OPENAI_API_KEY = "   ";

      const result = await createChatCompletion([
        { role: "user", content: "Hello" },
      ]);

      expect(result).toBeNull();
      expect(MockedOpenAI).not.toHaveBeenCalled();
    });
  });

  describe("when OPENAI_API_KEY is set", () => {
    const fakeApiKey = "sk-test-key-12345";

    beforeEach(() => {
      process.env.OPENAI_API_KEY = fakeApiKey;
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "response" } }],
      });
    });

    it("instantiates OpenAI with the trimmed API key", async () => {
      await createChatCompletion([{ role: "user", content: "Hello" }]);

      expect(MockedOpenAI).toHaveBeenCalledWith({ apiKey: fakeApiKey });
    });

    it("trims whitespace from the API key before passing it to the SDK", async () => {
      process.env.OPENAI_API_KEY = "  sk-padded-key  ";

      await createChatCompletion([{ role: "user", content: "Hello" }]);

      expect(MockedOpenAI).toHaveBeenCalledWith({ apiKey: "sk-padded-key" });
    });

    it("calls chat.completions.create with the provided messages", async () => {
      const messages = [
        { role: "system" as const, content: "You are helpful." },
        { role: "user" as const, content: "Tell me about yourself." },
      ];

      await createChatCompletion(messages);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ messages }),
      );
    });

    it("uses 'gpt-4o-mini' as the default model when OPENAI_MODEL is not set", async () => {
      await createChatCompletion([{ role: "user", content: "Hi" }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: "gpt-4o-mini" }),
      );
    });

    it("uses OPENAI_MODEL env var when it is set", async () => {
      process.env.OPENAI_MODEL = "gpt-4-turbo";

      await createChatCompletion([{ role: "user", content: "Hi" }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: "gpt-4-turbo" }),
      );
    });

    it("trims whitespace from OPENAI_MODEL", async () => {
      process.env.OPENAI_MODEL = "  gpt-4o  ";

      await createChatCompletion([{ role: "user", content: "Hi" }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: "gpt-4o" }),
      );
    });

    it("uses the default model when OPENAI_MODEL is only whitespace", async () => {
      process.env.OPENAI_MODEL = "   ";

      await createChatCompletion([{ role: "user", content: "Hi" }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ model: "gpt-4o-mini" }),
      );
    });

    it("calls chat.completions.create with temperature 0.2", async () => {
      await createChatCompletion([{ role: "user", content: "Hi" }]);

      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ temperature: 0.2 }),
      );
    });

    it("returns the content string from the first choice", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "This is the answer." } }],
      });

      const result = await createChatCompletion([
        { role: "user", content: "Question?" },
      ]);

      expect(result).toBe("This is the answer.");
    });

    it("trims whitespace from the returned content", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "  answer with padding  " } }],
      });

      const result = await createChatCompletion([
        { role: "user", content: "Question?" },
      ]);

      expect(result).toBe("answer with padding");
    });

    it("returns null when choices array is empty", async () => {
      mockCreate.mockResolvedValue({ choices: [] });

      const result = await createChatCompletion([
        { role: "user", content: "Hi" },
      ]);

      expect(result).toBeNull();
    });

    it("returns null when message content is null", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: null } }],
      });

      const result = await createChatCompletion([
        { role: "user", content: "Hi" },
      ]);

      expect(result).toBeNull();
    });

    it("returns null when message content is an empty string", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "" } }],
      });

      const result = await createChatCompletion([
        { role: "user", content: "Hi" },
      ]);

      expect(result).toBeNull();
    });

    it("returns null when message content is only whitespace", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "   " } }],
      });

      const result = await createChatCompletion([
        { role: "user", content: "Hi" },
      ]);

      expect(result).toBeNull();
    });

    it("propagates errors thrown by the OpenAI SDK", async () => {
      mockCreate.mockRejectedValue(new Error("Network error"));

      await expect(
        createChatCompletion([{ role: "user", content: "Hi" }]),
      ).rejects.toThrow("Network error");
    });

    it("handles an empty messages array without throwing", async () => {
      mockCreate.mockResolvedValue({
        choices: [{ message: { content: "response" } }],
      });

      const result = await createChatCompletion([]);

      expect(result).toBe("response");
      expect(mockCreate).toHaveBeenCalledWith(
        expect.objectContaining({ messages: [] }),
      );
    });
  });
});
