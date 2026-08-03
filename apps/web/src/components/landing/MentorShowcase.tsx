"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import {
  Bot,
  User,
  Sparkles,
  CheckCircle2,
  Code2,
  ArrowRight,
  HelpCircle,
  Brain,
  Lightbulb,
  GitPullRequest,
  Check,
  Rocket,
  ShieldCheck,
} from "lucide-react";

interface StepItem {
  id: number;
  name: string;
  badge: string;
  icon: React.ElementType;
  userPrompt: string;
  mentorReply: string;
  codeSnippet?: string;
  diffSnippet?: string;
  takeaway: string;
}

const STAGES: StepItem[] = [
  {
    id: 1,
    name: "01. Explain & Question",
    badge: "Architectural Intent",
    icon: HelpCircle,
    userPrompt: "How should I combine dense vector scores with BM25 sparse keyword rankings?",
    mentorReply:
      "Before writing any code: consider score scale differences. Cosine similarity ranges [0, 1] while BM25 outputs unbounded positive floats. If you add them directly, what happens to documents with high keyword matches?",
    takeaway: "The mentor prompts active reflection on score distributions rather than outputting code.",
  },
  {
    id: 2,
    name: "02. Hint 1: Intuition",
    badge: "Conceptual Nudge",
    icon: Lightbulb,
    userPrompt: "Why does min-max scaling fail when BM25 score distributions shift per query?",
    mentorReply:
      "Min-max scaling depends on the single highest score in a batch. One repetitive outlier document squashes all other candidate scores. How can we rank items based purely on position without score distortion?",
    takeaway: "Deepens foundational intuition around outlier sensitivity in information retrieval.",
  },
  {
    id: 3,
    name: "03. Hint 2: Mental Model",
    badge: "Algorithm Concept",
    icon: Brain,
    userPrompt: "What algorithm converts raw scores into rank-order position penalties?",
    mentorReply:
      "Reciprocal Rank Fusion (RRF). Instead of score addition, it assigns weight based purely on rank position: score = 1.0 / (k + rank), where k=60 balances top-rank sensitivity.",
    takeaway: "Introduces the industry-standard algorithm without writing the boilerplate for you.",
  },
  {
    id: 4,
    name: "04. Hint 3: Blueprint",
    badge: "Implementation Strategy",
    icon: Code2,
    userPrompt: "What is the concrete implementation strategy for RRF in Python?",
    mentorReply:
      "1. Collect top-20 candidate IDs from the dense index.\n2. Collect top-20 candidate IDs from the BM25 index.\n3. Initialize rrf_scores = {}\n4. For each (id, rank) in dense and bm25: rrf_scores[id] += 1.0 / (60 + rank)\n5. Sort descending and return top-k.",
    codeSnippet: `def compute_rrf(dense_ranks: dict[str, int], bm25_ranks: dict[str, int], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for doc_id, rank in dense_ranks.items():
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    for doc_id, rank in bm25_ranks.items():
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)`,
    takeaway: "Provides the structured algorithm blueprint to implement in your codebase.",
  },
  {
    id: 5,
    name: "05. Review & Improve",
    badge: "PR-Style AST Review",
    icon: GitPullRequest,
    userPrompt: "I implemented the hybrid endpoint. Can you review my code before I open a PR?",
    mentorReply:
      "Your core RRF logic is sound! However, notice that dense and sparse searches run sequentially with `await`, doubling latency. Wrap them in `asyncio.gather()` to run concurrent IO.",
    diffSnippet: `- dense_res = await vector_store.search(query, top_k=20)
- sparse_res = await bm25_index.search(query, top_k=20)
+ dense_res, sparse_res = await asyncio.gather(
+     vector_store.search(query, top_k=20),
+     bm25_index.search(query, top_k=20)
+ )`,
    takeaway: "Staff engineer AST diff review: cuts P95 latency from 95ms to 42ms.",
  },
  {
    id: 6,
    name: "06. Deploy & Fade",
    badge: "Autonomous Mastery",
    icon: Rocket,
    userPrompt: "Tests are passing with 100% assertions. Are we ready to ship?",
    mentorReply:
      "All eval assertions passed (Groundedness > 0.95, P95 < 50ms). You solved this milestone with solid architectural reasoning. The AI mentor steps back as your competence grows.",
    takeaway: "As your skill compounds, DevAtlas reduces assistance until you build independently.",
  },
];

