"use client";

import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw, ChevronRight, ChevronLeft, Database, Layers, Sparkles, CheckCircle2, Bot } from "lucide-react";

interface PipelineStep {
  stage: number;
  label: string;
  name: string;
  denseScore: string;
  sparseScore: string;
  rrfScore: string;
  status: string;
  explanation: string;
  isComplete?: boolean;
}

const PIPELINE_NODES = [
  { id: 0, label: "Ingest", name: "Doc Loader" },
  { id: 1, label: "Chunk", name: "Semantic Overlap" },
  { id: 2, label: "Embed", name: "Vector + BM25" },
  { id: 3, label: "Fusion", name: "RRF Reranker" },
  { id: 4, label: "Eval", name: "RAG Triad Gate" },
];

const STEPS: PipelineStep[] = [
  {
    stage: 0,
    label: "Ingestion",
    name: "Markdown & PDF Ingestion",
    denseScore: "—",
    sparseScore: "—",
    rrfScore: "—",
    status: "Parsing raw documents into clean AST tokens",
    explanation: "Extracting sections, headings, and codeblocks from source repos.",
  },
  {
    stage: 1,
    label: "Chunking",
    name: "Semantic Boundary Split (512 tokens)",
    denseScore: "—",
    sparseScore: "—",
    rrfScore: "—",
    status: "Created 48 chunks with 64-token sliding overlap",
    explanation: "Preserving context boundaries so vector embeddings don't truncate mid-sentence.",
  },
  {
    stage: 2,
    label: "Retrieval",
    name: "Dense Semantic + BM25 Lexical",
    denseScore: "0.94 Cosine",
    sparseScore: "14.2 BM25",
    rrfScore: "0.0162 RRF",
    status: "Retrieved top-10 candidate chunks from Qdrant & SQLite BM25",
    explanation: "Dense captures conceptual intent; BM25 catches exact symbol names & error codes.",
  },
  {
    stage: 3,
    label: "Fusion",
    name: "Reciprocal Rank Fusion (k=60)",
    denseScore: "0.97 Cosine",
    sparseScore: "18.6 BM25",
    rrfScore: "0.0328 RRF",
    status: "Fused top-3 grounded chunks into synthesis prompt",
    explanation: "Eliminating hallucination by passing only high-confidence citations to LLM.",
  },
  {
    stage: 4,
    label: "Evaluation",
    name: "RAG Triad Quality Gate",
    denseScore: "0.99 Relevance",
    sparseScore: "0.00 Hallucination",
    rrfScore: "42ms Latency",
    status: "Passed 4/4 automated eval tests · Ready to ship! 🎉",
    explanation: "Groundedness: 1.0, Answer Relevance: 0.98, Context Precision: 0.96.",
    isComplete: true,
  },
];

