"use client";

import { Bot, CheckCircle2, Circle, Hammer, RefreshCw, Sparkles, User } from "lucide-react";
import { useState } from "react";
import { Button } from "ui";

import { Badge } from "@/components/ui/Badge";
import { TextArea } from "@/components/ui/TextArea";
import {
  useBuildPlan,
  useGenerateBuildPlan,
  useUpdateStepMode,
  useUpdateStepStatus,
} from "@/hooks/useBuildPlan";
import type { BuildPlanStepRead, StepBuildMode } from "@/types/build-plan";

function GenerateBuildPlanForm({ projectId, regenerate }: { projectId: string; regenerate: boolean }) {
  const [context, setContext] = useState("");
  const generate = useGenerateBuildPlan(projectId);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    generate.mutate(context.trim() || null);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {!regenerate && (
        <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
          DevAtlas analyzes this project&apos;s description and proposes a stack and an ordered,
          ready-to-implement step list — a technical build plan, not a learning roadmap. Add a
          description in Settings first if you haven&apos;t.
        </p>
      )}
      <TextArea
        id="build-plan-context"
        label={regenerate ? "What should change?" : "Anything else to consider?"}
        optional
        rows={2}
        maxLength={4000}
        placeholder="e.g. I'd rather use SQLite than Postgres for this one"
        value={context}
        onChange={(e) => setContext(e.target.value)}
      />
      {generate.isError && (
        <p role="alert" className="text-sm text-danger-ink">
          {generate.error.message}
        </p>
      )}
      <div>
        <Button type="submit" loading={generate.isPending}>
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          {regenerate ? "Regenerate build plan" : "Generate build plan"}
        </Button>
      </div>
    </form>
  );
}

function BuildModePicker({
  step,
  projectId,
}: {
  step: BuildPlanStepRead;
  projectId: string;
}) {
  const updateMode = useUpdateStepMode(projectId);

  function pick(mode: StepBuildMode) {
    if (step.build_mode === mode || updateMode.isPending) return;
    updateMode.mutate({ stepId: step.id, buildMode: mode });
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        type="button"
        onClick={() => pick("guided")}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
          step.build_mode === "guided"
            ? "border-accent bg-accent-soft text-accent-ink"
            : "border-line text-ink-secondary hover:bg-surface-muted hover:text-ink"
        }`}
      >
        <User className="h-3 w-3" aria-hidden="true" />
        I&apos;ll build it
      </button>
      <button
        type="button"
        onClick={() => pick("generated")}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors ${
          step.build_mode === "generated"
            ? "border-accent bg-accent-soft text-accent-ink"
            : "border-line text-ink-secondary hover:bg-surface-muted hover:text-ink"
        }`}
      >
        <Bot className="h-3 w-3" aria-hidden="true" />
        Let AI build it
      </button>
    </div>
  );
}

function StepRow({ step, projectId }: { step: BuildPlanStepRead; projectId: string }) {
  const updateStatus = useUpdateStepStatus(projectId);
  const isDone = step.status === "completed";

  return (
    <li className="rounded-lg border border-line bg-surface-muted p-3">
      <div className="flex items-start gap-2.5">
        <button
          type="button"
          onClick={() =>
            updateStatus.mutate({
              stepId: step.id,
              status: step.status === "pending" ? "in_progress" : "completed",
            })
          }
          disabled={isDone || updateStatus.isPending}
          aria-label={isDone ? "Completed" : "Mark step progress"}
          className="mt-0.5 shrink-0 text-ink-muted transition-colors disabled:cursor-default hover:not-disabled:text-accent-ink"
        >
          {isDone ? (
            <CheckCircle2 className="h-4 w-4 text-success-ink" aria-hidden="true" />
          ) : (
            <Circle className={`h-4 w-4 ${step.status === "in_progress" ? "text-accent-ink" : ""}`} aria-hidden="true" />
          )}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className={`text-sm font-semibold ${isDone ? "text-ink-faint line-through" : "text-ink"}`}>
              {step.title}
            </p>
            {step.status === "in_progress" && <Badge variant="accent">In progress</Badge>}
          </div>
          <p className="mt-0.5 text-sm text-ink-muted">{step.description}</p>
          {!isDone && (
            <div className="mt-2">
              <BuildModePicker step={step} projectId={projectId} />
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

export function BuildPlanSection({ projectId }: { projectId: string }) {
  const { data: plan, isLoading, isError } = useBuildPlan(projectId);
  const [regenerating, setRegenerating] = useState(false);

  return (
    <section aria-labelledby="build-plan-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="build-plan-heading" className="flex items-center gap-2 text-sm font-semibold text-ink-secondary">
          <Hammer className="h-4 w-4" aria-hidden="true" />
          Build plan
        </h2>
        {plan && !regenerating && (
          <button
            type="button"
            onClick={() => setRegenerating(true)}
            className="inline-flex items-center gap-1.5 rounded-sm text-xs font-medium text-ink-muted hover:text-ink"
          >
            <RefreshCw className="h-3 w-3" aria-hidden="true" />
            Regenerate
          </button>
        )}
      </div>

      <div className="mt-3 rounded-lg border border-line bg-surface p-5">
        {isLoading && <p className="text-sm text-ink-muted">Loading build plan…</p>}

        {!isLoading && (isError || !plan) && (
          <GenerateBuildPlanForm projectId={projectId} regenerate={false} />
        )}

        {plan && regenerating && (
          <div className="flex flex-col gap-4">
            <GenerateBuildPlanForm projectId={projectId} regenerate />
            <button
              type="button"
              onClick={() => setRegenerating(false)}
              className="self-start text-xs font-medium text-ink-muted hover:text-ink"
            >
              Cancel
            </button>
          </div>
        )}

        {plan && !regenerating && (
          <div className="flex flex-col gap-4">
            <p className="text-sm leading-relaxed text-ink-secondary">{plan.summary}</p>

            {plan.recommended_stack.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {plan.recommended_stack.map((item) => (
                  <span
                    key={item.name}
                    title={item.reason}
                    className="rounded-full border border-line bg-surface-muted px-2.5 py-1 text-xs font-medium text-ink-secondary"
                  >
                    {item.name}
                  </span>
                ))}
              </div>
            )}

            <ol className="flex flex-col gap-2">
              {plan.steps.map((step) => (
                <StepRow key={step.id} step={step} projectId={projectId} />
              ))}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}