export function MentorShowcase() {
  const [activeStageId, setActiveStageId] = useState<number>(1);
  const activeStage = STAGES.find((s) => s.id === activeStageId) ?? STAGES[0]!;
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section
      ref={containerRef}
      className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32"
    >
      {/* Background Glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_50%,rgba(139,92,246,0.1),transparent_60%)]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center mb-16"
        >
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-purple-400">
            SOCRATIC PEDAGOGY
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            An AI mentor that teaches, <br />
            <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-300 bg-clip-text text-transparent">
              then gets out of your way.
            </span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            DevAtlas guides you through progressive hints from mental models to PR-style AST reviews. As your engineering competence grows, the scaffolding gradually disappears.
          </p>
        </motion.div>

        <div className="grid gap-10 lg:grid-cols-[1fr_1.3fr] lg:items-center">
          {/* Left Column: Stage Selector List */}
          <div className="space-y-2.5">
            {STAGES.map((stage) => {
              const isSelected = stage.id === activeStageId;
              const Icon = stage.icon;
              return (
                <button
                  key={stage.id}
                  type="button"
                  onClick={() => setActiveStageId(stage.id)}
                  className={`group relative flex w-full items-center justify-between rounded-2xl border p-4 text-left transition-all duration-300 ${
                    isSelected
                      ? "border-purple-500/50 bg-purple-950/25 shadow-glow-purple"
                      : "border-white/[0.06] bg-zinc-900/40 hover:border-white/[0.15] hover:bg-zinc-900/70"
                  }`}
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-xl transition-colors ${
                        isSelected
                          ? "bg-purple-500 text-white"
                          : "bg-zinc-800 text-zinc-400 group-hover:text-white"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white">{stage.name}</p>
                      <p className="text-xs text-zinc-400">{stage.badge}</p>
                    </div>
                  </div>
                  <ArrowRight
                    className={`h-4 w-4 transition-transform ${
                      isSelected ? "text-purple-400 translate-x-1" : "text-zinc-600 group-hover:text-zinc-400"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          {/* Right Column: Live Animated Conversation Mockup */}
          <div className="relative">
            <div className="rounded-3xl border border-white/[0.1] bg-[#121215]/95 p-6 backdrop-blur-2xl shadow-overlay">
              {/* Window Bar */}
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-rose-500/80" />
                  <span className="h-3 w-3 rounded-full bg-amber-500/80" />
                  <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
                  <span className="ml-2 font-mono text-xs text-zinc-300 font-semibold">
                    DevAtlas Senior AI Mentor
                  </span>
                </div>
                <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2.5 py-0.5 font-mono text-[10px] text-purple-300 font-semibold">
                  {activeStage.badge}
                </span>
              </div>

              {/* Chat Thread with Smooth Framer Motion Transition */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeStage.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25 }}
                  className="mt-6 space-y-4"
                >
                  {/* User Message */}
                  <div className="flex items-start gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-zinc-800 text-zinc-300">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="rounded-2xl rounded-tl-none border border-white/[0.06] bg-zinc-900/80 p-3.5 text-xs sm:text-sm text-zinc-200">
                      {activeStage.userPrompt}
                    </div>
                  </div>

                  {/* Mentor Response */}
                  <div className="flex items-start gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-purple-500/30 bg-purple-500/20 text-purple-300">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex-1 rounded-2xl rounded-tl-none border border-purple-500/30 bg-[#16151E] p-4 text-xs sm:text-sm text-zinc-200">
                      <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-purple-400 uppercase tracking-wider mb-2">
                        <Sparkles className="h-3 w-3" />
                        Socratic Guidance
                      </div>
                      <p className="whitespace-pre-line leading-relaxed text-zinc-200 font-sans">
                        {activeStage.mentorReply}
                      </p>

                      {/* Code Snippet if present */}
                      {activeStage.codeSnippet && (
                        <pre className="mt-3 overflow-x-auto rounded-xl border border-white/[0.08] bg-black/60 p-3 font-mono text-[11px] text-zinc-300">
                          {activeStage.codeSnippet}
                        </pre>
                      )}

                      {/* Diff Snippet if present */}
                      {activeStage.diffSnippet && (
                        <div className="mt-3 overflow-hidden rounded-xl border border-white/[0.08] bg-black/70 p-3 font-mono text-[11px]">
                          {activeStage.diffSnippet.split("\n").map((line, idx) => (
                            <div
                              key={idx}
                              className={
                                line.startsWith("+")
                                  ? "text-emerald-400 bg-emerald-950/40 px-1 rounded"
                                  : line.startsWith("-")
                                  ? "text-rose-400 bg-rose-950/40 px-1 rounded"
                                  : "text-zinc-400"
                              }
                            >
                              {line}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Bottom Pedagogical Takeaway */}
              <div className="mt-6 flex items-center justify-between border-t border-white/[0.06] pt-3 text-[11px] font-mono text-zinc-500">
                <span className="text-zinc-400">{activeStage.takeaway}</span>
                <span className="text-emerald-400 font-semibold shrink-0 ml-2">Active Recall</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
