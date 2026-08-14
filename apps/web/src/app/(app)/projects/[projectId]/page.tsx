"use client";

import {
  ArrowRight,
  BookOpen,
  Code2,
  FileText,
  GitPullRequest,
  MessageSquare,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { RoadmapSection } from "@/components/projects/RoadmapSection";
import { Badge } from "@/components/ui/Badge";
import { useProject } from "@/hooks/useProjects";

// Modules with no dedicated UI yet — visible-but-honest placeholders.
// Roadmap has its own real section below; Mentor is live inside the
// workspace's Chat tab (see the "Interactive workspace" section below) —
// neither belongs in this "not built" list.
const MODULES: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: FileText,
    title: "Documentation",
    body: "Ingest the docs and repositories your project depends on.",
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
            Your project is set up. Generate a roadmap below to get a milestone plan, then open
            the workspace to start your first lesson and ask your mentor questions.
          </p>
        )}
      </section>

      <RoadmapSection projectId={project.id} />

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
            Editor, file explorer, lesson panel, and{" "}
            <span className="inline-flex items-center gap-1 text-ink">
              <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
              mentor chat
            </span>{" "}
            — open this project&apos;s workspace.
          </p>
        </div>
        <Link
          href={`/projects/${project.id}/workspace`}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm font-medium text-ink hover:bg-accent-hover"
        >
          Open workspace
          <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </section>
    </div>
  );
}
