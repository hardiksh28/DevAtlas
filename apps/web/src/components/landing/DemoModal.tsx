"use client";

import React, { useState } from "react";
import {
  X,
  Play,
  FolderPlus,
  GitBranch,
  Bot,
  Rocket,
  CheckCircle2,
  ArrowRight,
  Terminal,
} from "lucide-react";
import Link from "next/link";

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const stepIcon = "h-5 w-5 text-ink";

const DEMO_STEPS = [
  {
    step: 1,
    title: "1. Create Your AI Project",
    icon: <FolderPlus className={stepIcon} />,
    summary: "Select your project archetype — from a multimodal RAG service to an autonomous agent fleet.",
    details: [
      "Select stack: FastAPI + pgvector / Qdrant + LangChain / LlamaIndex",
      "Attach custom GitHub repository & technical documentation",
      "DevAtlas parses docs and architectures your baseline structure",
    ],
    code: `# Initializing your DevAtlas project workspace
$ devatlas init --template rag-service --db qdrant
✓ Loaded project template (FastAPI + Qdrant + PyTorch)
✓ Ingested 14 documentation files into workspace memory
✓ Generated 6 engineering milestones tailored to your stack`,
  },
  {
    step: 2,
    title: "2. Generate Milestone Roadmap",
    icon: <GitBranch className={stepIcon} />,
    summary: "A battle-tested milestone roadmap tailored specifically to your project requirements.",
    details: [
      "Milestone 1: Data ingestion & semantic chunking strategies",
      "Milestone 2: Hybrid search & Reciprocal Rank Fusion",
      "Milestone 3: RAG Triad evaluation metrics & benchmark harness",
    ],
    code: `# Milestone Roadmap Generated
[✓] M1: Chunking & Token Window Design
[→] M2: Hybrid Search & RRF Algorithm (In Progress)
[ ] M3: Context Compression & Query Expansion
[ ] M4: Continuous Evaluation & Latency Budgets`,
  },
  {
    step: 3,
    title: "3. Build With AI Mentorship",
    icon: <Bot className={stepIcon} />,
    summary: "Write real code in your IDE while the mentor provides progressive, Socratic guidance.",
    details: [
      "Level 1 Nudge: Questions that stimulate problem breakdown",
      "Level 2 Concept: Architectural mental models and tradeoffs",
      "Level 3 Approach: Actionable strategy leaving the code to you",
    ],
    code: `>>> Mentor Hint (Level 2: Concept)
"Dense vectors struggle on exact keyword matches like SKUs or IDs.
Consider combining pgvector with BM25 keyword scoring."`,
  },
  {
    step: 4,
    title: "4. Review & Ship to Production",
    icon: <Rocket className={stepIcon} />,
    summary: "Senior engineer code review, CI/CD validation, and deployment with production observability.",
    details: [
      "Automated code review checking edge cases & security",
      "Evaluation test suite asserting >95% retrieval recall",
      "Containerized Docker deploy with latency monitoring",
    ],
    code: `✓ Automated Tests Passed: 12/12
✓ Precision@5: 0.96 | Recall@5: 0.98 | Latency: 42ms
✓ Container ready for deployment: docker pull registry.devatlas.ai/rag:v1.0`,
  },
];

export function DemoModal({ isOpen, onClose }: DemoModalProps) {
  const [activeStep, setActiveStep] = useState(0);

  if (!isOpen) return null;

  const current = DEMO_STEPS[activeStep] ?? DEMO_STEPS[0]!;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="anim-fade-in fixed inset-0 bg-ink/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal Dialog */}
      <div className="anim-pop-in relative z-10 w-full max-w-4xl overflow-hidden rounded-2xl border-2 border-ink bg-surface p-6 sticker-shadow">
        {/* Header */}
        <div className="flex items-center justify-between border-b-2 border-line pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border-2 border-ink bg-accent text-ink">
              <Play className="h-4 w-4 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold text-ink">DevAtlas Interactive Workflow Walkthrough</h3>
              <p className="text-xs text-ink-muted">
                Explore how engineers build and ship real AI projects from scratch
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink transition-colors"
            aria-label="Close demo walkthrough"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Step Tabs */}
        <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {DEMO_STEPS.map((s, idx) => (
            <button
              key={s.step}
              onClick={() => setActiveStep(idx)}
              className={`flex items-center gap-2 rounded-xl border-2 p-2.5 text-left text-xs transition-colors ${
                activeStep === idx
                  ? "border-ink bg-accent-soft text-ink"
                  : "border-line bg-surface-muted text-ink-muted hover:border-ink hover:text-ink"
              }`}
            >
              <div className="shrink-0">{s.icon}</div>
              <span className="truncate font-semibold">{s.title}</span>
            </button>
          ))}
        </div>

        {/* Main Content Showcase */}
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {/* Left Details */}
          <div className="space-y-4">
            <div>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-accent-ink">
                Phase 0{current.step} of 04
              </span>
              <h4 className="mt-1 text-lg font-bold text-ink">{current.title}</h4>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">{current.summary}</p>
            </div>

            <div className="space-y-2.5">
              {current.details.map((detail, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-ink-secondary">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-success mt-0.5" />
                  <span>{detail}</span>
                </div>
              ))}
            </div>

            <div className="pt-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-accent px-5 py-2.5 text-xs font-bold text-ink sticker-shadow-sm sticker-shadow-hover"
              >
                Start Building This Project Free
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Right Simulated Terminal */}
          <div className="rounded-xl border-2 border-ink bg-ink p-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/15 pb-2 text-[11px] text-white/50">
              <span className="flex items-center gap-1.5 text-white/70">
                <Terminal className="h-3.5 w-3.5" />
                terminal · devatlas
              </span>
              <span className="text-accent">Live Session</span>
            </div>
            <pre className="mt-3 whitespace-pre-wrap leading-relaxed text-white/80 text-[11px]">{current.code}</pre>
          </div>
        </div>

        {/* Footer Controls */}
        <div className="mt-6 flex items-center justify-between border-t-2 border-line pt-4">
          <div className="flex items-center gap-1.5">
            {DEMO_STEPS.map((_, idx) => (
              <span
                key={idx}
                className={`h-2 rounded-full transition-all ${
                  activeStep === idx ? "w-6 bg-accent" : "w-2 bg-line/40"
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
              disabled={activeStep === 0}
              className="rounded-full border-2 border-ink px-3 py-1.5 text-xs font-bold text-ink disabled:opacity-40 hover:bg-surface-muted"
            >
              Previous
            </button>
            <button
              onClick={() => setActiveStep((prev) => Math.min(DEMO_STEPS.length - 1, prev + 1))}
              disabled={activeStep === DEMO_STEPS.length - 1}
              className="rounded-full border-2 border-ink bg-ink px-3.5 py-1.5 text-xs font-bold text-white disabled:opacity-40 hover:bg-ink/90"
            >
              Next Step
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
