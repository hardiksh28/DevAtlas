import {
  BookOpenCheck,
  CheckCircle2,
  FileSearch,
  FolderPlus,
  GitPullRequest,
  Hammer,
  Map,
  Rocket,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";

import { DevAtlasLogo, DevAtlasMark } from "@/components/brand/Logo";
import { Badge } from "@/components/ui/Badge";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

// Link-as-button classes mirror packages/ui Button variants — the
// landing page navigates, so these must be real anchors, not buttons.
const primaryLink =
  "inline-flex min-h-10 items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover";
const secondaryLink =
  "inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-surface-muted";

const STEPS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: FolderPlus,
    title: "Start a project",
    body: "Pick something you actually want to exist — an API, an agent, a retrieval service.",
  },
  {
    icon: FileSearch,
    title: "Add documentation or a repository",
    body: "Bring the docs and code your project depends on so guidance stays grounded in your stack.",
  },
  {
    icon: Map,
    title: "Get a learning roadmap",
    body: "DevAtlas maps the concepts and milestones between where you are and a shipped project.",
  },
  {
    icon: Hammer,
    title: "Learn and build",
    body: "Short lessons arrive exactly when a milestone needs them. You write the code.",
  },
  {
    icon: GitPullRequest,
    title: "Review and improve code",
    body: "Your mentor reviews what you wrote — correctness, design, and the why behind both.",
  },
  {
    icon: Rocket,
    title: "Deploy with confidence",
    body: "Ship it for real, with guidance on infrastructure, monitoring, and cost.",
  },
];

const HINT_LEVELS = [
  {
    level: "Nudge",
    body: "A pointed question that redirects your attention to the right place.",
  },
  {
    level: "Concept",
    body: "The underlying idea explained — enough theory to reason with, no more.",
  },
  {
    level: "Approach",
    body: "A concrete strategy for this exact problem, still leaving the code to you.",
  },
  {
    level: "Walkthrough",
    body: "A worked example when you're truly stuck — followed by a similar challenge to prove it landed.",
  },
];

const FEATURES_NOW = [
  { title: "Accounts and secure sessions", body: "Email verification, password reset, and protected workspaces." },
  { title: "Project workspace", body: "Create, organize, archive, and restore the projects you're building." },
  { title: "Workspace dashboard", body: "Your projects and recent activity in one calm place." },
];

