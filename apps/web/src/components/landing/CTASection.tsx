"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Sparkles, CheckCircle2 } from "lucide-react";

export function CTASection() {
  return (
    <section className="relative border-t-2 border-line py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-[2rem] border-2 border-ink bg-ink p-8 sm:p-14 lg:p-20 text-center sticker-shadow">
          {/* Ambient glow */}
          <div
            className="pointer-events-none absolute inset-0 -z-0"
            style={{
              background: "radial-gradient(ellipse 600px 300px at 50% 0%, rgba(250,204,21,0.25), transparent 70%)",
            }}
          />

          <div className="relative mx-auto max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border-2 border-white/20 bg-white/10 px-3.5 py-1 text-xs font-bold text-accent">
              <Sparkles className="h-3.5 w-3.5" />
              <span>START BUILDING TODAY</span>
            </div>

            <h2 className="mt-6 text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-black tracking-[-0.04em] text-white">
              Build software like an engineer.
            </h2>

            <p className="mt-6 text-base sm:text-lg text-white/60 leading-relaxed max-w-2xl mx-auto">
              Stop getting stuck in tutorial loops. Upload your repository, follow your personalized
              milestone roadmap, and ship production-ready AI systems.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/register"
                className="group inline-flex items-center gap-2 rounded-full border-2 border-ink bg-accent px-8 py-4 text-sm font-bold text-ink sticker-shadow-sm sticker-shadow-hover"
              >
                <span>Start Building Free</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/login"
                className="rounded-full border-2 border-white/20 bg-white/5 px-7 py-4 text-sm font-bold text-white transition-colors hover:bg-white/10"
              >
                Sign In to Workspace
              </Link>
            </div>

            <div className="mt-8 flex items-center justify-center gap-6 text-xs text-white/50">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-accent" />
                Free forever tier
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-accent" />
                Instant setup
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
