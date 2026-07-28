import { readFile } from "node:fs/promises";
import { auditWorkflowEvidence } from "../lib/evidence-auditor/audit.ts";
import { parseAuditInput } from "../lib/evidence-auditor/schemas.ts";

async function main(): Promise<void> {
  const inputPath = process.argv[2];
  if (!inputPath) throw new Error("Usage: npm run audit:evidence -- <input.json>");

  const input = parseAuditInput(JSON.parse(await readFile(inputPath, "utf8")));
  const report = await auditWorkflowEvidence(input);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
