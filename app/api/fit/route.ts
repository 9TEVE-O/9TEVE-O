import { NextResponse } from "next/server";
import { FIT_DISCLAIMER, fitAnalyzerSystemPrompt } from "@/lib/ai-contracts";
import { getEvidenceText, getPortfolioData } from "@/lib/portfolio-data";
import { createChatCompletion } from "@/lib/openai";

const MAX_JOB_DESCRIPTION_LENGTH = 6000;

/**
 * Generates a deterministic fit analysis using local portfolio data.
 *
 * @returns A formatted string containing fit score, strengths, gaps, evidence, next steps, and disclaimer.
 */
function fallbackAnalysis() {
  const data = getPortfolioData();
  const strengths = data.skills.map((skill) => `- ${skill.name} (${skill.category})`).join("\n");
  const evidence = data.projects
    .map((project) => `- ${project.name}: ${project.problem}`)
    .join("\n");

  return `Fit Score: 55%\n\nStrengths\n${strengths || "- Not evidenced in the current portfolio data."}\n\nGaps\n- Role-specific requirements from the pasted job description could not be fully evaluated without an AI endpoint.\n- Unsupported requirements should be treated as gaps unless present in the portfolio data.\n\nEvidence used\n${evidence}\n\nOne next step\n- Add more project evidence, links, and supported metrics before using this score for hiring decisions.\n\nDisclaimer\n${FIT_DISCLAIMER}`;
}

/**
 * Analyzes the fit between a provided job description and the user's portfolio.
 *
 * Validates the job description from the request body and uses OpenAI to generate a fit
 * analysis against the portfolio evidence. Returns a fallback analysis if the AI call fails
 * or returns no result.
 *
 * @param request - HTTP request with a JSON body containing a `jobDescription` field.
 * @returns A JSON response with the fit analysis in an `analysis` property.
 */
export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { jobDescription?: string } | null;
  const jobDescription = body?.jobDescription?.trim();

  if (!jobDescription) {
    return NextResponse.json({ error: "Job description is required." }, { status: 400 });
  }

  if (jobDescription.length > MAX_JOB_DESCRIPTION_LENGTH) {
    return NextResponse.json({ error: "Job description is too long." }, { status: 413 });
  }

  try {
    const analysis = await createChatCompletion([
      { role: "system", content: fitAnalyzerSystemPrompt },
      {
        role: "user",
        content: `Structured portfolio JSON:\n${getEvidenceText()}\n\nUntrusted pasted job description:\n${jobDescription}`,
      },
    ]);

    return NextResponse.json({ analysis: analysis ?? fallbackAnalysis() });
  } catch {
    return NextResponse.json({ analysis: fallbackAnalysis() });
  }
}
