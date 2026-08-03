"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  Folder,
  FileCode2,
  Terminal,
  Play,
  CheckCircle2,
  Bot,
  Sparkles,
  Layers,
  ChevronRight,
  ChevronDown,
  Globe,
  ExternalLink,
  Activity,
} from "lucide-react";

const CODE_LINES = [
  "# Milestone 2: Reciprocal Rank Fusion implementation",
  "async def retrieve_hybrid_context(query: str, top_k: int = 5):",
  "    # Concurrent dense + sparse vector index query",
  "    dense_hits, sparse_hits = await asyncio.gather(",
  "        vector_store.search(query, top_k=20),",
  "        bm25_index.search(query, top_k=20)",
  "    )",
  "    reranked = rerank_rrf(dense_hits, sparse_hits, k=60)",
  "    return reranked[:top_k]",
];

export function WorkspacePreview() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  const [activeTab, setActiveTab] = useState<string>("rag.py");
  const [folderOpen, setFolderOpen] = useState(true);
  const [evalRunning, setEvalRunning] = useState(false);
  const [evalLogs, setEvalLogs] = useState<string[]>([
    "✓ test_groundedness_score: 1.00 PASSED [0.12s]",
    "✓ test_context_precision: 0.98 PASSED [0.08s]",
    "✓ test_p95_latency_budget: 42ms PASSED [0.04s]",
  ]);

  const files = [
    { name: "rag.py", path: "src/pipeline/rag.py" },
    { name: "qdrant_store.py", path: "src/vector/qdrant_store.py" },
    { name: "test_evals.py", path: "evals/test_evals.py" },
  ];

  const runEvals = () => {
    setEvalRunning(true);
    setEvalLogs(["$ pytest evals/test_evals.py -v", "Running 3 test suites..."]);
    setTimeout(() => {
      setEvalLogs([
        "$ pytest evals/test_evals.py -v",
        "✓ test_groundedness_score: 1.00 PASSED [0.12s]",
        "✓ test_context_precision: 0.98 PASSED [0.08s]",
        "✓ test_p95_latency_budget: 42ms PASSED [0.04s]",
        "Status: 3 passed, 0 warnings in 0.24s (Exit Code 0)",
      ]);
      setEvalRunning(false);
    }, 1200);
  };

  return (
    <section
      id="workspace"
      ref={containerRef}
      className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32"
    >
      {/* Subtle Background Glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_0%,rgba(59,130,246,0.12),transparent_70%)]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-400">
            INTEGRATED CLOUD RUNTIME
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            A realistic IDE in your browser.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            Everything you need to write, test, evaluate, and ship AI systems without dealing with local environment breakage.
          </p>
        </motion.div>

        {/* Realistic IDE Mockup */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mt-16 overflow-hidden rounded-3xl border border-white/[0.1] bg-[#0E0E11] shadow-overlay backdrop-blur-2xl"
        >
          {/* Top IDE Navigation Header */}
          <div className="flex items-center justify-between border-b border-white/[0.08] bg-[#141418] px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-rose-500/80" />
              <span className="h-3 w-3 rounded-full bg-amber-500/80" />
              <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
              <div className="ml-3 hidden sm:flex items-center gap-2 rounded-md bg-black/40 px-3 py-1 text-xs font-mono text-zinc-400">
                <span>workspace: hybrid-rag-evals</span>
                <span className="text-zinc-600">/</span>
                <span className="text-blue-400 font-semibold">Python 3.12</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-xs text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Container Active
              </span>
              <button
                type="button"
                onClick={runEvals}
                disabled={evalRunning}
                className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 transition-colors shadow-glow-blue active:scale-95 disabled:opacity-50"
              >
                <Play className={`h-3 w-3 fill-white ${evalRunning ? "animate-spin" : ""}`} />
                <span>{evalRunning ? "Running..." : "Run Evals"}</span>
              </button>
            </div>
          </div>

          {/* Main IDE Body Grid */}
          <div className="grid lg:grid-cols-[220px_1fr_320px] min-h-[480px]">
            {/* 1. File Explorer Sidebar */}
            <div className="hidden lg:block border-r border-white/[0.08] bg-[#101014] p-4 text-xs font-mono">
              <div className="flex items-center justify-between font-bold text-zinc-400 uppercase tracking-wider text-[10px]">
                <span>Explorer</span>
                <span>3 files</span>
              </div>

              <div className="mt-4 space-y-1">
                <button
                  type="button"
                  onClick={() => setFolderOpen(!folderOpen)}
                  className="flex w-full items-center gap-1.5 text-zinc-300 font-semibold hover:text-white"
                >
                  {folderOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                  <Folder className="h-3.5 w-3.5 text-blue-400" />
                  <span>src/pipeline</span>
                </button>

                {folderOpen && (
                  <div className="ml-4 space-y-1 mt-1">
                    {files.map((file) => (
                      <button
                        key={file.name}
                        type="button"
                        onClick={() => setActiveTab(file.name)}
                        className={`flex w-full items-center gap-1.5 rounded px-2 py-1 transition-colors ${
                          activeTab === file.name
                            ? "bg-blue-500/20 text-blue-400 font-semibold"
                            : "text-zinc-400 hover:text-zinc-200"
                        }`}
                      >
                        <FileCode2 className="h-3.5 w-3.5" />
                        <span>{file.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-8 border-t border-white/[0.06] pt-4">
                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                  Milestone Progress
                </div>
                <div className="mt-2 text-xs font-semibold text-zinc-200">
                  Milestone 2 of 5
                </div>
                <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-zinc-800">
                  <div className="h-full w-[40%] rounded-full bg-blue-500" />
                </div>
              </div>
            </div>

            {/* 2. Center Code Editor + Terminal */}
            <div className="flex flex-col border-b lg:border-b-0 lg:border-r border-white/[0.08] bg-[#0E0E11]">
              {/* Tab Bar */}
              <div className="flex items-center border-b border-white/[0.08] bg-[#121216] px-2 text-xs font-mono">
                {files.map((file) => (
                  <button
                    key={file.name}
                    type="button"
                    onClick={() => setActiveTab(file.name)}
                    className={`flex items-center gap-1.5 border-b-2 px-3 py-2 transition-colors ${
                      activeTab === file.name
                        ? "border-blue-500 bg-[#0E0E11] text-white font-semibold"
                        : "border-transparent text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    <FileCode2 className="h-3.5 w-3.5 text-blue-400" />
                    <span>{file.name}</span>
                  </button>
                ))}
              </div>

              {/* Code Contents with Syntax Highlighting & Blinking Cursor */}
              <div className="flex-1 p-4 font-mono text-xs text-zinc-300 overflow-x-auto leading-relaxed">
                <div className="space-y-1">
                  {CODE_LINES.map((line, idx) => (
                    <div key={idx} className="flex items-start">
                      <span className="w-6 text-zinc-600 select-none mr-2 text-right">{idx + 1}</span>
                      <span className="flex-1">
                        {line.startsWith("#") ? (
                          <span className="text-zinc-500">{line}</span>
                        ) : line.includes("async def") ? (
                          <>
                            <span className="text-purple-400">async def</span>{" "}
                            <span className="text-blue-400">retrieve_hybrid_context</span>(query: str, top_k: int = 5):
                          </>
                        ) : line.includes("asyncio.gather") ? (
                          <>
                            <span className="text-zinc-300">    dense_hits, sparse_hits = </span>
                            <span className="text-purple-400">await</span>{" "}
                            <span className="text-yellow-300">asyncio.gather</span>(
                          </>
                        ) : line.includes("return") ? (
                          <>
                            <span className="text-purple-400">    return</span>{" "}
                            <span>reranked[:top_k]</span>
                            <span className="animate-pulse text-blue-400 font-bold ml-0.5">|</span>
                          </>
                        ) : (
                          <span>{line}</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Integrated Terminal */}
              <div className="border-t border-white/[0.08] bg-[#0A0A0D] p-3 text-xs font-mono">
                <div className="flex items-center justify-between text-zinc-500 pb-2 border-b border-white/[0.04]">
                  <div className="flex items-center gap-2">
                    <Terminal className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-zinc-300">Terminal (zsh)</span>
                  </div>
                  <span className="text-emerald-400">Exit Code 0</span>
                </div>
                <div className="mt-2 text-zinc-400 space-y-0.5">
                  {evalLogs.map((log, i) => (
                    <p
                      key={i}
                      className={
                        log.startsWith("✓")
                          ? "text-emerald-400"
                          : log.startsWith("$")
                          ? "text-zinc-200"
                          : "text-zinc-400"
                      }
                    >
                      {log}
                    </p>
                  ))}
                </div>
              </div>
            </div>

            {/* 3. Right Sidebar: Live AI Mentor & Browser Preview */}
            <div className="bg-[#101014] p-4 text-xs flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between font-mono text-[11px] font-bold text-zinc-400 uppercase tracking-wider">
                  <div className="flex items-center gap-1.5 text-purple-400">
                    <Bot className="h-4 w-4" />
                    <span>AI Mentor</span>
                  </div>
                  <span className="text-emerald-400">Active</span>
                </div>

                <div className="mt-4 rounded-xl border border-white/[0.08] bg-zinc-900/80 p-3">
                  <div className="flex items-center gap-1.5 font-mono text-[10px] text-zinc-500 uppercase">
                    <Sparkles className="h-3 w-3 text-purple-400" />
                    AST Code Review
                  </div>
                  <p className="mt-2 text-xs text-zinc-300 leading-relaxed">
                    Your concurrency patch using <code className="text-purple-300">asyncio.gather</code> dropped latency by 56%. Ready to run production eval assertions!
                  </p>
                </div>

                <div className="mt-4 rounded-xl border border-blue-500/30 bg-blue-950/20 p-3">
                  <div className="font-mono text-[10px] font-bold text-blue-400 uppercase">
                    Next Milestone Action
                  </div>
                  <p className="mt-1 text-xs text-zinc-300">
                    Configure the RAG Triad test suite in <code className="text-blue-300 font-mono">evals/</code>.
                  </p>
                </div>
              </div>

              {/* Live Preview Dock */}
              <div className="mt-6 rounded-xl border border-white/[0.06] bg-black/40 p-3 font-mono text-[11px]">
                <div className="flex items-center justify-between text-zinc-400 pb-2 border-b border-white/[0.04]">
                  <div className="flex items-center gap-1.5 text-zinc-300">
                    <Globe className="h-3.5 w-3.5 text-blue-400" />
                    <span>Preview Port :8000</span>
                  </div>
                  <span className="text-emerald-400">200 OK</span>
                </div>
                <div className="mt-2 text-zinc-400 flex items-center justify-between">
                  <span>Latency:</span>
                  <span className="text-emerald-400 font-bold">42ms (p95)</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
