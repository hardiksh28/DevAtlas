"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  Map,
  Bot,
  GitPullRequest,
  Rocket,
  Sparkles,
} from "lucide-react";

export function FeatureBentoGrid() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section id="features" ref={containerRef} className="relative border-t-2 border-line py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-accent-ink">
            ENGINEERED FOR MASTERY
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-black tracking-[-0.03em] text-ink">
            Built for developers who want to understand, <br className="hidden sm:inline" />
            <span className="highlight-mark">not just copy and paste.</span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-ink-secondary">
            DevAtlas replaces disconnected videos with a unified workspace that bridges the gap between reading documentation and shipping software.
          </p>
        </motion.div>

        {/* Bento Grid */}
        <div className="mt-16 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Card 1: Roadmaps (Large Span 2 Cols on LG) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.1 }}
            whileHover={{ y: -4 }}
            className="group relative overflow-hidden rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover lg:col-span-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-ink border-2 border-ink transition-transform group-hover:scale-110 group-hover:rotate-3">
                <Map className="h-6 w-6" />
              </div>
              <span className="rounded-full border-2 border-ink bg-accent-soft px-3 py-1 font-mono text-xs font-bold text-ink">
                MILESTONE DECOMPOSITION
              </span>
            </div>

            <h3 className="mt-6 text-2xl font-bold text-ink">
              Personalized engineering roadmaps generated from your own project.
            </h3>
            <p className="mt-2 text-sm text-ink-secondary leading-relaxed max-w-xl">
              Paste any GitHub repository, official documentation, or technical spec. DevAtlas breaks down complex architectures into sequential, bite-sized milestones tailored to what you want to build.
            </p>

            {/* Visual Mini Preview */}
            <div className="mt-6 grid grid-cols-3 gap-3">
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">Input</p>
                <p className="mt-1 text-xs font-bold text-ink font-mono">Any GitHub Repo</p>
              </div>
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">Accuracy</p>
                <p className="mt-1 text-xs font-bold text-success-ink font-mono">100% Grounded</p>
              </div>
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">Progression</p>
                <p className="mt-1 text-xs font-bold text-accent-ink font-mono">Milestone Gates</p>
              </div>
            </div>
          </motion.div>

          {/* Card 2: AI Mentor (Span 1) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.2 }}
            whileHover={{ y: -4 }}
            className="group relative overflow-hidden rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-ink border-2 border-ink transition-transform group-hover:scale-110 group-hover:rotate-3">
                <Bot className="h-6 w-6" />
              </div>
              <span className="rounded-full border-2 border-ink bg-accent-soft px-3 py-1 font-mono text-xs font-bold text-ink">
                SOCRATIC GUIDANCE
              </span>
            </div>

            <h3 className="mt-6 text-xl font-bold text-ink">
              An AI Mentor that teaches instead of solving.
            </h3>
            <p className="mt-2 text-sm text-ink-secondary leading-relaxed">
              When you hit a wall, DevAtlas gives you progressive hints—from high-level intuition to concrete strategies—without ever spoiling the code.
            </p>

            <div className="mt-6 rounded-xl border-2 border-line bg-surface-muted p-3 font-mono text-xs text-ink-secondary">
              Hint 1: Check score normalization ranges
            </div>
          </motion.div>

          {/* Card 3: Code Review (Span 1) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.3 }}
            whileHover={{ y: -4 }}
            className="group relative overflow-hidden rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-ink border-2 border-ink transition-transform group-hover:scale-110 group-hover:rotate-3">
                <GitPullRequest className="h-6 w-6" />
              </div>
              <span className="rounded-full border-2 border-ink bg-accent-soft px-3 py-1 font-mono text-xs font-bold text-ink">
                CODE QUALITY
              </span>
            </div>

            <h3 className="mt-6 text-xl font-bold text-ink">
              Pull Request style reviews that explain why your code should improve.
            </h3>
            <p className="mt-2 text-sm text-ink-secondary leading-relaxed">
              Receive AST-level feedback on concurrency bottlenecks, memory allocations, and edge cases with inline diff comparisons.
            </p>

            <div className="mt-6 flex items-center gap-2 text-xs font-mono font-bold text-accent-ink">
              <Sparkles className="h-4 w-4" />
              <span>Senior Staff-level code reviews</span>
            </div>
          </motion.div>

          {/* Card 4: Production Deployment (Large Span 2 Cols on LG) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.4 }}
            whileHover={{ y: -4 }}
            className="group relative overflow-hidden rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover lg:col-span-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-ink border-2 border-ink transition-transform group-hover:scale-110 group-hover:rotate-3">
                <Rocket className="h-6 w-6" />
              </div>
              <span className="rounded-full border-2 border-ink bg-accent-soft px-3 py-1 font-mono text-xs font-bold text-ink">
                PRODUCTION READY
              </span>
            </div>

            <h3 className="mt-6 text-2xl font-bold text-ink">
              Automated evaluation test suites and 1-click cloud deployment.
            </h3>
            <p className="mt-2 text-sm text-ink-secondary leading-relaxed max-w-xl">
              Verify your system with automated test assertions for latency budgets, hallucination rates, and groundedness before deploying live cloud endpoints.
            </p>

            {/* Metrics Bar */}
            <div className="mt-6 grid grid-cols-3 gap-3">
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">Assertions</p>
                <p className="mt-1 text-xs font-bold text-success-ink font-mono">100% Automated</p>
              </div>
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">P95 Latency</p>
                <p className="mt-1 text-xs font-bold text-accent-ink font-mono">&lt;50ms Response</p>
              </div>
              <div className="rounded-xl border-2 border-line bg-surface-muted p-3">
                <p className="font-mono text-[10px] text-ink-muted uppercase">Deployment</p>
                <p className="mt-1 text-xs font-bold text-accent-ink font-mono">Live HTTPS URL</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
