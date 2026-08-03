"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRight,
  FolderPlus,
  FileSearch,
  Map,
  Hammer,
  GitPullRequest,
  Rocket,
  CheckCircle2,
  Clock,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { DevAtlasLogo, DevAtlasMark } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { HeroAlgorithmVisual } from "@/components/landing/HeroAlgorithmVisual";
import { ApproachComparisonVisual } from "@/components/landing/ApproachComparisonVisual";
import { InteractiveMentorVisual } from "@/components/landing/InteractiveMentorVisual";

const STEPS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: FolderPlus,
    title: "Start a project",
    body: "Pick something you actually want to exist — an API, an agent, or a retrieval service.",
  },
  {
    icon: FileSearch,
    title: "Add documentation or a repo",
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
    body: "Short lessons arrive exactly when a milestone needs them. You write the actual code.",
  },
  {
    icon: GitPullRequest,
    title: "Review and improve code",
    body: "Your mentor reviews what you wrote — correctness, design, and the architectural why.",
  },
  {
    icon: Rocket,
    title: "Deploy with confidence",
    body: "Ship it for real, with guidance on infrastructure, monitoring, and cost budgets.",
  },
];

const FEATURES_NOW = [
  {
    title: "Accounts and secure sessions",
    body: "Email verification, password reset, and protected workspaces.",
  },
  {
    title: "Project workspace",
    body: "Create, organize, archive, and restore the projects you're building.",
  },
  {
    title: "Workspace dashboard",
    body: "Your projects and recent activity organized in one calm place.",
  },
];

