"use client";

import { FormEvent, useState } from "react";
import { trackEvent } from "@/lib/analytics";

/**
 * Renders two interactive forms for querying portfolio experience and analyzing job fit.
 *
 * The "Ask My Portfolio" form allows users to ask questions about their project experience, with answers constrained to local portfolio data. The "Fit Analyzer" form accepts a pasted job description and provides analysis of portfolio alignment. Results appear in formatted text blocks when available, and submit buttons show loading state during request processing.
 */
export function PortfolioInteractions() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function askPortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsAsking(true);
    trackEvent("ask_portfolio_submitted");
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = (await response.json()) as { answer?: string; error?: string };
      setAnswer(data.answer ?? data.error ?? "Unable to answer from portfolio data.");
    } finally {
      setIsAsking(false);
    }
  }

  async function analyzeFit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsAnalyzing(true);
    trackEvent("fit_analyzer_submitted");
    try {
      const response = await fetch("/api/fit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jobDescription }),
      });
      const data = (await response.json()) as { analysis?: string; error?: string };
      setAnalysis(data.analysis ?? data.error ?? "Unable to analyze fit from portfolio data.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-2" id="ask">
      <form onSubmit={askPortfolio} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Ask My Portfolio</p>
        <h2 className="mt-2 text-2xl font-bold text-slate-950">Ask about evidenced project experience</h2>
        <p className="mt-2 text-sm text-slate-600">
          Answers are constrained to local portfolio data. Missing evidence is called out explicitly.
        </p>
        <textarea
          className="mt-5 min-h-32 w-full rounded-2xl border border-slate-300 p-4 text-sm outline-none ring-blue-200 focus:ring-4"
          maxLength={1200}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: What evidence shows backend or governance automation experience?"
          required
          value={question}
        />
        <button className="mt-4 rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60" disabled={isAsking}>
          {isAsking ? "Checking evidence..." : "Ask portfolio"}
        </button>
        {answer ? <pre className="mt-5 whitespace-pre-wrap rounded-2xl bg-slate-100 p-4 text-sm text-slate-800">{answer}</pre> : null}
      </form>

      <form onSubmit={analyzeFit} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" id="fit">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Fit Analyzer</p>
        <h2 className="mt-2 text-2xl font-bold text-slate-950">Paste a job description</h2>
        <p className="mt-2 text-sm text-slate-600">
          Raw job descriptions are not stored by default. Analytics events exclude pasted text.
        </p>
        <textarea
          className="mt-5 min-h-32 w-full rounded-2xl border border-slate-300 p-4 text-sm outline-none ring-blue-200 focus:ring-4"
          maxLength={6000}
          onChange={(event) => setJobDescription(event.target.value)}
          placeholder="Paste role requirements here..."
          required
          value={jobDescription}
        />
        <button className="mt-4 rounded-full bg-blue-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60" disabled={isAnalyzing}>
          {isAnalyzing ? "Analyzing evidence..." : "Analyze fit"}
        </button>
        {analysis ? <pre className="mt-5 whitespace-pre-wrap rounded-2xl bg-slate-100 p-4 text-sm text-slate-800">{analysis}</pre> : null}
      </form>
    </section>
  );
}
