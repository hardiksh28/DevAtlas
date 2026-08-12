"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Video, Bot, Zap, XCircle, CheckCircle2 } from "lucide-react";

export function ProblemSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section ref={containerRef} className="relative py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-accent-ink">
            THE ROOT PROBLEM
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-black tracking-[-0.03em] text-ink">
            Why tutorials fail. <br className="hidden sm:inline" />
            <span className="text-ink-muted">Why ChatGPT doesn&apos;t teach.</span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-ink-secondary">
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
            className="flex flex-col justify-between rounded-3xl border-2 border-rose-300 bg-rose-50 p-7"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-rose-500 border-2 border-rose-300">
                  <Video className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-rose-300 bg-white px-2.5 py-0.5 font-mono text-[10px] text-rose-600 font-bold uppercase">
                  Tutorial Hell
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-ink">Passive Video Courses</h3>
              <p className="mt-2 text-xs leading-relaxed text-ink-secondary">
                Watching an instructor code creates an illusion of mastery. The moment you open an empty IDE, you have no framework for where to start.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-ink-secondary">
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                  <span>Zero active recall or synthesis</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                  <span>Toy projects disconnected from production</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                  <span>Outdated dependencies and broken setups</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t border-rose-300 font-mono text-[11px] text-rose-600">
              Outcome: 90% abandonment rate
            </div>
          </motion.div>

          {/* Card 2: ChatGPT / Copilot */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.2 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border-2 border-amber-300 bg-amber-50 p-7"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-amber-600 border-2 border-amber-300">
                  <Bot className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-amber-300 bg-white px-2.5 py-0.5 font-mono text-[10px] text-amber-700 font-bold uppercase">
                  Answer Generators
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-ink">ChatGPT &amp; Copilot Dumps</h3>
              <p className="mt-2 text-xs leading-relaxed text-ink-secondary">
                LLMs give instant answers instead of teaching. By bypassing problem-solving, developers never understand the underlying architecture.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-ink-secondary">
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>Hallucinates deprecated API methods</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>Dumps code without explaining trade-offs</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>Leaves you stuck when edge cases break in prod</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t border-amber-300 font-mono text-[11px] text-amber-700">
              Outcome: Fragile code, zero intuition
            </div>
          </motion.div>

          {/* Card 3: DevAtlas Standard */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.3 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border-2 border-ink bg-accent-soft p-7 sticker-shadow"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-ink border-2 border-ink">
                  <Zap className="h-5 w-5" />
                </div>
                <span className="rounded-full border-2 border-ink bg-accent px-2.5 py-0.5 font-mono text-[10px] text-ink font-bold uppercase">
                  The DevAtlas Standard
                </span>
              </div>

              <h3 className="mt-6 text-xl font-bold text-ink">Engineering-First Learning</h3>
              <p className="mt-2 text-xs leading-relaxed text-ink-secondary">
                DevAtlas turns real repositories into structured milestones with progressive Socratic hints and senior PR code reviews.
              </p>

              <ul className="mt-6 space-y-3 text-xs text-ink-secondary">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success-ink shrink-0 mt-0.5" />
                  <span>Grounded on real repo AST &amp; official docs</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success-ink shrink-0 mt-0.5" />
                  <span>Socratic hints that guide without spoiling</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success-ink shrink-0 mt-0.5" />
                  <span>Automated test suites &amp; cloud deployment</span>
                </li>
              </ul>
            </div>

            <div className="mt-6 pt-4 border-t-2 border-ink font-mono text-[11px] font-bold text-ink">
              Outcome: Senior-level production confidence
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
