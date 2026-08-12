"use client";

import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";
import { FolderUp, BrainCircuit, BookOpenCheck, Rocket, ArrowRight, CheckCircle2 } from "lucide-react";

interface StepCard {
  number: string;
  title: string;
  description: string;
  icon: React.ElementType;
  tag: string;
}

const STEPS: StepCard[] = [
  {
    number: "01",
    title: "Upload & Ingest",
    description: "Provide a GitHub repository URL, PDF/Markdown documentation, or your raw software architecture idea.",
    icon: FolderUp,
    tag: "Source Ingestion",
  },
  {
    number: "02",
    title: "Understand & Map",
    description: "DevAtlas parses AST tokens, builds a dependency graph, and generates a personalized milestone roadmap.",
    icon: BrainCircuit,
    tag: "Knowledge Graph",
  },
  {
    number: "03",
    title: "Build with Mentor",
    description: "Write code in the cloud sandbox. When stuck, escalate through 4 progressive hint levels without spoiling answers.",
    icon: BookOpenCheck,
    tag: "Socratic Feedback",
  },
  {
    number: "04",
    title: "Evaluate & Ship",
    description: "Pass automated RAG Triad test suites, benchmark token latency budgets, and deploy production containers.",
    icon: Rocket,
    tag: "Production CI/CD",
  },
];

export function HowItWorksSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section id="how-it-works" ref={containerRef} className="relative border-t-2 border-line py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-accent-ink">
            ENGINEERING WORKFLOW
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-black tracking-[-0.03em] text-ink">
            Four steps from idea to production.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-ink-secondary">
            Every step is designed to eliminate passive browsing and instill senior-level architectural confidence.
          </p>
        </motion.div>

        {/* 4 Connected Cards Grid */}
        <div className="mt-16 relative">
          {/* Connecting Flow Line across desktop */}
          <div className="hidden lg:block absolute top-1/2 left-8 right-8 -translate-y-12 h-0.5 border-t-2 border-dashed border-line -z-0" />

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 relative z-10">
            {STEPS.map((step, idx) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, y: 25 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ duration: 0.5, delay: idx * 0.12, ease: "easeOut" }}
                  whileHover={{ y: -6 }}
                  className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border-2 border-ink bg-surface p-6 sticker-shadow-sm sticker-shadow-hover"
                >
                  {/* Top Step Header */}
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-2xl font-black text-ink-faint group-hover:text-accent-ink transition-colors">
                        {step.number}
                      </span>
                      <span className="rounded-full border-2 border-ink bg-accent-soft px-2.5 py-0.5 font-mono text-[10px] font-bold text-ink">
                        {step.tag}
                      </span>
                    </div>

                    <div className="mt-6 flex h-12 w-12 items-center justify-center rounded-2xl border-2 border-ink bg-accent text-ink transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
                      <Icon className="h-6 w-6" />
                    </div>

                    <h3 className="mt-5 text-lg font-bold text-ink">{step.title}</h3>

                    <p className="mt-2 text-xs leading-relaxed text-ink-secondary">{step.description}</p>
                  </div>

                  {/* Bottom Step Indicator */}
                  <div className="mt-6 flex items-center justify-between pt-4 border-t-2 border-line text-xs font-mono text-ink-muted">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                      <span>Step {idx + 1} of 4</span>
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-ink-faint transition-transform group-hover:translate-x-1 group-hover:text-ink" />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
