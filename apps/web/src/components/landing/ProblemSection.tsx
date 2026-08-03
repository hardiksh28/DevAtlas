"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Video, Bot, Zap, ArrowRight, XCircle, CheckCircle2 } from "lucide-react";

export function ProblemSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section ref={containerRef} className="relative py-20 sm:py-28 lg:py-32">
      {/* Background Subtle Gradient */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900/50 via-transparent to-transparent" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-400">
            THE ROOT PROBLEM
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            Why tutorials fail. <br className="hidden sm:inline" />
            <span className="text-zinc-400">Why ChatGPT doesn&apos;t teach.</span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            Copying code from video instructors or generating full scripts with LLMs skips the exact mental friction that builds senior engineering skill.
          </p>
        </motion.div>

        {/* 3 Clear Comparison Columns */}
        <div className="mt-16 grid gap-6 lg:grid-cols-3">
          {/* Card 1: Video Tutorials */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.1 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border border-rose-500/20 bg-gradient-to-b from-rose-950/20 to-zinc-900/40 p-7 backdrop-blur-xl transition-all duration-300 hover:border-rose-500/30 hover:shadow-glass"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Video className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-rose-500/30 bg-rose-500/10 px-2.5 py-0.5 font-mono text-[10px] text-rose-400 font-semibold uppercase">
                  Tutorial Hell
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-white">Passive Video Courses</h3>
              <p className="mt-2 text-xs leading-relaxed text-zinc-400">
                Watching an instructor code creates an illusion of mastery. The moment you open an empty IDE, you have no framework for where to start.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-zinc-300">
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>Zero active recall or synthesis</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>Toy projects disconnected from production</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>Outdated dependencies and broken setups</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t border-rose-500/10 font-mono text-[11px] text-rose-400/80">
              Outcome: 90% abandonment rate
            </div>
          </motion.div>

          {/* Card 2: ChatGPT / Copilot */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.2 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border border-amber-500/20 bg-gradient-to-b from-amber-950/20 to-zinc-900/40 p-7 backdrop-blur-xl transition-all duration-300 hover:border-amber-500/30 hover:shadow-glass"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  <Bot className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 font-mono text-[10px] text-amber-400 font-semibold uppercase">
                  Answer Generators
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-white">ChatGPT &amp; Copilot Dumps</h3>
              <p className="mt-2 text-xs leading-relaxed text-zinc-400">
                LLMs give instant answers instead of teaching. By bypassing problem-solving, developers never understand the underlying architecture.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-zinc-300">
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>Hallucinates deprecated API methods</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>Dumps code without explaining trade-offs</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>Leaves you stuck when edge cases break in prod</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t border-amber-500/10 font-mono text-[11px] text-amber-400/80">
              Outcome: Fragile code, zero intuition
            </div>
          </motion.div>

          {/* Card 3: DevAtlas Standard */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.3 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border-2 border-blue-500/50 bg-gradient-to-b from-blue-950/40 via-zinc-900/80 to-zinc-900/80 p-7 backdrop-blur-xl shadow-glow-blue transition-all duration-300 hover:border-blue-400"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  <Zap className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-blue-500/40 bg-blue-500/20 px-2.5 py-0.5 font-mono text-[10px] text-blue-300 font-bold uppercase">
                  The DevAtlas Standard
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-white">Engineering-First Learning</h3>
              <p className="mt-2 text-xs leading-relaxed text-zinc-300">
                DevAtlas turns real repositories into structured milestones with progressive Socratic hints and senior PR code reviews.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-zinc-200">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Grounded on real repo AST &amp; official docs</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Socratic hints that guide without spoiling</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Automated test suites &amp; cloud deployment</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t border-blue-500/20 font-mono text-[11px] text-emerald-400">
              Outcome: Senior-level production confidence
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
