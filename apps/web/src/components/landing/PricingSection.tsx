"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { Check, ArrowRight, Sparkles } from "lucide-react";

export function PricingSection() {
  const [annual, setAnnual] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section
      id="pricing"
      ref={containerRef}
      className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32"
    >
      {/* Background Glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_50%,rgba(139,92,246,0.1),transparent_70%)]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-purple-400">
            TRANSPARENT PRICING
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            Simple pricing for serious engineers.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            Start building today. Upgrade when you need unlimited repositories, deeper AST reviews, and cloud sandboxes.
          </p>

          {/* Billing Toggle */}
          <div className="mt-8 inline-flex items-center gap-3 rounded-full border border-white/[0.08] bg-zinc-900/80 p-1 backdrop-blur-xl">
            <button
              type="button"
              onClick={() => setAnnual(false)}
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                !annual ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-white"
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-semibold transition-all ${
                annual
                  ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-glow-blue"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <span>Annual</span>
              <span className="rounded-full bg-emerald-400/20 px-2 py-0.5 text-[10px] text-emerald-300 font-mono">
                Save 20%
              </span>
            </button>
          </div>
        </motion.div>

        {/* Pricing Cards Grid */}
        <div className="mt-16 grid gap-8 lg:grid-cols-3 lg:items-center">
          {/* 1. Starter Plan */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.1 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border border-white/[0.08] bg-zinc-900/40 p-8 backdrop-blur-xl transition-all duration-300 hover:border-white/[0.2] hover:shadow-glass"
          >
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
                STARTER
              </div>
              <h3 className="mt-2 text-2xl font-bold text-white">₹399</h3>
              <p className="mt-1 font-mono text-xs text-zinc-500">
                per month {annual ? "(billed annually)" : ""}
              </p>
              <p className="mt-3 text-xs text-zinc-300 font-medium">
                Perfect for students and developers learning new technologies.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-zinc-300">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>5 Projects</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Personalized Roadmaps</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Socratic AI Mentor</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Pull Request Style Code Reviews</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Documentation Upload</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                  <span>Repository Analysis</span>
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-xl border border-white/[0.1] bg-zinc-800/80 py-3 text-center text-xs font-semibold text-white transition-colors hover:bg-zinc-700"
            >
              Get Started with Starter
            </Link>
          </motion.div>

          {/* 2. Pro Plan (Elevated & Recommended) */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.2 }}
            whileHover={{ y: -6, scale: 1.02 }}
            className="relative flex flex-col justify-between rounded-3xl border-2 border-blue-500/60 bg-gradient-to-b from-blue-950/40 via-zinc-900/90 to-zinc-900/90 p-8 sm:p-9 backdrop-blur-2xl shadow-glow-blue transition-all duration-300 hover:border-blue-400 lg:-my-4"
          >
            {/* Most Popular Badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-3.5 py-1 text-[11px] font-bold text-white shadow-md">
                <Sparkles className="h-3 w-3" />
                MOST POPULAR
              </span>
            </div>

            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-blue-400">
                PRO
              </div>
              <h3 className="mt-2 text-2xl font-bold text-white">₹999</h3>
              <p className="mt-1 font-mono text-xs text-zinc-400">
                per month {annual ? "(billed annually)" : ""}
              </p>
              <p className="mt-3 text-xs text-zinc-200 font-medium">
                For engineers building production systems and shipping software.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-zinc-200">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span className="font-semibold text-white">Unlimited Projects</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span className="font-semibold text-white">Unlimited AI Reviews</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Advanced Socratic Mentor &amp; AST Diffs</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Full Browser Workspace &amp; Cloud Sandbox</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Priority Review Queue</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-blue-400 shrink-0" />
                  <span>Automated Eval Gates &amp; Deployments</span>
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 py-3.5 text-center text-xs font-semibold text-white shadow-glow-blue transition-all hover:opacity-95 hover:shadow-[0_0_30px_rgba(59,130,246,0.6)]"
            >
              Start 14-Day Free Trial
            </Link>
          </motion.div>

          {/* 3. Enterprise Plan */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.3 }}
            whileHover={{ y: -4 }}
            className="flex flex-col justify-between rounded-3xl border border-white/[0.08] bg-zinc-900/40 p-8 backdrop-blur-xl transition-all duration-300 hover:border-white/[0.2] hover:shadow-glass"
          >
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
                ENTERPRISE
              </div>
              <h3 className="mt-2 text-2xl font-bold text-white">Custom</h3>
              <p className="mt-1 font-mono text-xs text-zinc-500">tailored to your engineering team</p>
              <p className="mt-3 text-xs text-zinc-300 font-medium">
                For organizations onboarding engineers on internal stacks and private APIs.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-zinc-300">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Self-Hosted &amp; Private VPC Ingestion</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Custom Internal Curriculum</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Dedicated GPU Inference Clusters</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>SAML SSO &amp; SOC2 Type II Compliance</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>Dedicated Solutions Architect &amp; SLA</span>
                </li>
              </ul>
            </div>

            <a
              href="mailto:sales@devatlas.ai"
              className="mt-8 block w-full rounded-xl border border-white/[0.1] bg-zinc-800/80 py-3 text-center text-xs font-semibold text-white transition-colors hover:bg-zinc-700"
            >
              Contact Sales
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
