"use client";

import React, { useState } from "react";
import { CheckCircle2, Terminal, Bot } from "lucide-react";

export function HeroCosmicVisual() {
  const [activeTab, setActiveTab] = useState<"code" | "roadmap" | "mentor">("code");

  return (
    <div className="relative mx-auto flex w-full max-w-[580px] items-center justify-center lg:max-w-none">
      {/* Main Workstation Card */}
      <div className="relative z-10 w-full overflow-hidden rounded-2xl border border-white/10 bg-[#0d0f14] p-4 shadow-xl">
        {/* Window Topbar */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <span className="h-3 w-3 rounded-full bg-white/15" />
              <span className="h-3 w-3 rounded-full bg-white/15" />
              <span className="h-3 w-3 rounded-full bg-white/15" />
            </div>
            <span className="ml-2 font-mono text-xs text-slate-500">
              devatlas-workspace · rag-service
            </span>
          </div>

          {/* Interactive view tabs */}
          <div className="flex items-center rounded-lg border border-white/10 bg-white/[0.03] p-0.5 text-xs">
            {(["code", "roadmap", "mentor"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                  activeTab === tab
                    ? "bg-white/10 text-white"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {tab === "code" ? "Code" : tab === "roadmap" ? "Milestones" : "Mentor Feedback"}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Card Content */}
        <div className="mt-3 min-h-[220px]">
          {activeTab === "code" && (
            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <span className="flex items-center gap-1.5 text-slate-400">
                  <Terminal className="h-3.5 w-3.5" />
                  pipeline.py
                </span>
                <span className="text-emerald-400/80 font-semibold flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
                  Tests Passing (4/4)
                </span>
              </div>

              {/* Code Snippet Box */}
              <div className="rounded-lg border border-white/10 bg-black/30 p-3.5 text-slate-300 leading-relaxed">
                <p>
                  <span className="text-indigo-300">async def</span>{" "}
                  <span className="text-slate-100">hybrid_retrieval</span>
                  <span className="text-slate-500">(query:</span>{" "}
                  <span className="text-slate-400">str</span>
                  <span className="text-slate-500">, top_k:</span>{" "}
                  <span className="text-slate-400">int = 5</span>
                  <span className="text-slate-500">):</span>
                </p>
                <p className="pl-4 text-slate-600">
                  # Embed query with semantic vector model
                </p>
                <p className="pl-4">
                  q_emb = <span className="text-indigo-300">await</span> embeddings.
                  <span className="text-slate-100">aembed_query</span>(query)
                </p>
                <p className="pl-4 text-slate-600">
                  # Combine dense vectors + reciprocal rank fusion
                </p>
                <p className="pl-4">
                  ranked_docs = <span className="text-indigo-300">await</span> qdrant.
                  <span className="text-slate-100">search_fusion</span>(q_emb, k=top_k)
                </p>
                <p className="pl-4">
                  <span className="text-indigo-300">return</span> ranked_docs
                </p>
              </div>
            </div>
          )}

          {activeTab === "roadmap" && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-slate-500">Project Progress</span>
                <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-0.5 font-mono text-[11px] font-semibold text-slate-400">
                  Milestone 3 of 6
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2.5 rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-slate-400">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400/80 shrink-0" />
                  <span className="line-through text-slate-500">1. Define chunking & metadata schema</span>
                </div>
                <div className="flex items-center gap-2.5 rounded-lg border border-indigo-500/30 bg-indigo-500/[0.06] p-2.5 text-white">
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-500 text-[10px] font-bold text-white">
                    2
                  </span>
                  <span className="font-medium">2. Implement reciprocal rank fusion (Active)</span>
                </div>
                <div className="flex items-center gap-2.5 rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-slate-500">
                  <span className="flex h-4 w-4 items-center justify-center rounded-full border border-slate-600 text-[10px]">
                    3
                  </span>
                  <span>3. Build automated RAG Triad evaluation pipeline</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "mentor" && (
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-300 font-semibold">
                <Bot className="h-4 w-4 text-indigo-400" />
                Senior AI Mentor Feedback
              </div>
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3 text-slate-300 leading-relaxed">
                <p className="font-mono text-[11px] text-slate-500 font-semibold uppercase tracking-wider mb-1">
                  Level 1 Hint · Guided Question
                </p>
                <p className="text-slate-300">
                  &ldquo;Your reciprocal rank fusion weighting is clean! Notice how keyword search handles exact model numbers better than semantic embeddings alone. How will you calibrate the alpha parameter for your domain?&rdquo;
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer ribbon */}
        <div className="mt-3 flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] px-3.5 py-2">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400/80" />
            <span className="font-mono text-[11px] text-slate-400">
              Flow State: <strong className="text-slate-200 font-semibold">Active</strong>
            </span>
          </div>
          <span className="text-[11px] font-medium text-slate-500">
            20k+ Engineers in Flow
          </span>
        </div>
      </div>
    </div>
  );
}
