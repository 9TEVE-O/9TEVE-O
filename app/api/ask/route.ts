import { NextResponse } from "next/server";
import { askPortfolioSystemPrompt, MISSING_EVIDENCE } from "@/lib/ai-contracts";
import { getEvidenceText, getPortfolioData } from "@/lib/portfolio-data";
import { createChatCompletion } from "@/lib/openai";

const MAX_QUESTION_LENGTH = 1200;

function fallbackAnswer(question: string) {
  const normalizedQuestion = question.toLowerCase();
  const matchingProject = getPortfolioData().projects.find((project) =>
    [project.name, project.problem, project.role, ...project.techStack, ...project.evidence]
      .join(" ")
      .toLowerCase()
      .includes(normalizedQuestion.split(/\s+/).find((word) => word.length > 4) ?? normalizedQuestion),
  );

  if (!matchingProject) {
    return `${MISSING_EVIDENCE}\n\nClosest relevant project: ${getPortfolioData().projects[0]?.name ?? MISSING_EVIDENCE}.`;
  }

  return `Evidence found in project: ${matchingProject.name}.\n\nProblem: ${matchingProject.problem}\nRole: ${matchingProject.role}\nTech stack: ${matchingProject.techStack.join(", ") || MISSING_EVIDENCE}\nMetrics: ${matchingProject.metrics.join(", ") || MISSING_EVIDENCE}`;
}

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
