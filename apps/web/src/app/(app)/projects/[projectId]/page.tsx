"use client";

import {
  ArrowRight,
  BookOpen,
  Code2,
  FileText,
  GitPullRequest,
  Map,
  MessageSquare,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/Badge";
import { useProject } from "@/hooks/useProjects";

// Future modules shown as visible-but-honest placeholders. None of
// these render interactive controls — the only live actions on this
// page are real ones (Settings).
const MODULES: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: FileText,
    title: "Documentation",
    body: "Ingest the docs and repositories your project depends on.",
  },
  {
    icon: Map,
    title: "Roadmap",
    body: "A milestone plan generated from your project's goal and stack.",
  },
  {
    icon: MessageSquare,
    title: "Mentor",
    body: "Ask questions and get progressive hints grounded in your code.",
  },
  {
    icon: GitPullRequest,
    title: "Code Review",
    body: "Reviews of your commits, tuned to what you're learning.",
  },
  {
    icon: TrendingUp,
    title: "Progress",
    body: "Concept mastery and milestone completion over time.",
  },
];

export default function ProjectOverviewPage() {
  const params = useParams<{ projectId: string }>();
  const { data: project } = useProject(params.projectId);

  if (!project) return null;

  const needsDescription = !project.description;

  return (
    <div className="flex flex-col gap-8">
      {/* Start here — always points at a real, currently-possible action. */}
      <section
        aria-labelledby="start-here-heading"
        className="rounded-lg border border-line bg-surface p-5"
      >
        <h2 id="start-here-heading" className="flex items-center gap-2 text-sm font-semibold text-ink-secondary">
          <BookOpen className="h-4 w-4" aria-hidden="true" />
          Start here
        </h2>
        {needsDescription ? (
          <>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
              Describe what this project should do and for whom. A concrete goal is what the
              roadmap generator will work from when it lands — and it sharpens your own thinking
              now.
            </p>
            <Link
              href={`/projects/${project.id}/settings`}
              className="mt-3 inline-flex items-center gap-1.5 rounded-sm text-sm font-medium text-accent-ink hover:underline"
            >
              Add a description in Settings
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </>
        ) : (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
            Your project is set up. The next step — adding documentation so your mentor understands
            your stack — is the module we&apos;re building now. Until then, keep refining the
            project&apos;s scope in Settings.
          </p>
        )}
      </section>

      {/* Roadmap placeholder — explicitly labeled, no fake content. */}
      <section aria-labelledby="roadmap-heading">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="roadmap-heading" className="text-sm font-semibold text-ink-secondary">
            Project roadmap
          </h2>
          <Badge variant="outline">Available after documentation ingestion</Badge>
        </div>
        <div className="mt-3 rounded-lg border border-dashed border-line-strong p-5">
          <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
            Once you can add documentation and a repository, DevAtlas will generate a milestone
            roadmap here — the ordered path from this project&apos;s current state to a deployed,
            reviewed piece of software.
          </p>
        </div>
      </section>

      {/* Module grid */}
      <section aria-labelledby="modules-heading">
        <h2 id="modules-heading" className="text-sm font-semibold text-ink-secondary">
          Modules
        </h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((mod) => (
            <div key={mod.title} className="rounded-lg border border-line bg-surface p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-surface-muted text-ink-muted">
                  <mod.icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <Badge variant="outline">Coming soon</Badge>
              </div>
              <h3 className="mt-3 text-sm font-semibold text-ink">{mod.title}</h3>
              <p className="mt-1 text-sm text-ink-muted">{mod.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* The one real, always-available action on this page — Monaco,
          file explorer, lesson panel, and mentor chat, all live. */}
      <section
        aria-labelledby="workspace-heading"
        className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-line bg-surface p-5"
      >
        <div>
          <h2 id="workspace-heading" className="flex items-center gap-2 text-sm font-semibold text-ink-secondary">
            <Code2 className="h-4 w-4" aria-hidden="true" />
            Interactive workspace
          </h2>
          <p className="mt-1 max-w-xl text-sm text-ink-muted">
            Editor, file explorer, lesson panel, and mentor chat — open this project&apos;s workspace.
          </p>
        </div>
        <Link
          href={`/projects/${project.id}/workspace`}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
        >
          Open workspace
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </section>
    </div>
  );
}