export function HeroAlgorithmVisual() {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(3); // Default step 3: Fusion
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const step = STEPS[currentStepIndex] ?? STEPS[0]!;

  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev >= STEPS.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(timer);
  }, [isPlaying]);

  const handlePrev = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setIsPlaying(false);
    setCurrentStepIndex((prev) => Math.min(STEPS.length - 1, prev + 1));
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const togglePlay = () => {
    if (currentStepIndex >= STEPS.length - 1) {
      setCurrentStepIndex(0);
    }
    setIsPlaying((prev) => !prev);
  };

  return (
    <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
      {/* Live Badge (Orange Pill on top-left) */}
      <div className="absolute -top-3 left-4 z-20">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-[#F0653A] px-2.5 py-0.5 text-[11px] font-bold tracking-wider text-white shadow-sm">
          <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
          LIVE PIPELINE
        </span>
      </div>

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
            retrieval-service · hybrid-rag
          </div>
        </div>

        {/* Pipeline Nodes Row */}
        <div className="mt-8">
          <div className="grid grid-cols-5 gap-1.5 sm:gap-2">
            {PIPELINE_NODES.map((node, idx) => {
              const isActive = idx === step.stage;
              const isPast = idx < step.stage;

              return (
                <div key={idx} className="flex flex-col items-center">
                  {/* Step Card */}
                  <button
                    type="button"
                    onClick={() => {
                      setIsPlaying(false);
                      setCurrentStepIndex(idx);
                    }}
                    className={`flex h-12 w-full flex-col items-center justify-center rounded-lg border-2 text-center transition-all duration-300 ${
                      isActive
                        ? step.isComplete
                          ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:border-emerald-400 dark:bg-emerald-950/40 dark:text-emerald-300 scale-105 shadow-sm"
                          : "border-[#F0653A] bg-[#FEF3EC] text-[#E05327] dark:border-[#F0653A] dark:bg-[#2C1E18] dark:text-[#FF8259] scale-105 shadow-sm"
                        : isPast
                        ? "border-line-strong/40 bg-surface-muted text-ink-secondary dark:border-[#3E3B34] dark:bg-[#24221E]"
                        : "border-line bg-surface text-ink-muted opacity-60 dark:border-[#2E2C27] dark:bg-[#1C1B18]"
                    }`}
                  >
                    <span className="font-mono text-[10px] font-bold">0{idx + 1}</span>
                    <span className="truncate px-1 text-[11px] font-semibold">{node.label}</span>
                  </button>

                  {/* Active Marker Arrow */}
                  <div className="mt-2 flex h-6 flex-col items-center justify-start text-xs font-bold font-mono">
                    {isActive && (
                      <div className="flex flex-col items-center text-[#F0653A] dark:text-[#FF8259] animate-bounce">
                        <span className="text-[10px] leading-none">▲</span>
                        <span className="text-[10px] font-extrabold uppercase tracking-tight">Active</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Active Step Details Card */}
          <div className="mt-3 rounded-xl border border-line bg-surface-muted p-3.5 dark:bg-[#24221E]">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-ink">
                {step.name}
              </span>
              <span className="font-mono text-[11px] text-[#F0653A] dark:text-[#FF8259] font-semibold">
                Stage {step.stage + 1} of 5
              </span>
            </div>

            <p className="mt-1.5 text-xs text-ink-secondary leading-relaxed font-medium">
              {step.status}
            </p>

            {/* Metrics Chips */}
            <div className="mt-3 flex flex-wrap gap-2 font-mono text-[10px]">
              <span className="rounded border border-line bg-surface px-2 py-0.5 text-ink-muted">
                Dense: <strong className="text-ink">{step.denseScore}</strong>
              </span>
              <span className="rounded border border-line bg-surface px-2 py-0.5 text-ink-muted">
                BM25: <strong className="text-ink">{step.sparseScore}</strong>
              </span>
              <span className="rounded border border-line bg-surface px-2 py-0.5 text-ink-muted">
                RRF Rank: <strong className="text-[#F0653A] dark:text-[#FF8259]">{step.rrfScore}</strong>
              </span>
            </div>
          </div>

          {/* Explanation Text */}
          <p className="mt-3 text-center text-xs text-ink-muted leading-relaxed">
            {step.explanation}
          </p>

          {/* Stepper Controls */}
          <div className="mt-5 flex items-center justify-between border-t border-line pt-3 text-xs text-ink-muted">
            <div className="flex items-center gap-1 font-mono text-[11px]">
              <span>Milestone {currentStepIndex + 1} / {STEPS.length}</span>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentStepIndex === 0}
                aria-label="Previous step"
                className="flex h-7 w-7 items-center justify-center rounded border border-line bg-surface text-ink disabled:opacity-30 hover:bg-surface-muted transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={togglePlay}
                aria-label={isPlaying ? "Pause pipeline" : "Play pipeline"}
                className="flex h-7 items-center gap-1.5 rounded border border-line bg-surface px-2.5 text-xs font-medium text-ink hover:bg-surface-muted transition-colors"
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-3 w-3 fill-current" />
                    <span>Pause</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3 fill-current ml-0.5" />
                    <span>Run Pipeline</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleNext}
                disabled={currentStepIndex === STEPS.length - 1}
                aria-label="Next step"
                className="flex h-7 w-7 items-center justify-center rounded border border-line bg-surface text-ink disabled:opacity-30 hover:bg-surface-muted transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={handleReset}
                aria-label="Reset pipeline"
                className="flex h-7 w-7 items-center justify-center rounded border border-line bg-surface text-ink hover:bg-surface-muted transition-colors"
                title="Reset"
              >
                <RotateCcw className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