const FEATURES_PLANNED = [
  {
    title: "Documentation ingestion",
    body: "Ground your mentor in the docs and repos your project uses.",
  },
  {
    title: "AI mentor chat",
    body: "A senior engineer that explains and questions — and knows when not to answer.",
  },
  {
    title: "Roadmap generation",
    body: "A milestone plan generated from your project idea to production deployment.",
  },
  {
    title: "Lessons and quizzes",
    body: "Just-in-time learning attached to real milestones, with active recall checks.",
  },
  {
    title: "Code review",
    body: "Reviews of your actual code, tuned to what you're currently learning.",
  },
  {
    title: "Deployment guidance",
    body: "From working-on-my-machine to running reliably in production.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-ink selection:bg-[#F0653A]/20 selection:text-[#F0653A] font-sans antialiased">
      {/* Header / Navigation */}
      <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          {/* Logo */}
          <Link href="/" aria-label="DevAtlas home" className="group">
            <DevAtlasLogo size={24} />
          </Link>

          {/* Right Controls */}
          <div className="flex items-center gap-3 sm:gap-4">
            <ThemeToggle />
            <Link
              href="/login"
              className="text-sm font-medium text-ink-secondary hover:text-ink transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-lg border border-line-strong/60 bg-surface px-4 py-1.5 text-sm font-medium text-ink hover:bg-surface-muted transition-all dark:border-[#3E3B34] dark:bg-surface-card"
            >
              Create account
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* ================= HERO SECTION ================= */}
        <section className="mx-auto max-w-6xl px-4 pt-12 pb-16 sm:px-6 sm:pt-16 sm:pb-24 lg:pt-20 lg:pb-28">
          <div className="grid gap-12 lg:grid-cols-[1.1fr_1fr] lg:items-center">
            {/* Left Column: Hero Copy */}
            <div className="max-w-xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#F0653A] dark:text-[#FF7A50]">
                PROJECT-FIRST AI ENGINEERING LEARNING
              </p>

              <h1 className="mt-4 text-4xl font-extrabold tracking-[-0.03em] leading-[1.08] text-ink sm:text-5xl lg:text-[58px]">
                Build one real AI project. <br />
                Learn everything it takes to{" "}
                <span className="text-[#F0653A] dark:text-[#FF7A50]">ship it</span>.
              </h1>

              <p className="mt-6 text-base sm:text-lg leading-relaxed text-ink-secondary">
                DevAtlas pairs you with a mentor that explains concepts, asks the right questions,
                and reviews your code — while you build production software, not toy exercises.
              </p>

              {/* Action Buttons */}
              <div className="mt-8 flex flex-wrap items-center gap-3 sm:gap-4">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#181613] px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-[#2E2B27] dark:bg-[#F6F4EF] dark:text-[#161513] dark:hover:bg-white shadow-sm"
                >
                  <span>Start building free</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center rounded-lg border border-line-strong/40 bg-surface px-5 py-3 text-sm font-semibold text-ink transition-colors hover:bg-surface-muted dark:border-[#3E3B34] dark:bg-surface-card"
                >
                  Explore how it works
                </a>
              </div>
            </div>

            {/* Right Column: Hero Live Interactive Pipeline Card */}
            <div>
              <HeroAlgorithmVisual />
            </div>
          </div>
        </section>

        {/* ================= SECTION 2: ARCHITECTURE COMPARISON (ZIG-ZAG) ================= */}
        <section className="border-t border-line bg-canvas py-16 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:items-center">
              {/* Left Column: Interactive Architecture Card */}
              <div className="order-2 lg:order-1">
                <ApproachComparisonVisual />
              </div>

              {/* Right Column: Editorial Copy */}
              <div className="order-1 max-w-xl lg:order-2">
                <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#F0653A] dark:text-[#FF7A50]">
                  NAIVE PROMPT → PRODUCTION ARCHITECTURE
                </p>

                <h2 className="mt-3 text-3xl font-extrabold tracking-[-0.02em] leading-[1.12] text-ink sm:text-4xl lg:text-[46px]">
                  Never stop at the <span className="text-[#F0653A] dark:text-[#FF7A50]">first</span> <br />
                  prompt.
                </h2>

                <p className="mt-5 text-base leading-relaxed text-ink-secondary">
                  Every AI system carries its architecture side by side — the obvious single prompt
                  and the production pipeline. Jump between them in a tap and watch hallucination
                  drop and latency fall, so you learn the <em>why</em>, not just the trick.
                </p>

                <div className="mt-7">
                  <a
                    href="#how-it-works"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink underline underline-offset-4 decoration-2 decoration-[#F0653A] hover:text-[#F0653A] transition-colors"
                  >
                    <span>Explore real architectural workflows</span>
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ================= SECTION 3: SOCRATIC AI MENTOR ================= */}
        <section className="border-t border-line bg-canvas py-16 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid gap-12 lg:grid-cols-[1.1fr_1fr] lg:items-center">
              {/* Left Column: Editorial Copy */}
              <div className="max-w-xl">
                <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#F0653A] dark:text-[#FF7A50]">
                  SOCRATIC AI MENTOR
                </p>

                <h2 className="mt-3 text-3xl font-extrabold tracking-[-0.02em] leading-[1.12] text-ink sm:text-4xl lg:text-[46px]">
                  A mentor that questions, not an <span className="text-[#F0653A] dark:text-[#FF7A50]">answer</span> machine.
                </h2>

                <p className="mt-5 text-base leading-relaxed text-ink-secondary">
                  Pasting generated code teaches you nothing. The DevAtlas mentor works like a good
                  senior engineer: it starts with a question, escalates help only when you need it,
                  and steps back as you get stronger.
                </p>

                <p className="mt-3 text-sm text-ink-muted leading-relaxed">
                  Assistance is progressive — four levels, in order, never skipping ahead of your effort.
                </p>

                <div className="mt-7">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink underline underline-offset-4 decoration-2 decoration-[#F0653A] hover:text-[#F0653A] transition-colors"
                  >
                    <span>Try the 4-level hint ladder</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              {/* Right Column: Interactive Mentor Ladder Card */}
              <div>
                <InteractiveMentorVisual />
              </div>
            </div>
          </div>
        </section>

        {/* ================= SECTION 4: 6-STEP WORKFLOW ================= */}
        <section id="how-it-works" className="border-t border-line bg-surface py-16 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="max-w-xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-ink-muted">
                HOW IT WORKS
              </p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
                One project, start to finish.
              </h2>
              <p className="mt-3 text-base text-ink-secondary">
                Every step exists to get your software shipped — and to make sure you understand it.
              </p>
            </div>

            <ol className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {STEPS.map((step, i) => {
                const Icon = step.icon;
                return (
                  <li
                    key={step.title}
                    className="flex flex-col justify-between rounded-2xl border-2 border-line-strong/70 bg-canvas p-6 shadow-sm transition-all duration-300 hover:border-[#F0653A] hover:shadow-raised dark:border-[#36342E]"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-[#F0653A] dark:text-[#FF8259]">
                          0{i + 1}
                        </span>
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-surface text-ink">
                          <Icon className="h-4 w-4" />
                        </div>
                      </div>

                      <h3 className="mt-4 text-base font-bold text-ink">
                        {step.title}
                      </h3>
                      <p className="mt-2 text-xs leading-relaxed text-ink-secondary">
                        {step.body}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </section>

        {/* ================= SECTION 5: WHERE DEVATLAS IS TODAY ================= */}
        <section className="border-t border-line bg-canvas py-16 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="max-w-xl">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-ink-muted">
                PROJECT ROADMAP
              </p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
                Where DevAtlas is today
              </h2>
              <p className="mt-3 text-base text-ink-secondary">
                We&apos;re building in the open. Here&apos;s exactly what works now and what&apos;s
                coming next.
              </p>
            </div>

            <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_1.8fr]">
              {/* Available Now Card */}
              <div className="rounded-2xl border-2 border-line-strong/80 bg-surface p-6 shadow-sm dark:border-[#36342E] dark:bg-surface-card">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 font-mono text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Available now
                </div>

                <ul className="mt-6 space-y-5">
                  {FEATURES_NOW.map((f) => (
                    <li key={f.title} className="border-b border-line pb-4 last:border-b-0 last:pb-0">
                      <h3 className="text-sm font-bold text-ink">{f.title}</h3>
                      <p className="mt-1 text-xs text-ink-secondary leading-relaxed">{f.body}</p>
                    </li>
                  ))}
                </ul>
              </div>

              {/* In Development Card */}
              <div className="rounded-2xl border-2 border-line-strong/80 bg-surface p-6 shadow-sm dark:border-[#36342E] dark:bg-surface-card">
                <div className="inline-flex items-center gap-1.5 rounded-full bg-[#FEF3EC] px-3 py-1 font-mono text-xs font-semibold text-[#E05327] dark:bg-[#2C1E18] dark:text-[#FF8259]">
                  <Clock className="h-3.5 w-3.5" />
                  In active development
                </div>

                <ul className="mt-6 grid gap-x-8 gap-y-5 sm:grid-cols-2">
                  {FEATURES_PLANNED.map((f) => (
                    <li key={f.title} className="border-b border-line pb-4 last:border-b-0 last:pb-0 sm:last:border-b">
                      <h3 className="text-sm font-bold text-ink">{f.title}</h3>
                      <p className="mt-1 text-xs text-ink-secondary leading-relaxed">{f.body}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ================= FINAL CTA ================= */}
        <section className="border-t border-line bg-surface py-16 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="rounded-3xl border-2 border-line-strong/80 bg-canvas p-8 text-center sm:p-12 lg:p-16 dark:border-[#36342E] shadow-raised">
              <div className="mx-auto max-w-2xl">
                <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#F0653A] dark:text-[#FF7A50]">
                  START BUILDING TODAY
                </p>
                <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
                  The best way to learn AI engineering is to ship an AI project.
                </h2>
                <p className="mt-4 text-base text-ink-secondary">
                  DevAtlas guides you from initial document ingestion to production evaluation gates.
                  No copy-pasting. Pure understanding.
                </p>
                <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
                  <Link
                    href="/register"
                    className="inline-flex items-center gap-2 rounded-lg bg-[#181613] px-7 py-3.5 text-sm font-semibold text-white transition-all hover:bg-[#2E2B27] dark:bg-[#F6F4EF] dark:text-[#161513] dark:hover:bg-white shadow-sm"
                  >
                    <span>Start building free</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    href="/login"
                    className="rounded-lg border border-line-strong/40 bg-surface px-6 py-3.5 text-sm font-semibold text-ink transition-colors hover:bg-surface-muted dark:border-[#3E3B34] dark:bg-surface-card"
                  >
                    Sign in to workspace
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ================= FOOTER ================= */}
      <footer className="border-t border-line bg-surface py-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-3">
            <DevAtlasMark monochrome className="h-5 w-5 text-ink-muted" />
            <span className="font-semibold text-sm text-ink">DevAtlas</span>
            <span className="font-mono text-xs text-ink-muted">
              — Learn AI engineering by building.
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs text-ink-secondary">
            <Link href="/login" className="hover:text-ink transition-colors">
              Sign in
            </Link>
            <Link href="/register" className="hover:text-ink transition-colors">
              Create account
            </Link>
            <a href="#how-it-works" className="hover:text-ink transition-colors">
              How it works
            </a>
            <span className="font-mono text-ink-muted">
              © {new Date().getFullYear()} DevAtlas
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