const FEATURES_PLANNED = [
  { title: "Documentation ingestion", body: "Ground your mentor in the docs and repos your project uses." },
  { title: "AI mentor chat", body: "A senior engineer that explains and questions — and knows when not to answer." },
  { title: "Roadmap generation", body: "A milestone plan from your project idea to deployment." },
  { title: "Lessons and quizzes", body: "Just-in-time learning attached to real milestones, with recall checks." },
  { title: "Code review", body: "Reviews of your actual code, tuned to what you're currently learning." },
  { title: "Deployment guidance", body: "From working-on-my-machine to running in production." },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link href="/" aria-label="DevAtlas home" className="rounded-md">
            <DevAtlasLogo size={26} />
          </Link>
          <nav className="flex items-center gap-1 sm:gap-2">
            <ThemeToggle />
            <Link
              href="/login"
              className="inline-flex min-h-10 items-center rounded-md px-3 text-sm font-medium text-ink-secondary transition-colors hover:bg-surface-muted hover:text-ink"
            >
              Sign in
            </Link>
            <Link href="/register" className={primaryLink}>
              Create account
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="mx-auto grid max-w-6xl gap-12 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:py-24">
          <div className="max-w-xl">
            <p className="font-mono text-xs font-medium uppercase tracking-widest text-accent-ink">
              Project-first AI engineering learning
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
              Build one real AI project. Learn everything it takes to ship it.
            </h1>
            <p className="mt-5 text-base leading-relaxed text-ink-secondary sm:text-lg">
              DevAtlas pairs you with a mentor that explains concepts, asks the right questions,
              and reviews your code — while you build production software, not toy exercises.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register" className={primaryLink}>
                Start building
              </Link>
              <a href="#how-it-works" className={secondaryLink}>
                Explore how it works
              </a>
            </div>
          </div>

          {/* Product preview — composed from the app's real panel styles,
              clearly labeled as an illustration of where the product is going. */}
          <div aria-hidden="true" className="hidden sm:block">
            <div className="rounded-xl border border-line bg-surface p-4 shadow-raised">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <p className="font-mono text-xs text-ink-muted">retrieval-service · roadmap</p>
                <Badge variant="accent">Milestone 2 of 6</Badge>
              </div>
              <ul className="mt-3 space-y-2.5">
                <li className="flex items-center gap-2.5 text-sm text-ink-muted">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-success-ink" />
                  <span className="line-through decoration-line-strong">Scope the project and stack</span>
                </li>
                <li className="flex items-center gap-2.5 text-sm font-medium text-ink">
                  <span className="flex h-4 w-4 shrink-0 items-center justify-center">
                    <span className="h-2.5 w-2.5 rounded-full bg-accent" />
                  </span>
                  Build the document ingestion pipeline
                </li>
                <li className="flex items-center gap-2.5 text-sm text-ink-muted">
                  <span className="flex h-4 w-4 shrink-0 items-center justify-center">
                    <span className="h-2 w-2 rounded-full border border-line-strong" />
                  </span>
                  Design chunking and embeddings
                </li>
                <li className="flex items-center gap-2.5 text-sm text-ink-muted">
                  <span className="flex h-4 w-4 shrink-0 items-center justify-center">
                    <span className="h-2 w-2 rounded-full border border-line-strong" />
                  </span>
                  Evaluate retrieval quality
                </li>
              </ul>
              <div className="mt-4 rounded-lg border border-line bg-surface-muted p-3">
                <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
                  Mentor · hint 1 of 4
                </p>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-secondary">
                  Before reaching for a vector database — what does “relevant” mean for your
                  users’ queries? Try writing three example queries first.
                </p>
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-ink-faint">
              An illustration of the DevAtlas workspace, built from the product’s own components.
            </p>
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
            <div className="max-w-xl">
              <h2 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                How it works
              </h2>
              <p className="mt-3 text-ink-secondary">
                One project, start to finish. Every step exists to get your software shipped —
                and to make sure you understand it.
              </p>
            </div>
            <ol className="mt-10 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
              {STEPS.map((step, i) => (
                <li key={step.title} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-line bg-canvas text-accent-ink">
                      <step.icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                  </div>
                  <div>
                    <p className="font-mono text-xs text-ink-faint">0{i + 1}</p>
                    <h3 className="mt-0.5 text-sm font-semibold text-ink">{step.title}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{step.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Mentor, not answer machine */}
        <section className="border-t border-line">
          <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div className="max-w-xl">
              <h2 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                A mentor, not an answer machine
              </h2>
              <p className="mt-3 leading-relaxed text-ink-secondary">
                Pasting generated code teaches you nothing. The DevAtlas mentor works like a good
                senior engineer: it starts with a question, escalates help only when you need it,
                and steps back as you get stronger.
              </p>
              <p className="mt-3 leading-relaxed text-ink-secondary">
                Assistance is progressive — four levels, in order, never skipping ahead of your
                effort.
              </p>
            </div>
            <ol className="space-y-3">
              {HINT_LEVELS.map((hint, i) => (
                <li
                  key={hint.level}
                  className="flex gap-4 rounded-lg border border-line bg-surface p-4"
                >
                  <span className="font-mono text-sm font-semibold text-accent-ink">{i + 1}</span>
                  <div>
                    <p className="text-sm font-semibold text-ink">{hint.level}</p>
                    <p className="mt-1 text-sm leading-relaxed text-ink-muted">{hint.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Feature grid: now vs planned */}
        <section className="border-t border-line bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
            <div className="max-w-xl">
              <h2 className="text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
                Where DevAtlas is today
              </h2>
              <p className="mt-3 text-ink-secondary">
                We&apos;re building in the open. Here&apos;s exactly what works now and what&apos;s
                coming.
              </p>
            </div>

            <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_2fr]">
              <div>
                <Badge variant="success">Available now</Badge>
                <ul className="mt-4 space-y-4">
                  {FEATURES_NOW.map((f) => (
                    <li key={f.title}>
                      <h3 className="text-sm font-semibold text-ink">{f.title}</h3>
                      <p className="mt-1 text-sm text-ink-muted">{f.body}</p>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <Badge variant="outline">In development</Badge>
                <ul className="mt-4 grid gap-x-8 gap-y-4 sm:grid-cols-2">
                  {FEATURES_PLANNED.map((f) => (
                    <li key={f.title}>
                      <h3 className="text-sm font-semibold text-ink">{f.title}</h3>
                      <p className="mt-1 text-sm text-ink-muted">{f.body}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-4 py-16 sm:px-6 sm:py-20">
            <BookOpenCheck className="h-8 w-8 text-accent-ink" aria-hidden="true" />
            <h2 className="max-w-2xl text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
              The best way to learn AI engineering is to ship an AI project.
            </h2>
            <Link href="/register" className={primaryLink}>
              Start building
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-2 text-ink-muted">
            <DevAtlasMark monochrome className="h-5 w-5" />
            <span className="text-sm">DevAtlas — learn AI engineering by building.</span>
          </div>
          <nav className="flex gap-5 text-sm text-ink-muted">
            <Link href="/login" className="transition-colors hover:text-ink">
              Sign in
            </Link>
            <Link href="/register" className="transition-colors hover:text-ink">
              Create account
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
