import { describe, expect, it } from "vitest";
import fixture from "../fixtures/eval-001.input.json";
import { auditWorkflowEvidence } from "../src/audit.js";
import { AuditInputSchema } from "../src/schemas.js";

describe.skipIf(process.env.RUN_LIVE_EVAL !== "true")("live evaluation", () => {
  it("returns all seven outputs", async () => {
    const result = await auditWorkflowEvidence(AuditInputSchema.parse(fixture));
    expect(Object.keys(result)).toHaveLength(7);
  }, 60_000);
});
