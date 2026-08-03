"use client";

import React, { useState } from "react";
import { Bot, User, Sparkles } from "lucide-react";

interface MentorTier {
  id: string;
  name: string;
  levelNum: number;
  cognitiveGoal: string;
  mentorPrompt: string;
  mentorQuote: string;
  codeSnippet?: string;
}

const MENTOR_TIERS: MentorTier[] = [
  {
    id: "nudge",
    name: "1. Nudge",
    levelNum: 1,
    cognitiveGoal: "Pointed Socratic Question",
    mentorPrompt: "How should I structure the document ingestion pipeline before indexing?",
    mentorQuote:
      "Before reaching for a vector database — what does 'relevant' mean for your users' queries? Try writing three example query-chunk pairs first to define your retrieval baseline.",
  },
  {
    id: "concept",
    name: "2. Concept",
    levelNum: 2,
    cognitiveGoal: "Architectural Mental Model",
    mentorPrompt: "Why not just embed the entire document at once without chunking?",
    mentorQuote:
      "Embedding models compress text into a fixed-dimension vector. If a document spans multiple topics, semantic specificity dissolves. Chunking with sliding overlap preserves local context.",
  },
  {
    id: "approach",
    name: "3. Approach",
    levelNum: 3,
    cognitiveGoal: "Concrete Implementation Strategy",
    mentorPrompt: "What is the concrete strategy for combining vector and keyword search?",
    mentorQuote:
      "1. Query dense embeddings from Qdrant/pgvector (top 20).\n2. Query SQLite BM25 lexical index (top 20).\n3. Compute Reciprocal Rank Fusion: score = Σ 1 / (60 + rank).\n4. Pass top-5 reranked chunks into LLM prompt context.",
    codeSnippet: `def compute_rrf(dense_ranks: dict[str, int], bm25_ranks: dict[str, int], k: int = 60):
    rrf_scores = {}
    for doc_id, rank in dense_ranks.items():
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
    for doc_id, rank in bm25_ranks.items():
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)`,
  },
  {
    id: "walkthrough",
    name: "4. Walkthrough",
    levelNum: 4,
    cognitiveGoal: "Worked Solution & Proof",
    mentorPrompt: "I am stuck on implementing the async FastAPI retriever endpoint.",
    mentorQuote:
      "Here is the complete async pipeline with pydantic schemas and error handling. Study why the token budget guard protects your inference budget, then write the eval check.",
    codeSnippet: `@app.post("/api/retrieve", response_model=RetrievalResponse)
async def retrieve_context(req: QueryRequest) -> RetrievalResponse:
    query_emb = await embedder.aembed(req.query)
    dense_hits = await vector_store.asearch(query_emb, top_k=20)
    sparse_hits = await bm25_index.asearch(req.query, top_k=20)
    top_chunks = rerank_rrf(dense_hits, sparse_hits, top_k=5)
    return RetrievalResponse(chunks=top_chunks, latency_ms=42)`,
  },
];

export function InteractiveMentorVisual() {
  const [activeTierId, setActiveTierId] = useState<string>("nudge");

  const current =
    MENTOR_TIERS.find((t) => t.id === activeTierId) ?? MENTOR_TIERS[0]!;

  return (
    <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
      {/* Wireframe Card */}
      <div className="relative overflow-hidden rounded-2xl border-2 border-line-strong/80 bg-surface p-6 shadow-raised dark:border-[#36342E] dark:bg-surface-card transition-all">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
            <span className="h-2.5 w-2.5 rounded-full border border-line-strong/60 bg-transparent dark:border-white/30" />
          </div>

          <div className="font-mono text-xs font-medium text-ink-muted">
            devatlas-mentor · hint-ladder
          </div>
        </div>

        {/* Tier Selector Buttons */}
        <div className="mt-5 flex flex-wrap gap-2">
          {MENTOR_TIERS.map((tier) => {
            const isActive = tier.id === activeTierId;
            return (
              <button
                key={tier.id}
                type="button"
                onClick={() => setActiveTierId(tier.id)}
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
                <span>{tier.name}</span>
              </button>
            );
          })}
        </div>

        {/* Metrics */}
        <div className="mt-7 grid grid-cols-2 gap-4">
          <div>
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
              ASSISTANCE LEVEL
            </span>
            <div className="mt-1 font-mono text-2xl sm:text-3xl font-extrabold text-[#F0653A] dark:text-[#FF8259]">
              {current.levelNum} of 4
            </div>
          </div>

          <div>
            <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
              PEDAGOGICAL METHOD
            </span>
            <div className="mt-1 font-mono text-base sm:text-lg font-bold text-ink truncate">
              {current.cognitiveGoal}
            </div>
          </div>
        </div>

        {/* Chat / Guidance thread */}
        <div className="mt-6 space-y-3 border-t border-line pt-4">
          {/* User query */}
          <div className="flex items-start gap-2.5 text-xs text-ink-secondary">
            <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-surface-muted border border-line text-ink">
              <User className="h-3 w-3" />
            </div>
            <p className="italic leading-relaxed">
              &ldquo;{current.mentorPrompt}&rdquo;
            </p>
          </div>

          {/* Mentor reply */}
          <div className="rounded-xl border border-line bg-surface-muted p-3.5 text-xs leading-relaxed text-ink dark:bg-[#24221E]">
            <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-[#F0653A] dark:text-[#FF8259] uppercase tracking-wider mb-1.5">
              <Bot className="h-3.5 w-3.5" />
              DevAtlas Senior Mentor
            </div>
            <p className="whitespace-pre-line font-medium text-ink">
              {current.mentorQuote}
            </p>

            {current.codeSnippet && (
              <pre className="mt-2.5 rounded-lg border border-line bg-surface p-2.5 font-mono text-[11px] text-ink overflow-x-auto">
                {current.codeSnippet}
              </pre>
            )}
          </div>
        </div>

        {/* Caption */}
        <div className="mt-4 flex items-center justify-between font-mono text-[11px] text-ink-muted">
          <span>↑ tap tiers to escalate help without spoiling code</span>
          <span className="flex items-center gap-1 text-[#F0653A] dark:text-[#FF8259] font-semibold">
            <Sparkles className="h-3 w-3" /> Promotes deep mastery
          </span>
        </div>
      </div>
    </div>
  );
}
