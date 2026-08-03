"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  GitBranch,
  Search,
  Network,
  BookOpen,
  Map,
  Code2,
  Bot,
  CheckCircle2,
  Rocket,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Terminal,
  Layers,
  ArrowRight,
  FileCode2,
  Folder,
  ChevronRight,
  Activity,
  Globe,
  ExternalLink,
} from "lucide-react";

interface StepConfig {
  id: number;
  label: string;
  shortTitle: string;
  icon: React.ElementType;
  durationMs: number;
}

const STEPS: StepConfig[] = [
  { id: 0, label: "Paste GitHub Repo", shortTitle: "01. Ingestion", icon: GitBranch, durationMs: 2500 },
  { id: 1, label: "Repository Tree", shortTitle: "02. Structure", icon: Folder, durationMs: 2200 },
  { id: 2, label: "AST Analysis", shortTitle: "03. Parsing", icon: Search, durationMs: 2200 },
  { id: 3, label: "Dependency Graph", shortTitle: "04. Graph", icon: Network, durationMs: 2400 },
  { id: 4, label: "Docs Synthesized", shortTitle: "05. Docs", icon: BookOpen, durationMs: 2200 },
  { id: 5, label: "Roadmap Generated", shortTitle: "06. Roadmap", icon: Map, durationMs: 2400 },
  { id: 6, label: "Lesson Loaded", shortTitle: "07. Lesson", icon: Layers, durationMs: 2200 },
  { id: 7, label: "Live Code Editor", shortTitle: "08. Code", icon: Code2, durationMs: 2800 },
  { id: 8, label: "AI Socratic Review", shortTitle: "09. Mentor", icon: Bot, durationMs: 2600 },
  { id: 9, label: "Milestone Passed", shortTitle: "10. Verified", icon: CheckCircle2, durationMs: 2200 },
  { id: 10, label: "Cloud Deployment", shortTitle: "11. Shipped", icon: Rocket, durationMs: 3000 },
];

