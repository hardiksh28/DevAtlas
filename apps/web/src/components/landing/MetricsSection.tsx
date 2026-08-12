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
}

const METRICS: MetricItem[] = [
  {
    icon: GitBranch,
    targetNum: 14200,
    suffix: "+",
    label: "Repositories Parsed",
    sublabel: "Real-world codebases indexed",
  },
  {
    icon: Map,
    targetNum: 38500,
    suffix: "+",
    label: "Roadmaps Generated",
    sublabel: "Personalized milestone paths",
  },
  {
    icon: BookOpen,
    targetNum: 120000,
    suffix: "+",
    label: "Lessons Created",
    sublabel: "Grounded on source code",
  },
  {
    icon: Rocket,
    targetNum: 8900,
    suffix: "+",
    label: "Projects Built",
    sublabel: "Shipped to production cloud",
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
    <section ref={containerRef} className="relative border-y-2 border-line bg-surface-muted py-14">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="font-mono text-xs font-bold uppercase tracking-[0.2em] text-ink-muted">
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
                className="group relative overflow-hidden rounded-2xl border-2 border-ink bg-surface p-6 text-center transition-shadow duration-200 sticker-shadow-sm sticker-shadow-hover"
              >
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl border-2 border-ink bg-accent-soft text-ink transition-transform duration-300 group-hover:rotate-6">
                  <Icon className="h-5 w-5" />
                </div>

                <div className="mt-4 font-mono text-2xl sm:text-3xl font-black tracking-tight text-ink">
                  <AnimatedCounter
                    target={metric.targetNum}
                    suffix={metric.suffix}
                    decimals={metric.decimals}
                    inView={isInView}
                  />
                </div>

                <div className="mt-1 text-sm font-bold text-ink">{metric.label}</div>

                <div className="mt-0.5 text-xs text-ink-muted">{metric.sublabel}</div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
