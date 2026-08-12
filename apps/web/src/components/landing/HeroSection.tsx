"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Play,
  GitBranch,
  CheckCircle2,
  Terminal,
  Sparkles,
} from "lucide-react";
import { DemoModal } from "@/components/landing/DemoModal";

const ANIMATED_STEPS = [
  "Upload Repository",
  "Analyze Architecture",
  "Generate Roadmap",
  "Learn Every Concept",
  "Write Real Code",
  "Senior AI Reviews",
  "Ship Production Software",
];

export function HeroSection() {
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % ANIMATED_STEPS.length);
    }, 2400);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative overflow-hidden pt-12 pb-20 sm:pt-16 sm:pb-32 lg:pt-20 lg:pb-36">
      {/* Dot Grid Backdrop */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-dot-grid" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.15fr_1fr] lg:items-center">
          {/* Left Column: Hero Typography & CTA */}
          <div className="max-w-2xl">
            {/* 1. One-Line Product Positioning Statement */}
            <div className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-surface px-3.5 py-1.5 text-xs font-bold text-ink shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-accent" />
              <span className="text-ink-secondary">DevAtlas</span>
              <span className="h-3 w-[1px] bg-line" />
              <span className="text-accent-ink font-bold">The AI Engineering Workspace</span>
            </div>

            {/* 2. Hero Headline */}
            <h1 className="mt-7 text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-black tracking-[-0.03em] leading-[1.08] text-ink">
              <span className="highlight-mark">Stop Watching Tutorials.</span>
              <br />
              Start Building Production Software.
            </h1>

            {/* 3. Short Animated Sequence (Looping Hero Flow) */}
            <div className="mt-5 flex items-center gap-2 font-mono text-xs sm:text-sm text-ink-muted">
              <span className="text-ink-faint">Workflow:</span>
              <div className="relative inline-flex h-6 overflow-hidden items-center">
                <AnimatePresence mode="wait">
                  <motion.span
                    key={currentStepIndex}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25 }}
                    className="inline-flex items-center gap-1.5 font-bold text-accent-ink bg-accent-soft border border-accent px-2 py-0.5 rounded-md"
                  >
                    <Sparkles className="h-3 w-3" />
                    {ANIMATED_STEPS[currentStepIndex]}
                  </motion.span>
                </AnimatePresence>
              </div>
            </div>

            {/* 4. Short Description */}
            <p className="mt-5 text-base sm:text-lg leading-relaxed text-ink-secondary font-normal">
              Upload any GitHub repository, documentation, or project idea. DevAtlas becomes your
              AI mentor—creating a personalized roadmap, teaching every concept, reviewing your
              code like a senior engineer, and guiding you until your project is production-ready.
            </p>

            {/* 5. Primary & Secondary CTAs */}
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                href="/register"
                className="group inline-flex items-center justify-center gap-2 rounded-full border-2 border-ink bg-accent px-7 py-3.5 text-sm font-bold text-ink sticker-shadow sticker-shadow-hover"
              >
                <span>Start Building Free</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>

              <button
                type="button"
                onClick={() => setDemoModalOpen(true)}
                className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-ink bg-ink px-6 py-3.5 text-sm font-bold text-white transition-transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <Play className="h-4 w-4 fill-white text-white" />
                <span>Watch Interactive Demo</span>
              </button>
            </div>

            {/* 6. Subtle Trust Line */}
            <div className="mt-8 flex flex-wrap items-center gap-5 border-t-2 border-line pt-5 text-xs text-ink-muted font-mono">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                <span>Built for developers</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                <span>Works with your GitHub repositories</span>
              </div>
            </div>
          </div>

          {/* Right Column: Realistic High-Tech Workspace Illustration */}
          <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
            {/* Main Realistic Workspace Card */}
            <div className="relative rounded-2xl border-2 border-ink bg-surface p-5 sticker-shadow">
              {/* Window Bar */}
              <div className="flex items-center justify-between border-b-2 border-line pb-3.5">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-danger" />
                  <span className="h-3 w-3 rounded-full bg-accent" />
                  <span className="h-3 w-3 rounded-full bg-success" />
                  <span className="ml-2 font-mono text-xs text-ink-muted">
                    devatlas-workspace · rag-pipeline
                  </span>
                </div>
                <div className="flex items-center gap-1.5 rounded-full border border-success bg-success-soft px-2.5 py-0.5 font-mono text-[11px] text-success-ink">
                  <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
                  Grounded Mentor
                </div>
              </div>

              {/* Repo Ingestion Bar */}
              <div className="mt-4 rounded-xl border-2 border-line bg-surface-muted p-3">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-ink-secondary">
                    <GitBranch className="h-4 w-4 text-ink" />
                    <span className="font-mono font-medium">github.com/langchain-ai/rag-pipeline</span>
                  </div>
                  <span className="font-mono text-[11px] font-bold text-accent-ink">Indexed (142 files)</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-line/20">
                  <div className="h-full w-full rounded-full bg-accent" />
                </div>
              </div>

              {/* Roadmap Milestone Progression */}
              <div className="mt-4 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-mono text-ink-muted">
                  <span>LEARNING ROADMAP</span>
                  <span className="font-bold text-accent-ink">Milestone 2 of 5</span>
                </div>

                {/* Milestone 1 (Completed) */}
                <div className="flex items-center justify-between rounded-lg border-2 border-line bg-surface-muted p-2.5 text-xs text-ink-muted">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                    <span className="line-through text-ink-faint font-mono">
                      01. Document AST Parser &amp; Chunking
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-ink-faint">100% Passed</span>
                </div>

                {/* Milestone 2 (Active) */}
                <div className="relative overflow-hidden rounded-lg border-2 border-ink bg-accent-soft p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-ink text-[10px] font-bold text-white">
                        2
                      </span>
                      <span className="font-mono font-bold text-ink">
                        02. Hybrid Dense + BM25 Reciprocal Rank Fusion
                      </span>
                    </div>
                    <span className="rounded-full border border-ink bg-accent px-2 py-0.5 font-mono text-[10px] font-bold text-ink">
                      In Progress
                    </span>
                  </div>

                  {/* Socratic Mentor Hint Bubble */}
                  <div className="mt-3 rounded-lg border-2 border-line bg-surface p-3">
                    <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-ink-muted">
                      <span>DevAtlas Mentor · Hint 1 of 4 (Nudge)</span>
                      <span className="text-ink-faint">Latency: 42ms</span>
                    </div>
                    <p className="mt-1.5 text-xs text-ink-secondary leading-relaxed font-sans">
                      &ldquo;Before you combine the dense cosine scores with BM25 keyword rankings,
                      why does raw score addition fail? Consider the score normalization scale.&rdquo;
                    </p>
                  </div>
                </div>

                {/* Milestone 3 (Locked) */}
                <div className="flex items-center justify-between rounded-lg border-2 border-line bg-surface-muted p-2.5 text-xs text-ink-faint">
                  <div className="flex items-center gap-2.5">
                    <span className="h-2 w-2 rounded-full border border-ink-faint ml-1 mr-1" />
                    <span className="font-mono">03. Automated RAG Triad Evaluation Gates</span>
                  </div>
                  <span className="font-mono text-[10px] text-ink-faint">Upcoming</span>
                </div>
              </div>

              {/* Floating Live Indicator Footer */}
              <div className="mt-4 flex items-center justify-between border-t-2 border-line pt-3 text-[11px] font-mono text-ink-muted">
                <div className="flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5 text-ink" />
                  <span>pytest evals/ --groundedness</span>
                </div>
                <span className="text-success-ink font-bold">4 / 4 Assertions Verified</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Demo Walkthrough Modal */}
      <DemoModal isOpen={demoModalOpen} onClose={() => setDemoModalOpen(false)} />
    </section>
  );
}