export function InteractiveProductDemo() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const prefersReducedMotion = useReducedMotion();
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-advance loop through steps
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }

    const duration = STEPS[currentStep]?.durationMs ?? 2500;
    timerRef.current = setTimeout(() => {
      setCurrentStep((prev) => (prev + 1) % STEPS.length);
    }, duration);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [currentStep, isPlaying]);

  const goToStep = (index: number) => {
    setCurrentStep(index);
  };

  const togglePlay = () => {
    setIsPlaying((prev) => !prev);
  };

  const reset = () => {
    setCurrentStep(0);
    setIsPlaying(true);
  };

  return (
    <section className="relative overflow-hidden border-t border-white/[0.08] bg-[#09090B] py-16 sm:py-24 lg:py-28">
      {/* Ambient Radial Spotlight */}
      <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
        <div className="h-[550px] w-[900px] max-w-full rounded-full bg-gradient-to-tr from-blue-600/15 via-purple-600/15 to-cyan-500/10 blur-[140px]" />
        <div className="absolute inset-0 bg-matrix-grid opacity-40" />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-blue-400 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5" />
            <span>INTERACTIVE PRODUCT WALKTHROUGH</span>
          </div>

          <h2 className="mt-4 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            See DevAtlas in action. <br />
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">
              From repository to production in seconds.
            </span>
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            Watch how DevAtlas ingests any GitHub codebase, extracts an architectural roadmap, mentors your implementation, and ships live software.
          </p>
        </div>

        {/* Timeline Control Bar (Scrubbable Tabs) */}
        <div className="mt-12">
          {/* Scrollable on small screens */}
          <div className="flex items-center justify-between gap-2 overflow-x-auto pb-2 scrollbar-none">
            {STEPS.map((step, idx) => {
              const Icon = step.icon;
              const isActive = currentStep === idx;
              const isPast = currentStep > idx;

              return (
                <button
                  key={step.id}
                  type="button"
                  onClick={() => goToStep(idx)}
                  className={`group relative flex shrink-0 items-center gap-2 rounded-xl border px-3 py-2 text-xs font-mono transition-all duration-300 ${
                    isActive
                      ? "border-blue-500/60 bg-blue-950/40 text-white shadow-glow-blue"
                      : isPast
                      ? "border-white/[0.08] bg-zinc-900/60 text-zinc-300 hover:border-white/[0.2]"
                      : "border-white/[0.04] bg-zinc-900/30 text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  <Icon
                    className={`h-3.5 w-3.5 transition-transform group-hover:scale-110 ${
                      isActive ? "text-blue-400" : isPast ? "text-emerald-400" : "text-zinc-500"
                    }`}
                  />
                  <span>{step.shortTitle}</span>

                  {/* Active Step Progress Pill indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="activePill"
                      className="absolute inset-0 -z-10 rounded-xl bg-blue-600/10 border border-blue-500/40"
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Timeline Linear Progress Line */}
          <div className="mt-3 relative h-1 w-full overflow-hidden rounded-full bg-zinc-800/80">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-400"
              initial={{ width: "0%" }}
              animate={{ width: `${((currentStep + 1) / STEPS.length) * 100}%` }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Main Interactive Demo Sandbox Stage */}
        <div className="mt-8 relative rounded-3xl border border-white/[0.1] bg-[#101014]/95 p-4 sm:p-7 backdrop-blur-2xl shadow-overlay">
          {/* Top Stage Control Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-rose-500/80" />
              <span className="h-3 w-3 rounded-full bg-amber-500/80" />
              <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
              <span className="ml-2 font-mono text-xs text-zinc-400">
                devatlas-runtime · step {currentStep + 1} of {STEPS.length}
              </span>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={togglePlay}
                className="flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-zinc-900 px-3 py-1.5 font-mono text-xs text-zinc-300 hover:border-white/[0.2] hover:bg-zinc-800 hover:text-white transition-colors"
                aria-label={isPlaying ? "Pause demo" : "Play demo"}
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-3.5 w-3.5 text-amber-400" />
                    <span>Pause</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5 fill-emerald-400 text-emerald-400" />
                    <span>Resume</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={reset}
                className="flex items-center gap-1 rounded-lg border border-white/[0.08] bg-zinc-900 p-1.5 text-zinc-400 hover:text-white transition-colors"
                title="Restart from beginning"
                aria-label="Restart demo"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>

              <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 font-mono text-[11px] text-blue-300">
                <Activity className="h-3 w-3 animate-pulse text-blue-400" />
                <span>{STEPS[currentStep]?.label}</span>
              </div>
            </div>
          </div>

          {/* Dynamic Step Canvas Viewport */}
          <div className="relative mt-6 min-h-[440px] sm:min-h-[480px] flex items-center justify-center overflow-hidden rounded-2xl border border-white/[0.06] bg-[#0A0A0D]/90 p-4 sm:p-8">
            <AnimatePresence mode="wait">
              {/* STEP 0: Paste GitHub URL */}
              {currentStep === 0 && (
                <motion.div
                  key="step0"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl text-center"
                >
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/20 text-blue-400 border border-blue-500/30 shadow-glow-blue">
                    <GitBranch className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-xl sm:text-2xl font-bold text-white">
                    1. Connect Your Codebase
                  </h3>
                  <p className="mt-1 text-xs sm:text-sm text-zinc-400">
                    Paste any public or private GitHub repository URL
                  </p>

                  <div className="mt-6 flex items-center gap-2 rounded-xl border border-blue-500/40 bg-zinc-900/90 p-2 shadow-glow-blue">
                    <GitBranch className="h-5 w-5 text-blue-400 ml-2" />
                    <span className="flex-1 text-left font-mono text-xs sm:text-sm text-white overflow-hidden text-ellipsis whitespace-nowrap">
                      https://github.com/langchain-ai/rag-pipeline
                      <span className="animate-pulse text-blue-400 font-bold ml-0.5">|</span>
                    </span>
                    <span className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white">
                      Ingest
                    </span>
                  </div>
                </motion.div>
              )}

              {/* STEP 1: Repository Tree Expands */}
              {currentStep === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-lg rounded-2xl border border-white/[0.08] bg-zinc-900/80 p-6 font-mono text-xs"
                >
                  <div className="flex items-center justify-between text-zinc-400 pb-3 border-b border-white/[0.08]">
                    <div className="flex items-center gap-2 text-zinc-200">
                      <Folder className="h-4 w-4 text-blue-400" />
                      <span className="font-bold">rag-pipeline/</span>
                    </div>
                    <span className="text-emerald-400 text-[11px]">142 files found</span>
                  </div>

                  <motion.div
                    className="mt-4 space-y-2 text-zinc-300"
                    initial="hidden"
                    animate="visible"
                    variants={{
                      visible: { transition: { staggerChildren: 0.1 } },
                    }}
                  >
                    {[
                      { icon: Folder, name: "src/pipeline/hybrid_retrieval.py", tag: "Core Logic" },
                      { icon: Folder, name: "src/vector/qdrant_client.py", tag: "Store" },
                      { icon: Folder, name: "evals/test_rag_triad.py", tag: "Eval Suite" },
                      { icon: FileCode2, name: "pyproject.toml", tag: "Python 3.12" },
                      { icon: FileCode2, name: "Dockerfile", tag: "Container" },
                    ].map((f, i) => (
                      <motion.div
                        key={i}
                        variants={{
                          hidden: { opacity: 0, x: -10 },
                          visible: { opacity: 1, x: 0 },
                        }}
                        className="flex items-center justify-between rounded-lg bg-black/40 p-2.5"
                      >
                        <div className="flex items-center gap-2">
                          <f.icon className="h-3.5 w-3.5 text-blue-400" />
                          <span>{f.name}</span>
                        </div>
                        <span className="text-[10px] text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded">
                          {f.tag}
                        </span>
                      </motion.div>
                    ))}
                  </motion.div>
                </motion.div>
              )}

              {/* STEP 2: AST Analysis */}
              {currentStep === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl text-center"
                >
                  <div className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-500/20 text-purple-400 border border-purple-500/40 shadow-glow-purple">
                    <Search className="h-8 w-8 animate-pulse" />
                  </div>
                  <h3 className="mt-4 text-xl sm:text-2xl font-bold text-white">
                    3. Parsing AST Syntax Trees & Signatures
                  </h3>
                  <p className="mt-1 text-xs sm:text-sm text-zinc-400">
                    Extracting functions, async dependencies, and API schemas
                  </p>

                  <div className="mt-6 rounded-2xl border border-white/[0.08] bg-black/70 p-4 font-mono text-left text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-purple-400">
                      <span>✓ Class: HybridRetriever (Async)</span>
                      <span className="text-zinc-500">Lines 1-84</span>
                    </div>
                    <div className="flex items-center justify-between text-blue-400">
                      <span>✓ Function: compute_rrf(dense, sparse, k=60)</span>
                      <span className="text-zinc-500">Signatures OK</span>
                    </div>
                    <div className="flex items-center justify-between text-emerald-400">
                      <span>✓ Vector DB Interface: QdrantCollection</span>
                      <span className="text-zinc-500">1536-dim</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* STEP 3: Dependency Graph Builds */}
              {currentStep === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-2xl text-center"
                >
                  <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-2">
                    4. Dynamic Knowledge & Dependency Graph
                  </div>
                  <h3 className="text-lg sm:text-xl font-bold text-white mb-6">
                    Synthesizing System Interconnections
                  </h3>

                  <div className="grid grid-cols-3 gap-4 font-mono text-xs">
                    <div className="rounded-2xl border border-blue-500/40 bg-blue-950/20 p-4 shadow-glow-blue">
                      <div className="font-bold text-blue-400">Input Query</div>
                      <div className="text-[11px] text-zinc-400 mt-1">User Prompt + Embeddings</div>
                    </div>
                    <div className="rounded-2xl border border-purple-500/40 bg-purple-950/20 p-4 shadow-glow-purple">
                      <div className="font-bold text-purple-400">RRF Engine</div>
                      <div className="text-[11px] text-zinc-400 mt-1">Dense + BM25 Fusion</div>
                    </div>
                    <div className="rounded-2xl border border-cyan-500/40 bg-cyan-950/20 p-4 shadow-glow-cyan">
                      <div className="font-bold text-cyan-400">Eval Gate</div>
                      <div className="text-[11px] text-zinc-400 mt-1">Groundedness &gt; 0.95</div>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-center gap-2 font-mono text-[11px] text-zinc-500">
                    <span>Graph mapped: 8 nodes · 14 directional edges</span>
                  </div>
                </motion.div>
              )}

              {/* STEP 4: Documentation Parsed */}
              {currentStep === 4 && (
                <motion.div
                  key="step4"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl text-center"
                >
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                    <BookOpen className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-xl sm:text-2xl font-bold text-white">
                    5. Grounded Documentation Synthesized
                  </h3>
                  <p className="mt-1 text-xs sm:text-sm text-zinc-400">
                    Contextual guides generated specifically for this implementation
                  </p>

                  <div className="mt-6 rounded-2xl border border-white/[0.08] bg-zinc-900/80 p-4 text-left text-xs leading-relaxed text-zinc-300">
                    <span className="font-bold text-white block mb-1">
                      📖 Topic: Reciprocal Rank Fusion vs Weighted Cosine
                    </span>
                    &ldquo;RRF normalizes sparse keyword frequencies and dense semantic embeddings into a single rank-based scale, mitigating outlier distortions.&rdquo;
                  </div>
                </motion.div>
              )}

              {/* STEP 5: Roadmap Generated */}
              {currentStep === 5 && (
                <motion.div
                  key="step5"
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-lg space-y-3 font-mono text-xs text-left"
                >
                  <div className="text-center mb-4">
                    <span className="font-mono text-xs font-bold text-purple-400 uppercase">
                      6. Personalized Milestone Roadmap
                    </span>
                    <h3 className="text-lg font-bold text-white">4 Structured Milestones</h3>
                  </div>

                  <div className="rounded-xl border border-white/[0.06] bg-zinc-900/50 p-3 flex items-center justify-between text-zinc-400">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      01. Document AST Chunking & Metadata
                    </span>
                    <span className="text-[10px] text-zinc-500">Completed</span>
                  </div>

                  <div className="rounded-xl border border-blue-500/50 bg-blue-950/30 p-3 flex items-center justify-between text-white shadow-glow-blue">
                    <span className="flex items-center gap-2 font-bold">
                      <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping" />
                      02. Hybrid Dense + BM25 Reciprocal Rank Fusion
                    </span>
                    <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">Active</span>
                  </div>

                  <div className="rounded-xl border border-white/[0.06] bg-zinc-900/30 p-3 flex items-center justify-between text-zinc-500">
                    <span>03. Automated RAG Triad Assertions</span>
                    <span className="text-[10px]">Upcoming</span>
                  </div>
                </motion.div>
              )}

              {/* STEP 6: Lesson Loaded */}
              {currentStep === 6 && (
                <motion.div
                  key="step6"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl rounded-2xl border border-white/[0.08] bg-zinc-900/80 p-6 text-left"
                >
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                    <span className="font-mono text-xs text-blue-400 font-semibold">
                      Milestone 02 · Concept Primer
                    </span>
                    <span className="text-xs text-zinc-400">5 min read</span>
                  </div>
                  <h3 className="mt-3 text-lg font-bold text-white">
                    Why Concurrent Async Retrieval Cuts P95 Latency by 50%
                  </h3>
                  <p className="mt-2 text-xs sm:text-sm text-zinc-300 leading-relaxed">
                    Executing Qdrant vector queries and SQLite BM25 scans sequentially forces round-trip wait states. By leveraging <code className="text-purple-300">asyncio.gather</code>, both indices respond concurrently.
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-xs font-mono text-emerald-400">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Concept validated · Ready to write code</span>
                  </div>
                </motion.div>
              )}

              {/* STEP 7: Live Code Editor */}
              {currentStep === 7 && (
                <motion.div
                  key="step7"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-2xl rounded-2xl border border-white/[0.08] bg-[#0E0E11] p-5 font-mono text-xs text-left shadow-2xl"
                >
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] text-zinc-400">
                    <div className="flex items-center gap-2">
                      <FileCode2 className="h-4 w-4 text-blue-400" />
                      <span>src/pipeline/hybrid_retrieval.py</span>
                    </div>
                    <span className="text-emerald-400 text-[10px]">Autosaved</span>
                  </div>

                  <div className="mt-3 space-y-1 text-zinc-300 leading-relaxed">
                    <p className="text-zinc-600"># Milestone 2: Reciprocal Rank Fusion implementation</p>
                    <p>
                      <span className="text-purple-400">async def</span>{" "}
                      <span className="text-blue-400">retrieve_hybrid</span>(query: str, top_k: int = 5):
                    </p>
                    <p className="ml-4 text-emerald-300">
                      dense_hits, sparse_hits = <span className="text-purple-400">await</span> asyncio.gather(
                    </p>
                    <p className="ml-8 text-zinc-400">vector_store.search(query, top_k=20),</p>
                    <p className="ml-8 text-zinc-400">bm25_index.search(query, top_k=20)</p>
                    <p className="ml-4 text-emerald-300">)</p>
                    <p className="ml-4">
                      <span className="text-purple-400">return</span> rerank_rrf(dense_hits, sparse_hits)[:top_k]
                      <span className="animate-pulse text-blue-400 font-bold ml-1">|</span>
                    </p>
                  </div>
                </motion.div>
              )}

              {/* STEP 8: AI Socratic Mentor Review */}
              {currentStep === 8 && (
                <motion.div
                  key="step8"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl rounded-2xl border border-purple-500/40 bg-[#14121E] p-5 text-left shadow-glow-purple"
                >
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
                    <div className="flex items-center gap-2 text-purple-300 font-mono text-xs font-bold">
                      <Bot className="h-4 w-4" />
                      <span>DevAtlas Senior AI Mentor</span>
                    </div>
                    <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded font-mono">
                      AST Review
                    </span>
                  </div>

                  <p className="mt-3 text-xs sm:text-sm text-zinc-200 leading-relaxed">
                    &ldquo;Excellent work using <code className="text-purple-300">asyncio.gather</code>! Your retrieval step is now concurrent. Let us verify against our test suite to ensure RRF score ties are deterministic.&rdquo;
                  </p>

                  <div className="mt-3 rounded-lg bg-black/60 p-2.5 font-mono text-[11px] text-emerald-400">
                    ✓ AST Verification: 0 syntax issues · 0 memory leaks
                  </div>
                </motion.div>
              )}

              {/* STEP 9: Milestone Completed */}
              {currentStep === 9 && (
                <motion.div
                  key="step9"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-lg text-center"
                >
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-glow-blue">
                    <CheckCircle2 className="h-9 w-9" />
                  </div>
                  <h3 className="mt-4 text-xl sm:text-2xl font-bold text-white">
                    10. Milestone 02 Passed with 100% Assertion Score
                  </h3>
                  <p className="mt-1 text-xs sm:text-sm text-zinc-400">
                    Automated RAG Triad test gates verified successfully
                  </p>

                  <div className="mt-6 grid grid-cols-3 gap-3 font-mono text-xs">
                    <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-3">
                      <span className="text-zinc-500 text-[10px] block">Groundedness</span>
                      <span className="text-emerald-400 font-bold">1.00</span>
                    </div>
                    <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-3">
                      <span className="text-zinc-500 text-[10px] block">Context Precision</span>
                      <span className="text-blue-400 font-bold">0.98</span>
                    </div>
                    <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-3">
                      <span className="text-zinc-500 text-[10px] block">Latency</span>
                      <span className="text-purple-400 font-bold">42ms</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* STEP 10: Cloud Deployment */}
              {currentStep === 10 && (
                <motion.div
                  key="step10"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35 }}
                  className="w-full max-w-xl text-center"
                >
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-purple-600 text-white shadow-glow-blue">
                    <Rocket className="h-8 w-8" />
                  </div>
                  <h3 className="mt-4 text-xl sm:text-2xl font-bold text-white">
                    11. Shipped to Production Cloud
                  </h3>
                  <p className="mt-1 text-xs sm:text-sm text-zinc-400">
                    Live production container deployed with monitoring & eval telemetry
                  </p>

                  <div className="mt-6 rounded-2xl border border-emerald-500/40 bg-emerald-950/20 p-4 font-mono text-xs flex items-center justify-between text-left">
                    <div className="flex items-center gap-2 text-white">
                      <Globe className="h-4 w-4 text-emerald-400" />
                      <span>https://rag-pipeline.devatlas.app</span>
                    </div>
                    <span className="rounded-full bg-emerald-500/20 text-emerald-300 px-3 py-1 text-[11px] font-bold">
                      Live 200 OK
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Bottom Footer Note */}
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-zinc-500 pt-4 border-t border-white/[0.06] font-mono">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              <span>Full lifecycle: Ingestion → Roadmap → Socratic Review → Production Deploy</span>
            </div>
            <span className="text-zinc-400">100% browser-based with isolated cloud container</span>
          </div>
        </div>
      </div>
    </section>
  );
}
