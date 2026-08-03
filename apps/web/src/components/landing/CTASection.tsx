"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Sparkles, CheckCircle2 } from "lucide-react";

export function CTASection() {
  return (
    <section className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32">
      {/* Centerpiece Spotlight Glow */}
      <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
        <div className="h-[400px] w-[700px] rounded-full bg-gradient-to-r from-blue-600/20 via-purple-600/15 to-cyan-500/15 blur-[120px]" />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl border border-white/[0.1] bg-gradient-to-b from-zinc-900/80 to-[#121215]/90 p-8 sm:p-14 lg:p-20 text-center backdrop-blur-2xl shadow-overlay">
          {/* Subtle Grid Backdrop */}
          <div className="pointer-events-none absolute inset-0 bg-matrix-grid opacity-30" />

          <div className="relative mx-auto max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-blue-400 backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5" />
              <span>START BUILDING TODAY</span>
            </div>

            <h2 className="mt-6 text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-extrabold tracking-[-0.04em] text-white">
              Build software like an engineer.
            </h2>

            <p className="mt-6 text-base sm:text-lg text-zinc-400 leading-relaxed max-w-2xl mx-auto">
              Stop getting stuck in tutorial loops. Upload your repository, follow your personalized
              milestone roadmap, and ship production-ready AI systems.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/register"
                className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 px-8 py-4 text-sm font-semibold text-white shadow-glow-blue transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(59,130,246,0.6)]"
              >
                <span>Start Building Free</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/login"
                className="rounded-xl border border-white/[0.1] bg-zinc-800/80 px-7 py-4 text-sm font-semibold text-zinc-300 backdrop-blur-xl transition-colors hover:bg-zinc-700 hover:text-white"
              >
                Sign In to Workspace
              </Link>
            </div>

            <div className="mt-8 flex items-center justify-center gap-6 text-xs text-zinc-500">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Free forever tier
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Instant setup
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
