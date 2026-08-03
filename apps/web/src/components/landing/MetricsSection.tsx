"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import { GitBranch, Map, BookOpen, Rocket } from "lucide-react";

interface MetricItem {
  icon: React.ElementType;
  targetNum: number;
  suffix: string;
  decimals?: number;
  label: string;
  sublabel: string;
  glowColor: string;
}

const METRICS: MetricItem[] = [
  {
    icon: GitBranch,
    targetNum: 14200,
    suffix: "+",
    label: "Repositories Parsed",
    sublabel: "Real-world codebases indexed",
    glowColor: "from-blue-500/20 to-transparent",
  },
  {
    icon: Map,
    targetNum: 38500,
    suffix: "+",
    label: "Roadmaps Generated",
    sublabel: "Personalized milestone paths",
    glowColor: "from-purple-500/20 to-transparent",
  },
  {
    icon: BookOpen,
    targetNum: 120000,
    suffix: "+",
    label: "Lessons Created",
    sublabel: "Grounded on source code",
    glowColor: "from-cyan-500/20 to-transparent",
  },
  {
    icon: Rocket,
    targetNum: 8900,
    suffix: "+",
    label: "Projects Built",
    sublabel: "Shipped to production cloud",
    glowColor: "from-emerald-500/20 to-transparent",
  },
];

function AnimatedCounter({
  target,
  suffix,
  decimals = 0,
  inView,
}: {
  target: number;
  suffix: string;
  decimals?: number;
  inView: boolean;
}) {
  const [count, setCount] = useState(0);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (!inView || prefersReducedMotion) {
      if (prefersReducedMotion && inView) setCount(target);
      return;
    }

    let start = 0;
    const duration = 1800; // ms
    const startTime = performance.now();

    const updateCounter = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentVal = start + (target - start) * easeOut;

      setCount(currentVal);

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        setCount(target);
      }
    };

    requestAnimationFrame(updateCounter);
  }, [inView, target, prefersReducedMotion]);

  const formatted =
    decimals > 0
      ? count.toFixed(decimals)
      : Math.floor(count).toLocaleString();

  return (
    <span>
      {formatted}
      {suffix}
    </span>
  );
}

export function MetricsSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-50px" });

  return (
    <section
      ref={containerRef}
      className="relative border-y border-white/[0.08] bg-[#09090B]/60 py-14 backdrop-blur-md"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            ENGINEERING RESULTS AT SCALE
          </p>
        </div>

        {/* 4 Core Metrics Grid */}
        <div className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {METRICS.map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: idx * 0.1, ease: "easeOut" }}
                whileHover={{ y: -4 }}
                className="group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-zinc-900/50 p-6 text-center backdrop-blur-xl transition-all duration-300 hover:border-white/[0.18] hover:bg-zinc-900/80 hover:shadow-glass"
              >
                {/* Background ambient radial highlight */}
                <div
                  className={`pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 h-24 w-24 rounded-full bg-gradient-to-b ${metric.glowColor} blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                />

                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-zinc-800/80 text-zinc-300 shadow-sm transition-all duration-300 group-hover:border-blue-500/40 group-hover:text-blue-400 group-hover:rotate-6">
                  <Icon className="h-5 w-5" />
                </div>

                <div className="mt-4 font-mono text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                  <AnimatedCounter
                    target={metric.targetNum}
                    suffix={metric.suffix}
                    decimals={metric.decimals}
                    inView={isInView}
                  />
                </div>

                <div className="mt-1 text-sm font-semibold text-zinc-200">
                  {metric.label}
                </div>

                <div className="mt-0.5 text-xs text-zinc-500">
                  {metric.sublabel}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
