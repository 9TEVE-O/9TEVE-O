const ANALYTICS_EVENT_PREFIX = "portfolio";

export function trackEvent(eventName: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(
    new CustomEvent(`${ANALYTICS_EVENT_PREFIX}:${eventName}`, {
      detail: { eventName, timestamp: new Date().toISOString() },
    }),
  );
}
