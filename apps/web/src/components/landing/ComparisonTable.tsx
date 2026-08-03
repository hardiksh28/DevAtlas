"use client";

import React from "react";
import { Check, X, Sparkles } from "lucide-react";

interface ComparisonRow {
  feature: string;
  tutorials: boolean | string;
  chatgpt: boolean | string;
  devatlas: boolean | string;
}

const COMPARISON_DATA: ComparisonRow[] = [
  {
    feature: "Grounded on your exact repos & documentation",
    tutorials: false,
    chatgpt: "Partial / Hallucinations",
    devatlas: true,
  },
  {
    feature: "4-Tier Socratic hints (never spoils solutions)",
    tutorials: false,
    chatgpt: false,
    devatlas: true,
  },
  {
    feature: "Personalized milestone roadmap from repo",
    tutorials: false,
    chatgpt: "Generic Text Only",
    devatlas: true,
  },
  {
    feature: "Integrated cloud runtime with vector databases",
    tutorials: false,
    chatgpt: false,
    devatlas: true,
  },
  {
    feature: "Senior AST code reviews & architectural why",
    tutorials: false,
    chatgpt: "Basic Linting",
    devatlas: true,
  },
  {
    feature: "Automated RAG Triad & hallucination eval gates",
    tutorials: false,
    chatgpt: false,
    devatlas: true,
  },
  {
    feature: "Production Docker & cloud deployment guidance",
    tutorials: "Outdated",
    chatgpt: false,
    devatlas: true,
  },
];

export function ComparisonTable() {
  return (
    <section id="comparison" className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-blue-400">
            HOW WE COMPARE
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-[-0.03em] text-white">
            Built for engineering depth, not shortcuts.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-zinc-400">
            See how DevAtlas fundamentally differs from passive video courses and generic chat generators.
          </p>
        </div>

        {/* Comparison Table Card */}
        <div className="mt-16 overflow-x-auto rounded-3xl border border-white/[0.08] bg-zinc-900/40 p-1 backdrop-blur-2xl shadow-overlay">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b border-white/[0.08] text-xs font-mono uppercase tracking-wider text-zinc-400">
                <th className="p-6 font-semibold">Capability</th>
                <th className="p-6 font-semibold text-center text-zinc-400">Video Tutorials</th>
                <th className="p-6 font-semibold text-center text-zinc-400">ChatGPT / Copilot</th>
                <th className="p-6 font-bold text-center text-blue-400 bg-blue-950/20 rounded-t-2xl border-x border-t border-blue-500/30">
                  <div className="flex items-center justify-center gap-1.5">
                    <Sparkles className="h-4 w-4" />
                    <span>DevAtlas</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06] text-xs sm:text-sm">
              {COMPARISON_DATA.map((row, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-6 font-medium text-zinc-200">{row.feature}</td>

                  {/* Video Tutorials */}
                  <td className="p-6 text-center text-zinc-400 font-mono">
                    {row.tutorials === true ? (
                      <Check className="h-5 w-5 text-emerald-400 mx-auto" />
                    ) : row.tutorials === false ? (
                      <X className="h-5 w-5 text-rose-500 mx-auto opacity-70" />
                    ) : (
                      <span className="text-zinc-500 text-xs">{row.tutorials}</span>
                    )}
                  </td>

                  {/* ChatGPT / Copilot */}
                  <td className="p-6 text-center text-zinc-400 font-mono">
                    {row.chatgpt === true ? (
                      <Check className="h-5 w-5 text-emerald-400 mx-auto" />
                    ) : row.chatgpt === false ? (
                      <X className="h-5 w-5 text-rose-500 mx-auto opacity-70" />
                    ) : (
                      <span className="text-zinc-400 text-xs">{row.chatgpt}</span>
                    )}
                  </td>

                  {/* DevAtlas Highlight Column */}
                  <td className="p-6 text-center font-mono font-semibold text-white bg-blue-950/10 border-x border-blue-500/20 last:rounded-b-2xl">
                    {row.devatlas === true ? (
                      <div className="flex items-center justify-center gap-1.5 text-blue-400">
                        <Check className="h-5 w-5 stroke-[2.5]" />
                      </div>
                    ) : (
                      <span className="text-blue-300">{row.devatlas}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
