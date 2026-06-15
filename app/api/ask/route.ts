import { NextResponse } from "next/server";
import { askPortfolioSystemPrompt, MISSING_EVIDENCE } from "@/lib/ai-contracts";
import { getEvidenceText, getPortfolioData } from "@/lib/portfolio-data";
import { createChatCompletion } from "@/lib/openai";

const MAX_QUESTION_LENGTH = 1200;

/**
 * Generates a fallback answer using portfolio evidence that matches a recruiter question.
 *
 * @param question - The recruiter question to match against portfolio evidence
 * @returns A response containing project details if a match is found, or a fallback message with the closest available project
 */
function fallbackAnswer(question: string) {
  const normalizedQuestion = question.toLowerCase();
  const matchingProject = getPortfolioData().projects.find((project) =>
    [project.name, project.problem, project.role, ...project.techStack, ...project.evidence]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuestion.split(/\s+/).find((word) => word.length > 4) ?? normalizedQuestion),
  );

  if (!matchingProject) {
    return `${MISSING_EVIDENCE}\n\nNo relevant project was found in the current portfolio data.`;
  }

  return `Evidence found in project: ${matchingProject.name}.\n\nProblem: ${matchingProject.problem}\nRole: ${matchingProject.role}\nTech stack: ${matchingProject.techStack.join(", ") || MISSING_EVIDENCE}\nMetrics: ${matchingProject.metrics.join(", ") || MISSING_EVIDENCE}`;
}

/**
 * Answers recruiter questions using portfolio evidence.
 *
 * Validates the incoming question and queries an AI model with the question and portfolio evidence. Returns an AI-generated answer or a fallback answer based on portfolio keyword matching.
 *
 * @returns A JSON response containing `{ error: string }` if validation fails (missing or oversized question) or `{ answer: string }` with the generated answer.
 */
export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { question?: string } | null;
  const question = body?.question?.trim();

  if (!question) {
    return NextResponse.json({ error: "Question is required." }, { status: 400 });
  }

  if (question.length > MAX_QUESTION_LENGTH) {
    return NextResponse.json({ error: "Question is too long." }, { status: 413 });
  }

  const evidence = getEvidenceText();

  try {
    const answer = await createChatCompletion([
      { role: "system", content: askPortfolioSystemPrompt },
      { role: "user", content: `Structured portfolio JSON:\n${evidence}\n\nRecruiter question:\n${question}` },
    ]);

    return NextResponse.json({ answer: answer ?? fallbackAnswer(question) });
  } catch {
    return NextResponse.json({ answer: fallbackAnswer(question) });
  }
}
