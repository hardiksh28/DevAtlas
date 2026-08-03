"use client";

import React, { useState } from "react";
import {
  HelpCircle,
  Lightbulb,
  Compass,
  BookOpenCheck,
  Bot,
  User,
  CheckCircle,
} from "lucide-react";

interface HintLevel {
  id: number;
  level: string;
  badge: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  mentorMessage: string;
  codePreview?: string;
  keyTakeaway: string;
}

const iconClass = "h-5 w-5 text-indigo-400";

const HINT_LEVELS: HintLevel[] = [
  {
    id: 1,
    level: "Level 1",
    badge: "Socratic Question",
    title: "The Nudge",
    description: "A pointed question that redirects your attention without spoiling the answer.",
    icon: <HelpCircle className={iconClass} />,
    mentorMessage:
      "Before jumping into vector indexing — what does 'relevance' mean for your users' domain? Are they searching for exact part numbers or conceptual queries? What happens when an exact keyword doesn't appear in dense vector space?",
    keyTakeaway: "Forces you to clarify requirements before locking into an architecture.",
  },
  {
    id: 2,
    level: "Level 2",
    badge: "Mental Model",
    title: "The Concept",
    description: "The underlying principle explained — just enough theory to reason with, no more.",
    icon: <Lightbulb className={iconClass} />,
    mentorMessage:
      "Dense embeddings understand semantics ('car' ≈ 'automobile'), but struggle with exact hashes or model codes. Sparse search (BM25) excels at exact matches. Hybrid Search with Reciprocal Rank Fusion (RRF) combines ranked lists using: RRF_score(d) = Σ 1 / (k + rank(d)).",
    keyTakeaway: "Builds permanent architectural knowledge rather than copy-pasting.",
  },
  {
    id: 3,
    level: "Level 3",
    badge: "Action Plan",
    title: "The Approach",
    description: "A concrete strategy for this exact problem, still leaving the implementation to you.",
    icon: <Compass className={iconClass} />,
    mentorMessage:
      "1. Query pgvector for semantic top 20 docs.\n2. Query BM25 index on document chunks for lexical top 20 docs.\n3. Compute RRF scores with constant k=60 to merge and deduplicate.\n4. Return the top 5 reranked chunks to the LLM context window.",
    codePreview: `# Strategy outline for your implementation:
async def hybrid_retrieve(query: str, k: int = 60) -> List[Document]:
    semantic_results = await vector_store.similarity_search(query, limit=20)
    keyword_results  = await bm25_index.search(query, limit=20)
    return reciprocal_rank_fusion(semantic_results, keyword_results, k=k)`,
    keyTakeaway: "Gives clear scaffolding so you can write the actual code with confidence.",
  },
  {
    id: 4,
    level: "Level 4",
    badge: "Worked Pattern",
    title: "The Walkthrough",
    description: "A worked example when you are truly stuck, followed by a challenge to test mastery.",
    icon: <BookOpenCheck className={iconClass} />,
    mentorMessage:
      "Here is a complete, working implementation of Reciprocal Rank Fusion with async gathering. Review how the score accumulation prevents duplicate documents from dominating the context window.",
    codePreview: `async def rrf(query: str, top_k: int = 5, k: int = 60):
    dense_task = vector_store.asimilarity_search(query, k=20)
    sparse_task = bm25_store.asearch(query, k=20)
    dense_hits, sparse_hits = await asyncio.gather(dense_task, sparse_task)

    scores = collections.defaultdict(float)
    for rank, doc in enumerate(dense_hits):
        scores[doc.id] += 1.0 / (k + rank + 1)
    for rank, doc in enumerate(sparse_hits):
        scores[doc.id] += 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]`,
    keyTakeaway: "Provides complete closure when stuck, followed by a recall challenge.",
  },
];

export function InteractiveHintPlayground() {
  const [activeLevel, setActiveLevel] = useState<number>(1);
  const currentHint = HINT_LEVELS.find((h) => h.id === activeLevel) ?? HINT_LEVELS[0]!;

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr] lg:items-center">
      {/* Left: 4 Clickable Levels */}
      <div className="space-y-3">
        {HINT_LEVELS.map((hint) => {
          const isActive = hint.id === activeLevel;
          return (
            <button
              key={hint.id}
              onClick={() => setActiveLevel(hint.id)}
              className={`w-full text-left transition-colors duration-200 rounded-xl p-4 border flex items-start gap-4 ${
                isActive
                  ? "border-indigo-500/50 bg-indigo-500/[0.06]"
                  : "border-white/10 bg-white/[0.02] hover:border-white/20"
              }`}
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03]">
                {hint.icon}
              </div>

              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-500">
                      {hint.level}
                    </span>
                    <span className="text-sm font-semibold text-white">
                      {hint.title}
                    </span>
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    {hint.badge}
                  </span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-slate-400">
                  {hint.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Right: Live Mentor Simulation Card */}
      <div className="relative rounded-2xl border border-white/10 bg-[#0d0f14] p-5 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-indigo-500/25 bg-indigo-500/10 text-indigo-400">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs font-semibold text-white flex items-center gap-1.5">
                DevAtlas AI Mentor
                <span className="flex h-1.5 w-1.5 rounded-full bg-emerald-400/80" />
              </p>
              <p className="text-[10px] text-slate-500 font-mono">
                Project: Financial RAG Service · Milestone 2
              </p>
            </div>
          </div>

          <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 font-mono text-[11px] font-semibold text-slate-400">
            {currentHint.level}: {currentHint.title}
          </span>
        </div>

        {/* Chat Thread */}
        <div className="mt-4 space-y-3.5">
          {/* User query */}
          <div className="flex gap-2.5 items-start">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/[0.04] text-slate-400 text-xs border border-white/10">
              <User className="h-3.5 w-3.5" />
            </div>
            <div className="rounded-xl rounded-tl-none bg-white/[0.03] border border-white/10 p-3 text-xs text-slate-300">
              &ldquo;My retrieval fails when users search for specific ticker symbols like $NVDA. How should I solve this?&rdquo;
            </div>
          </div>

          {/* Mentor response */}
          <div className="flex gap-2.5 items-start">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-indigo-500/25 bg-indigo-500/10 text-indigo-400 text-xs">
              <Bot className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 space-y-3 rounded-xl rounded-tl-none border border-indigo-500/25 bg-indigo-500/[0.05] p-3.5 text-xs text-slate-200">
              <p className="whitespace-pre-line leading-relaxed font-sans">
                {currentHint.mentorMessage}
              </p>

              {currentHint.codePreview && (
                <div className="mt-2 rounded-lg border border-white/10 bg-black/30 p-3 font-mono text-[11px] text-slate-300 overflow-x-auto">
                  <pre className="text-slate-300">{currentHint.codePreview}</pre>
                </div>
              )}

              <div className="flex items-center gap-2 pt-2 border-t border-white/10 text-[11px] text-slate-400">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 shrink-0" />
                <span>
                  <strong className="text-slate-300">Pedagogical Goal:</strong> {currentHint.keyTakeaway}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Live Prompt Status */}
        <div className="mt-4 flex items-center justify-between rounded-lg bg-white/[0.02] border border-white/10 px-3 py-2 text-[11px] text-slate-500">
          <span>Click hint tabs above to see pedagogical escalation</span>
          <span className="text-slate-400 font-semibold flex items-center gap-1">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-400/80" /> Never writes code for you blindly
          </span>
        </div>
      </div>
    </div>
  );
}
