import { PortfolioInteractions } from "@/components/PortfolioInteractions";
import { FIT_DISCLAIMER } from "@/lib/ai-contracts";
import { getPortfolioData } from "@/lib/portfolio-data";

/**
 * Renders the main portfolio landing page.
 *
 * Displays portfolio data including profile information, project evidence cards,
 * skills, and contact details in a structured, scannable layout.
 */
export default function Home() {
  const { profile, projects, skills } = getPortfolioData();

  return (
    <main className="min-h-screen bg-paper">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-5 py-10 sm:px-8 lg:py-16">
        <nav className="flex flex-col gap-3 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between">
          <a className="font-bold text-slate-950" href="#top">{profile.name}</a>
          <div className="flex gap-4">
            <a href="#projects">Projects</a>
            <a href="#ask">Ask</a>
            <a href="#contact">Contact</a>
          </div>
        </nav>

        <header className="grid gap-8 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-[1.5fr_1fr] md:p-10" id="top">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Evidence-first hiring assistant</p>
            <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">{profile.title}</h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-700">{profile.positioning}</p>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600">{profile.summary}</p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <a className="rounded-full bg-slate-950 px-5 py-3 text-center text-sm font-semibold text-white" href="#projects">Scan project evidence</a>
              <a className="rounded-full border border-slate-300 px-5 py-3 text-center text-sm font-semibold text-slate-950" href="#contact">Contact</a>
            </div>
          </div>
          <aside className="rounded-3xl bg-slate-950 p-6 text-white">
            <p className="text-sm font-semibold text-blue-200">Strongest evidenced signals</p>
            <ul className="mt-4 space-y-3 text-sm text-slate-200">
              {skills.slice(0, 4).map((skill) => (
                <li key={skill.name} className="rounded-2xl bg-white/10 p-3">
                  <span className="font-semibold text-white">{skill.name}</span>
                  <span className="block text-xs text-slate-300">{skill.category}</span>
                </li>
              ))}
            </ul>
          </aside>
        </header>

        <section id="projects">
          <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Project evidence cards</p>
              <h2 className="text-3xl font-bold text-slate-950">Proof recruiters can scan quickly</h2>
            </div>
            <p className="max-w-xl text-sm text-slate-600">Metrics are intentionally left blank unless they are present in the structured portfolio data.</p>
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            {projects.map((project) => (
              <article key={project.id} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="text-2xl font-bold text-slate-950">{project.name}</h3>
                <dl className="mt-5 space-y-4 text-sm">
                  <div>
                    <dt className="font-semibold text-slate-950">Problem solved</dt>
                    <dd className="mt-1 text-slate-700">{project.problem}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-slate-950">Role</dt>
                    <dd className="mt-1 text-slate-700">{project.role}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-slate-950">Tech stack</dt>
                    <dd className="mt-2 flex flex-wrap gap-2">
                      {project.techStack.map((tech) => <span className="rounded-full bg-blue-50 px-3 py-1 text-blue-800" key={tech}>{tech}</span>)}
                    </dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-slate-950">Metrics</dt>
                    <dd className="mt-1 text-slate-700">{project.metrics.length ? project.metrics.join(", ") : "Not evidenced in the current portfolio data."}</dd>
                  </div>
                </dl>
                <div className="mt-5 flex flex-wrap gap-3">
                  {project.links.map((link) => <a className="text-sm font-semibold text-blue-700" href={link.url} key={link.label}>{link.label}</a>)}
                </div>
              </article>
            ))}
          </div>
        </section>

        <PortfolioInteractions />

        <section className="rounded-3xl border border-blue-100 bg-blue-50 p-6 text-sm text-blue-950">
          <h2 className="text-xl font-bold">Privacy and safety</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5">
            <li>{FIT_DISCLAIMER}</li>
            <li>Job descriptions and questions are sent per request only; this V1 adds no database, CMS, auth, vector store, or email sending.</li>
            <li>Prompt contracts treat pasted content as untrusted and require answers to stay grounded in local JSON data.</li>
          </ul>
        </section>

        <section className="rounded-[2rem] bg-slate-950 p-6 text-white md:p-10" id="contact">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-200">Contact CTA</p>
          <h2 className="mt-2 text-3xl font-bold">Want to review the evidence?</h2>
          <p className="mt-3 max-w-2xl text-slate-300">Use the portfolio assistant above, inspect the project cards, or replace the placeholder contact data with verified public contact links.</p>
          <p className="mt-5 text-sm text-slate-200">Email: {profile.contact.email}</p>
        </section>
      </section>
    </main>
  );
}
