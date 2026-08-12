"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { Check, Sparkles } from "lucide-react";

export function PricingSection() {
  const [annual, setAnnual] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section id="pricing" ref={containerRef} className="relative border-t-2 border-line py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-accent-ink">
            TRANSPARENT PRICING
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-black tracking-[-0.03em] text-ink">
            Simple pricing for serious engineers.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-ink-secondary">
            Start building today. Upgrade when you need unlimited repositories, deeper AST reviews, and cloud sandboxes.
          </p>

          {/* Billing Toggle */}
          <div className="mt-8 inline-flex items-center gap-1 rounded-full border-2 border-ink bg-surface p-1">
            <button
              type="button"
              onClick={() => setAnnual(false)}
              className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
                !annual ? "bg-ink text-white" : "text-ink-muted hover:text-ink"
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold transition-all ${
                annual ? "bg-accent text-ink" : "text-ink-muted hover:text-ink"
              }`}
            >
              <span>Annual</span>
              <span className="rounded-full bg-ink px-2 py-0.5 text-[10px] text-accent font-mono">
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
            className="flex flex-col justify-between rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover"
          >
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-ink-muted">
                STARTER
              </div>
              <h3 className="mt-2 text-2xl font-black text-ink">₹399</h3>
              <p className="mt-1 font-mono text-xs text-ink-faint">
                per month {annual ? "(billed annually)" : ""}
              </p>
              <p className="mt-3 text-xs text-ink-secondary font-medium">
                Perfect for students and developers learning new technologies.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-ink-secondary">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>5 Projects</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Personalized Roadmaps</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Socratic AI Mentor</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Pull Request Style Code Reviews</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Documentation Upload</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Repository Analysis</span>
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-full border-2 border-ink bg-surface py-3 text-center text-xs font-bold text-ink transition-colors hover:bg-surface-muted"
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
            className="relative flex flex-col justify-between rounded-3xl border-2 border-ink bg-accent-soft p-8 sm:p-9 sticker-shadow lg:-my-4"
          >
            {/* Most Popular Badge */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
              <span className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-accent px-3.5 py-1 text-[11px] font-bold text-ink">
                <Sparkles className="h-3 w-3" />
                MOST POPULAR
              </span>
            </div>

            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-accent-ink">
                PRO
              </div>
              <h3 className="mt-2 text-2xl font-black text-ink">₹999</h3>
              <p className="mt-1 font-mono text-xs text-ink-muted">
                per month {annual ? "(billed annually)" : ""}
              </p>
              <p className="mt-3 text-xs text-ink font-medium">
                For engineers building production systems and shipping software.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-ink">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span className="font-bold">Unlimited Projects</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span className="font-bold">Unlimited AI Reviews</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span>Advanced Socratic Mentor &amp; AST Diffs</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span>Full Browser Workspace &amp; Cloud Sandbox</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span>Priority Review Queue</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-ink shrink-0" />
                  <span>Automated Eval Gates &amp; Deployments</span>
                </li>
              </ul>
            </div>

            <Link
              href="/register"
              className="mt-8 block w-full rounded-full border-2 border-ink bg-ink py-3.5 text-center text-xs font-bold text-white transition-opacity hover:opacity-90"
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
            className="flex flex-col justify-between rounded-3xl border-2 border-ink bg-surface p-8 sticker-shadow-sm sticker-shadow-hover"
          >
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-ink-muted">
                ENTERPRISE
              </div>
              <h3 className="mt-2 text-2xl font-black text-ink">Custom</h3>
              <p className="mt-1 font-mono text-xs text-ink-faint">tailored to your engineering team</p>
              <p className="mt-3 text-xs text-ink-secondary font-medium">
                For organizations onboarding engineers on internal stacks and private APIs.
              </p>

              <ul className="mt-8 space-y-3.5 text-xs text-ink-secondary">
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Self-Hosted &amp; Private VPC Ingestion</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Custom Internal Curriculum</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Dedicated GPU Inference Clusters</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>SAML SSO &amp; SOC2 Type II Compliance</span>
                </li>
                <li className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 text-success shrink-0" />
                  <span>Dedicated Solutions Architect &amp; SLA</span>
                </li>
              </ul>
            </div>

            <a
              href="mailto:sales@devatlas.ai"
              className="mt-8 block w-full rounded-full border-2 border-ink bg-surface py-3 text-center text-xs font-bold text-ink transition-colors hover:bg-surface-muted"
            >
              Contact Sales
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
