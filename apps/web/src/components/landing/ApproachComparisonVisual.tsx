"use client";

import React, { useState } from "react";

interface Approach {
  id: string;
  name: string;
  latency: string;
  latencyColor: string;
  hallucination: string;
  hallucinationColor: string;
  tokens: string;
  tokenPercent: number;
  barColor: string;
  explanation: string;
}

const APPROACHES: Approach[] = [
  {
    id: "naive",
    name: "Naive Prompting",
    latency: "850ms",
    latencyColor: "text-rose-500 dark:text-rose-400",
    hallucination: "28.4%",
    hallucinationColor: "text-rose-500 dark:text-rose-400",
    tokens: "32,000 tokens ($0.48 / req)",
    tokenPercent: 100,
    barColor: "bg-rose-500",
    explanation: "Dumping raw context into one large prompt — high cost, slow TTFT, and frequent ungrounded hallucinations.",
  },
  {
    id: "basic-vector",
    name: "Basic Vector Search",
    latency: "120ms",
    latencyColor: "text-amber-500 dark:text-amber-400",
    hallucination: "8.2%",
    hallucinationColor: "text-amber-500 dark:text-amber-400",
    tokens: "4,000 tokens ($0.06 / req)",
    tokenPercent: 35,
    barColor: "bg-amber-500",
    explanation: "Pure semantic cosine search — good for broad concepts, but fails on exact symbols, model IDs, and syntax errors.",
  },
  {
    id: "hybrid-rag",
    name: "Hybrid RAG + Reranking",
    latency: "42ms",
    latencyColor: "text-emerald-600 dark:text-emerald-400",
    hallucination: "<0.5%",
    hallucinationColor: "text-emerald-600 dark:text-emerald-400",
    tokens: "1,200 tokens ($0.01 / req)",
    tokenPercent: 12,
    barColor: "bg-emerald-500",
    explanation: "Dense vectors + BM25 sparse index + Reciprocal Rank Fusion — exact lexical precision with deep semantic grounding.",
  },
];

export function ApproachComparisonVisual() {
  const [activeApproachId, setActiveApproachId] = useState<string>("hybrid-rag");

  const current =
    APPROACHES.find((a) => a.id === activeApproachId) ?? APPROACHES[2]!;

  return (
    <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
      {/* Main Wireframe Card */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-line-strong/80 bg-surface p-6 shadow-raised dark:border-[#36342E] dark:bg-surface-card transition-all">
        {/* Card Header: Window dots + problem title */}
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
          </div>

          <div className="font-mono text-xs font-medium text-ink-muted">
            rag-architecture · approaches
          </div>
        </div>

        {/* Approach Selector Buttons */}
        <div className="mt-5 flex flex-wrap gap-2">
          {APPROACHES.map((app) => {
            const isActive = app.id === activeApproachId;
            return (
              <button
                key={app.id}
                type="button"
                onClick={() => setActiveApproachId(app.id)}
                className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
                  isActive
                    ? "border-2 border-line-strong bg-[#FEF3EC] text-[#E05327] dark:border-[#F0653A] dark:bg-[#2C1E18] dark:text-[#FF8259] shadow-sm"
                    : "border border-line bg-surface-muted text-ink-secondary hover:text-ink hover:bg-surface"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    isActive ? "bg-[#F0653A]" : "bg-ink-muted"
                  }`}
                />
                <span>{app.name}</span>
              </button>
            );
          })}
        </div>

        {/* Complexity Big Metrics */}
        <div className="mt-7 grid grid-cols-2 gap-4">
          <div>
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
              P95 LATENCY
            </span>
            <div className={`mt-1 font-mono text-2xl sm:text-3xl font-extrabold ${current.latencyColor}`}>
              {current.latency}
            </div>
          </div>

          <div>
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
              HALLUCINATION RATE
            </span>
            <div className={`mt-1 font-mono text-2xl sm:text-3xl font-extrabold ${current.hallucinationColor}`}>
              {current.hallucination}
            </div>
          </div>
        </div>

        {/* Work to solve / Token cost bar */}
        <div className="mt-6 border-t border-line pt-4">
          <div className="flex items-center justify-between font-mono text-xs">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
              CONTEXT WORKLOAD · PER QUERY
            </span>
            <span className="font-bold text-ink">{current.tokens}</span>
          </div>

          {/* Animated Bar */}
          <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-surface-muted border border-line">
            <div
              className={`h-full rounded-full transition-all duration-500 ${current.barColor}`}
              style={{ width: `${current.tokenPercent}%` }}
            />
          </div>
        </div>

        {/* Explanation & Caption */}
        <div className="mt-5 border-t border-line pt-3">
          <p className="text-sm font-medium text-ink leading-relaxed">
            {current.explanation}
          </p>
          <p className="mt-2 font-mono text-[11px] text-ink-muted">
            ↑ tap an architecture to leap — hallucination drops and latency falls.
          </p>
        </div>
      </div>
    </div>
  );
}
