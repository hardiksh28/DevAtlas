"use client";

import { Sparkles } from "lucide-react";
import { Button } from "ui";

import { useGenerateMilestoneContent, useMilestone, useRoadmap } from "@/hooks/useRoadmap";
import { useSessionStore } from "@/store/useSessionStore";

/** Renders the milestone the learner currently has open — reuses the
 * existing app-wide `useSessionStore.currentMilestoneId` (not a new
 * workspace-local concept) so "which milestone am I on" stays a single
 * source of truth shared with the rest of the app. */
export function LessonPanel({ projectId }: { projectId: string }) {
  const { data: roadmap, isLoading: roadmapLoading, isError: roadmapError } = useRoadmap(projectId);
  const currentMilestoneId = useSessionStore((s) => s.currentMilestoneId);
  const setCurrentMilestone = useSessionStore((s) => s.setCurrentMilestone);
  const { data: milestone, isLoading: milestoneLoading } = useMilestone(projectId, currentMilestoneId);
  const generateContent = useGenerateMilestoneContent(projectId);

  if (roadmapLoading) {
    return <p className="p-4 text-sm text-ink-muted">Loading roadmap…</p>;
  }

  if (roadmapError || !roadmap) {
    return (
      <p className="p-4 text-sm text-ink-muted">
        No roadmap yet for this project — generate one from the project overview page first.
      </p>
    );
  }

  if (!currentMilestoneId) {
    return (
      <div className="flex h-full flex-col overflow-y-auto p-3">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">
          Pick a milestone
        </p>
        <ul className="space-y-1">
          {roadmap.milestones.map((m) => (
            <li key={m.id}>
              <button
                type="button"
                onClick={() => setCurrentMilestone(m.id)}
                disabled={m.status === "locked"}
                className="w-full rounded-sm px-2 py-1.5 text-left text-sm text-ink-muted hover:bg-surface-muted hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
              >
                {m.title}
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (milestoneLoading || !milestone) {
    return <p className="p-4 text-sm text-ink-muted">Loading lesson…</p>;
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <button
        type="button"
        onClick={() => setCurrentMilestone(null)}
        className="mb-2 self-start text-xs text-accent-ink hover:underline"
      >
        ← All milestones
      </button>
      <h2 className="text-sm font-semibold text-ink">{milestone.title}</h2>
      <p className="mb-3 text-xs text-ink-muted">{milestone.estimated_minutes} min · {milestone.status}</p>

      {!milestone.lesson_content ? (
        <Button
          type="button"
          size="sm"
          className="self-start"
          onClick={() => generateContent.mutate(milestone.id)}
          loading={generateContent.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Generate lesson
        </Button>
      ) : (
        <div className="space-y-4 text-sm text-ink">
          <p className="whitespace-pre-wrap">{milestone.lesson_content.explanation}</p>

          {milestone.lesson_content.key_points.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Key points
              </p>
              <ul className="list-inside list-disc space-y-1 text-ink-muted">
                {milestone.lesson_content.key_points.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          {milestone.lesson_content.exercises.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Exercises
              </p>
              <ol className="list-inside list-decimal space-y-2">
                {milestone.lesson_content.exercises.map((exercise, i) => (
                  <li key={i}>
                    {exercise.prompt}
                    {exercise.hint && <p className="ml-4 text-xs text-ink-muted">Hint: {exercise.hint}</p>}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
