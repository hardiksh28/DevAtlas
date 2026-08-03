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
  Shield,
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
    <section className="relative overflow-hidden pt-12 pb-20 sm:pt-20 sm:pb-32 lg:pt-24 lg:pb-36">
      {/* Ambient Spotlight & Dot Grid Backdrop */}
      <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
        <div className="h-[600px] w-[800px] max-w-full rounded-full bg-gradient-to-tr from-blue-600/15 via-purple-600/10 to-cyan-500/10 blur-[130px]" />
        <div className="absolute inset-0 bg-matrix-grid opacity-60" />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.15fr_1fr] lg:items-center">
          {/* Left Column: Hero Typography & CTA */}
          <div className="max-w-2xl">
            {/* 1. One-Line Product Positioning Statement */}
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-zinc-900/80 px-3.5 py-1 text-xs font-medium text-zinc-300 backdrop-blur-md shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              <span className="text-zinc-400">DevAtlas</span>
              <span className="h-3 w-[1px] bg-white/[0.12]" />
              <span className="text-blue-400 font-semibold">
                The AI Engineering Workspace
              </span>
            </div>

            {/* 2. Hero Headline */}
            <h1 className="mt-6 text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold tracking-[-0.04em] leading-[1.06] text-white">
              Stop Watching Tutorials. <br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">
                Start Building Production Software.
              </span>
            </h1>

            {/* 3. Short Animated Sequence (Looping Hero Flow) */}
            <div className="mt-4 flex items-center gap-2 font-mono text-xs sm:text-sm text-zinc-400">
              <span className="text-zinc-500">Workflow:</span>
              <div className="relative inline-flex h-6 overflow-hidden items-center">
                <AnimatePresence mode="wait">
                  <motion.span
                    key={currentStepIndex}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.25 }}
                    className="inline-flex items-center gap-1.5 font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-md"
                  >
                    <Sparkles className="h-3 w-3" />
                    {ANIMATED_STEPS[currentStepIndex]}
                  </motion.span>
                </AnimatePresence>
              </div>
            </div>

            {/* 4. Short Description */}
            <p className="mt-5 text-base sm:text-lg leading-relaxed text-zinc-400 font-normal">
              Upload any GitHub repository, documentation, or project idea. DevAtlas becomes your
              AI mentor—creating a personalized roadmap, teaching every concept, reviewing your
              code like a senior engineer, and guiding you until your project is production-ready.
            </p>

            {/* 5. Primary & Secondary CTAs */}
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                href="/register"
                className="group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-7 py-3.5 text-sm font-semibold text-white shadow-glow-blue transition-all duration-300 hover:shadow-[0_0_30px_rgba(59,130,246,0.6)] hover:scale-[1.02] active:scale-[0.98]"
              >
                <span>Start Building Free</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>

              <button
                type="button"
                onClick={() => setDemoModalOpen(true)}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/[0.1] bg-zinc-900/80 px-6 py-3.5 text-sm font-semibold text-zinc-200 backdrop-blur-xl transition-all duration-300 hover:border-white/[0.2] hover:bg-zinc-800 hover:text-white active:scale-[0.98]"
              >
                <Play className="h-4 w-4 fill-zinc-200 text-zinc-200" />
                <span>Watch Interactive Demo</span>
              </button>
            </div>

            {/* 6. Subtle Trust Line */}
            <div className="mt-8 flex flex-wrap items-center gap-5 border-t border-white/[0.08] pt-5 text-xs text-zinc-500 font-mono">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>No credit card required</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>Built for developers</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>Works with your GitHub repositories</span>
              </div>
            </div>
          </div>

          {/* Right Column: Realistic High-Tech Workspace Illustration */}
          <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
            {/* Ambient Card Glow */}
            <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-blue-600/30 to-purple-600/30 opacity-40 blur-2xl transition duration-1000 group-hover:opacity-75" />

            {/* Main Realistic Workspace Card */}
            <div className="relative rounded-2xl border border-white/[0.1] bg-[#121215]/90 p-5 backdrop-blur-2xl shadow-overlay">
              {/* Window Bar */}
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-3.5">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-rose-500/80" />
                  <span className="h-3 w-3 rounded-full bg-amber-500/80" />
                  <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 font-mono text-xs text-zinc-400">
                    devatlas-workspace · rag-pipeline
                  </span>
                </div>
                <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-[11px] text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Grounded Mentor
                </div>
              </div>

              {/* Repo Ingestion Bar */}
              <div className="mt-4 rounded-xl border border-white/[0.06] bg-zinc-900/70 p-3">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-zinc-300">
                    <GitBranch className="h-4 w-4 text-blue-400" />
                    <span className="font-mono font-medium">github.com/langchain-ai/rag-pipeline</span>
                  </div>
                  <span className="font-mono text-[11px] text-purple-400">Indexed (142 files)</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                  <div className="h-full w-full rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-400" />
                </div>
              </div>

              {/* Roadmap Milestone Progression */}
              <div className="mt-4 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                  <span>LEARNING ROADMAP</span>
                  <span className="text-blue-400">Milestone 2 of 5</span>
                </div>

                {/* Milestone 1 (Completed) */}
                <div className="flex items-center justify-between rounded-lg border border-white/[0.04] bg-zinc-900/40 p-2.5 text-xs text-zinc-400">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span className="line-through text-zinc-500 font-mono">
                      01. Document AST Parser &amp; Chunking
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-zinc-500">100% Passed</span>
                </div>

                {/* Milestone 2 (Active) */}
                <div className="relative overflow-hidden rounded-lg border border-blue-500/40 bg-blue-950/20 p-3 text-xs shadow-glow-blue">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-500 text-[10px] font-bold text-white">
                        2
                      </span>
                      <span className="font-mono font-semibold text-white">
                        02. Hybrid Dense + BM25 Reciprocal Rank Fusion
                      </span>
                    </div>
                    <span className="rounded bg-blue-500/20 px-2 py-0.5 font-mono text-[10px] font-medium text-blue-300">
                      In Progress
                    </span>
                  </div>

                  {/* Socratic Mentor Hint Bubble */}
                  <div className="mt-3 rounded-lg border border-white/[0.08] bg-[#09090B]/90 p-3">
                    <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-purple-400">
                      <span>DevAtlas Mentor · Hint 1 of 4 (Nudge)</span>
                      <span className="text-zinc-500">Latency: 42ms</span>
                    </div>
                    <p className="mt-1.5 text-xs text-zinc-300 leading-relaxed font-sans">
                      &ldquo;Before you combine the dense cosine scores with BM25 keyword rankings,
                      why does raw score addition fail? Consider the score normalization scale.&rdquo;
                    </p>
                  </div>
                </div>

                {/* Milestone 3 (Locked) */}
                <div className="flex items-center justify-between rounded-lg border border-white/[0.04] bg-zinc-900/30 p-2.5 text-xs text-zinc-500">
                  <div className="flex items-center gap-2.5">
                    <span className="h-2 w-2 rounded-full border border-zinc-700 ml-1 mr-1" />
                    <span className="font-mono">03. Automated RAG Triad Evaluation Gates</span>
                  </div>
                  <span className="font-mono text-[10px] text-zinc-600">Upcoming</span>
                </div>
              </div>

              {/* Floating Live Indicator Footer */}
              <div className="mt-4 flex items-center justify-between border-t border-white/[0.06] pt-3 text-[11px] font-mono text-zinc-500">
                <div className="flex items-center gap-1.5">
                  <Terminal className="h-3.5 w-3.5 text-blue-400" />
                  <span>pytest evals/ --groundedness</span>
                </div>
                <span className="text-emerald-400 font-semibold">4 / 4 Assertions Verified</span>
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
