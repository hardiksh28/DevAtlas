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
    <section id="comparison" className="relative border-t-2 border-line py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-accent-ink">
            HOW WE COMPARE
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-black tracking-[-0.03em] text-ink">
            Built for engineering depth, not shortcuts.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-ink-secondary">
            See how DevAtlas fundamentally differs from passive video courses and generic chat generators.
          </p>
        </div>

        {/* Comparison Table Card */}
        <div className="mt-16 overflow-x-auto rounded-3xl border-2 border-ink bg-surface p-1 sticker-shadow">
          <table className="w-full text-left border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b-2 border-line text-xs font-mono uppercase tracking-wider text-ink-muted">
                <th className="p-6 font-bold">Capability</th>
                <th className="p-6 font-bold text-center text-ink-muted">Video Tutorials</th>
                <th className="p-6 font-bold text-center text-ink-muted">ChatGPT / Copilot</th>
                <th className="p-6 font-bold text-center text-ink bg-accent rounded-t-2xl border-x-2 border-t-2 border-ink">
                  <div className="flex items-center justify-center gap-1.5">
                    <Sparkles className="h-4 w-4" />
                    <span>DevAtlas</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-line text-xs sm:text-sm">
              {COMPARISON_DATA.map((row, idx) => (
                <tr key={idx} className="hover:bg-surface-muted transition-colors">
                  <td className="p-6 font-medium text-ink">{row.feature}</td>

                  {/* Video Tutorials */}
                  <td className="p-6 text-center text-ink-muted font-mono">
                    {row.tutorials === true ? (
                      <Check className="h-5 w-5 text-success mx-auto" />
                    ) : row.tutorials === false ? (
                      <X className="h-5 w-5 text-rose-400 mx-auto" />
                    ) : (
                      <span className="text-ink-faint text-xs">{row.tutorials}</span>
                    )}
                  </td>

                  {/* ChatGPT / Copilot */}
                  <td className="p-6 text-center text-ink-muted font-mono">
                    {row.chatgpt === true ? (
                      <Check className="h-5 w-5 text-success mx-auto" />
                    ) : row.chatgpt === false ? (
                      <X className="h-5 w-5 text-rose-400 mx-auto" />
                    ) : (
                      <span className="text-ink-faint text-xs">{row.chatgpt}</span>
                    )}
                  </td>

                  {/* DevAtlas Highlight Column */}
                  <td className="p-6 text-center font-mono font-bold text-ink bg-accent-soft border-x-2 border-ink last:rounded-b-2xl">
                    {row.devatlas === true ? (
                      <div className="flex items-center justify-center gap-1.5 text-ink">
                        <Check className="h-5 w-5 stroke-[2.5]" />
                      </div>
                    ) : (
                      <span className="text-ink">{row.devatlas}</span>
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
