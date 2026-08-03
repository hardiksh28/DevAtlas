import React from "react";
import {
  Cpu,
  Layers,
  Terminal,
  Database,
  Boxes,
  Sparkles,
  ShieldCheck,
  Workflow,
} from "lucide-react";

interface TechItem {
  name: string;
  category: string;
  icon: React.ReactNode;
}

const iconClass = "h-4 w-4 text-slate-400";

const TECH_STACK: TechItem[] = [
  { name: "PyTorch", category: "Deep Learning", icon: <Cpu className={iconClass} /> },
  { name: "LangChain", category: "Orchestration", icon: <Workflow className={iconClass} /> },
  { name: "FastAPI", category: "High-Perf Backend", icon: <Terminal className={iconClass} /> },
  { name: "Qdrant / pgvector", category: "Vector Store", icon: <Database className={iconClass} /> },
  { name: "Hugging Face", category: "Open Models", icon: <Sparkles className={iconClass} /> },
  { name: "Docker & K8s", category: "Deployment", icon: <Boxes className={iconClass} /> },
  { name: "LlamaIndex", category: "Data Framework", icon: <Layers className={iconClass} /> },
  { name: "Evaluations", category: "RAG Triad & CI", icon: <ShieldCheck className={iconClass} /> },
];

export function TechStackTicker() {
  return (
    <div className="relative border-y border-white/10 bg-white/[0.015] py-8">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="text-center font-mono text-xs font-semibold uppercase tracking-widest text-slate-500">
          Learn, build, and deploy production stacks trusted by top engineering teams
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 sm:gap-4 md:gap-6">
          {TECH_STACK.map((tech) => (
            <div
              key={tech.name}
              className="group flex items-center gap-2.5 rounded-lg border border-white/10 bg-white/[0.02] px-4 py-2 transition-colors duration-200 hover:border-white/20 hover:bg-white/[0.04]"
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/[0.04]">
                {tech.icon}
              </span>
              <div className="flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-300 group-hover:text-white">
                  {tech.name}
                </span>
                <span className="text-[10px] text-slate-500">
                  {tech.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
