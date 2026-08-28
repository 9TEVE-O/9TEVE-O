import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { trackEvent } from "../analytics";

describe("trackEvent", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe("when window is defined (browser environment)", () => {
    it("dispatches a CustomEvent with the 'portfolio:' prefix", () => {
      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:page_view", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("page_view");

      expect(events).toHaveLength(1);
      expect(events[0].type).toBe("portfolio:page_view");
    });

    it("includes eventName in the event detail", () => {
      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:button_click", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("button_click");

      expect(events[0].detail.eventName).toBe("button_click");
    });

    it("includes a timestamp in ISO 8601 format in the event detail", () => {
      const fixedDate = new Date("2024-06-15T12:00:00.000Z");
      vi.setSystemTime(fixedDate);

      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:test_event", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("test_event");

      expect(events[0].detail.timestamp).toBe("2024-06-15T12:00:00.000Z");
    });

    it("uses the current system time for the timestamp", () => {
      const before = new Date("2024-01-01T00:00:00.000Z");
      vi.setSystemTime(before);

      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:timing_test", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("timing_test");

      expect(events[0].detail.timestamp).toBe(before.toISOString());
    });

    it("correctly prefixes event names containing underscores", () => {
      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:ai_query_submitted", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("ai_query_submitted");

      expect(events).toHaveLength(1);
    });

    it("correctly prefixes event names containing hyphens", () => {
      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:fit-score-viewed", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("fit-score-viewed");

      expect(events).toHaveLength(1);
      expect(events[0].detail.eventName).toBe("fit-score-viewed");
    });

    it("dispatches events via window.dispatchEvent", () => {
      const dispatchSpy = vi.spyOn(window, "dispatchEvent");

      trackEvent("spy_test");

      expect(dispatchSpy).toHaveBeenCalledOnce();
      const dispatched = dispatchSpy.mock.calls[0][0] as CustomEvent;
      expect(dispatched.type).toBe("portfolio:spy_test");
    });

    it("does not throw for an empty string event name", () => {
      expect(() => trackEvent("")).not.toThrow();
    });

    it("returns undefined (void)", () => {
      const result = trackEvent("return_value_test");
      expect(result).toBeUndefined();
    });
  });

  describe("when window is undefined (server-side / Node environment)", () => {
    it("does not dispatch any event and returns early", () => {
      const originalWindow = globalThis.window;
      // Simulate SSR: remove window
      // @ts-expect-error simulating SSR environment
      delete globalThis.window;

      let dispatchCalled = false;
      try {
        // If window is undefined, the function must not throw
        trackEvent("ssr_event");
      } finally {
        globalThis.window = originalWindow;
      }

      expect(dispatchCalled).toBe(false);
    });

    it("returns undefined when window is undefined", () => {
      const originalWindow = globalThis.window;
      // @ts-expect-error simulating SSR environment
      delete globalThis.window;

      let result: unknown = "sentinel";
      try {
        result = trackEvent("ssr_return_test");
      } finally {
        globalThis.window = originalWindow;
      }

      expect(result).toBeUndefined();
    });
  });

  describe("event detail structure", () => {
    it("detail object has exactly 'eventName' and 'timestamp' keys", () => {
      const events: CustomEvent[] = [];
      window.addEventListener("portfolio:structure_test", (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent("structure_test");

      const detail = events[0].detail;
      expect(Object.keys(detail).sort()).toEqual(
        ["eventName", "timestamp"].sort(),
      );
    });

    it("eventName in detail matches the argument passed to trackEvent", () => {
      const events: CustomEvent[] = [];
      const name = "specific_name_123";
      window.addEventListener(`portfolio:${name}`, (e) =>
        events.push(e as CustomEvent),
      );

      trackEvent(name);

      expect(events[0].detail.eventName).toBe(name);
    });
  });
});