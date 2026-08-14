"use client";

import { ArrowRight, CheckCircle2, Circle, Lock, Map, Sparkles } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "ui";

import { Badge } from "@/components/ui/Badge";
import { useGenerateRoadmap, useRoadmap, useStacks } from "@/hooks/useRoadmap";
import type { ExperienceLevel, MilestoneStatus } from "@/types/roadmap";

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const STATUS_ICON: Record<MilestoneStatus, typeof CheckCircle2> = {
  completed: CheckCircle2,
  in_progress: Circle,
  available: Circle,
  locked: Lock,
};

/** Generate-roadmap form, shown when the project has none yet — picks
 * from the seeded taxonomy's actual (stack, stack_version) pairs so it
 * can never submit a combination the curriculum engine has no concepts
 * for (see useStacks' docstring). */
function GenerateRoadmapForm({ projectId }: { projectId: string }) {
  const { data: stacksData, isLoading: stacksLoading } = useStacks();
  const generate = useGenerateRoadmap(projectId);
  const [stackKey, setStackKey] = useState("");
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>("beginner");

  const stacks = stacksData?.items ?? [];

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const stack = stacks.find((s) => `${s.stack}@${s.stack_version}` === stackKey);
    if (!stack) return;
    generate.mutate({
      stack: stack.stack,
      stack_version: stack.stack_version,
      experience_level: experienceLevel,
    });
  }

  if (!stacksLoading && stacks.length === 0) {
    return (
      <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
        No stacks are seeded in the taxonomy yet — an admin needs to run{" "}
        <code className="rounded bg-surface-muted px-1 py-0.5 text-xs">
          uv run python scripts/seed_taxonomy.py
        </code>{" "}
        before a roadmap can be generated.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
        DevAtlas deterministically sequences milestones from the taxonomy&apos;s prerequisite
        graph — pick the stack you&apos;re building with and your experience level.
      </p>

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-ink-secondary">Stack</span>
          <select
            value={stackKey}
            onChange={(e) => setStackKey(e.target.value)}
            required
            disabled={stacksLoading}
            className="min-h-10 min-w-48 rounded-md border border-line-strong bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
          >
            <option value="" disabled>
              {stacksLoading ? "Loading…" : "Select a stack"}
            </option>
            {stacks.map((s) => (
              <option key={`${s.stack}@${s.stack_version}`} value={`${s.stack}@${s.stack_version}`}>
                {s.stack} {s.stack_version} ({s.concept_count} concepts)
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-ink-secondary">Experience level</span>
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value as ExperienceLevel)}
            className="min-h-10 rounded-md border border-line-strong bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
          >
            {EXPERIENCE_LEVELS.map((level) => (
              <option key={level.value} value={level.value}>
                {level.label}
              </option>
            ))}
          </select>
        </label>

        <Button type="submit" loading={generate.isPending} disabled={!stackKey}>
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Generate roadmap
        </Button>
      </div>

      {generate.isError && (
        <p role="alert" className="text-sm text-danger-ink">
          {generate.error.message}
        </p>
      )}
    </form>
  );
}

export function RoadmapSection({ projectId }: { projectId: string }) {
  const { data: roadmap, isLoading, isError } = useRoadmap(projectId);

  return (
    <section aria-labelledby="roadmap-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="roadmap-heading" className="text-sm font-semibold text-ink-secondary">
          Project roadmap
        </h2>
        {roadmap && (
          <Badge variant="accent">
            {roadmap.milestones.filter((m) => m.status === "completed").length}/
            {roadmap.milestones.length} milestones
          </Badge>
        )}
      </div>

      <div className="mt-3 rounded-lg border border-line bg-surface p-5">
        {isLoading && <p className="text-sm text-ink-muted">Loading roadmap…</p>}

        {!isLoading && (isError || !roadmap) && <GenerateRoadmapForm projectId={projectId} />}

        {roadmap && (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2 text-xs text-ink-muted">
              <Map className="h-3.5 w-3.5" aria-hidden="true" />
              <span>
                {roadmap.stack} {roadmap.stack_version} · {roadmap.experience_level} ·{" "}
                {roadmap.estimated_total_minutes} min total
              </span>
            </div>

            <ol className="flex flex-col gap-1.5">
              {roadmap.milestones.map((milestone) => {
                const Icon = STATUS_ICON[milestone.status];
                return (
                  <li
                    key={milestone.id}
                    className="flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm"
                  >
                    <Icon
                      className={`h-4 w-4 shrink-0 ${
                        milestone.status === "completed"
                          ? "text-success-ink"
                          : milestone.status === "locked"
                            ? "text-ink-faint"
                            : "text-accent-ink"
                      }`}
                      aria-hidden="true"
                    />
                    <span
                      className={milestone.status === "locked" ? "text-ink-faint" : "text-ink"}
                    >
                      {milestone.title}
                    </span>
                    <span className="text-xs text-ink-faint">{milestone.estimated_minutes}m</span>
                  </li>
                );
              })}
            </ol>

            <Link
              href={`/projects/${projectId}/workspace`}
              className="mt-1 inline-flex w-fit items-center gap-1.5 rounded-sm text-sm font-medium text-accent-ink hover:underline"
            >
              Open the first milestone in your workspace
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}
