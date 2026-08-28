import { readFile } from "node:fs/promises";
import { auditWorkflowEvidence } from "./audit.js";
import { AuditInputSchema } from "./schemas.js";

async function main(): Promise<void> {
  const inputPath = process.argv[2];
  if (!inputPath) throw new Error("Usage: npm run audit -- <input.json>");
  const input = AuditInputSchema.parse(JSON.parse(await readFile(inputPath, "utf8")));
  const report = await auditWorkflowEvidence(input);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
