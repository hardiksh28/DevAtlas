import { BookOpen, Code2, MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/Badge";

/**
 * An honest preview of the DevAtlas learning environment — static
 * panels sketching the lesson/roadmap area, code surface, mentor rail,
 * and progress indicator. Nothing here is interactive or pretends to
 * be; it exists to make the product direction tangible while those
 * modules are built.
 */
export function WorkspacePreview() {
  return (
    <section aria-labelledby="workspace-preview-heading">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="workspace-preview-heading" className="text-sm font-semibold text-ink-secondary">
          The workspace you&apos;re heading toward
        </h2>
        <Badge variant="outline">Preview — in development</Badge>
      </div>
      <p className="mt-1 max-w-2xl text-sm text-ink-muted">
        Once documentation ingestion and roadmap generation land, this project opens into a full
        learning environment:
      </p>

      <div className="mt-4 grid gap-3 rounded-xl border border-dashed border-line-strong p-3 sm:p-4 lg:grid-cols-[1fr_1.4fr_1fr]">
        {/* Lesson / roadmap panel */}
        <div className="rounded-lg border border-line bg-surface p-4">
          <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-faint">
            <BookOpen className="h-3.5 w-3.5" />
            Lesson · Roadmap
          </p>
          <div className="mt-3 space-y-2">
            <div className="h-2.5 w-3/4 rounded bg-surface-muted" />
            <div className="h-2.5 w-full rounded bg-surface-muted" />
            <div className="h-2.5 w-5/6 rounded bg-surface-muted" />
            <div className="mt-4 h-2.5 w-2/3 rounded bg-surface-muted" />
            <div className="h-2.5 w-4/5 rounded bg-surface-muted" />
          </div>
          <p className="mt-4 text-xs text-ink-muted">
            Short lessons appear beside the milestone that needs them.
          </p>
        </div>

        {/* Code area */}
        <div className="rounded-lg border border-line bg-surface p-4">
          <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-faint">
            <Code2 className="h-3.5 w-3.5" />
            Your code
          </p>
          <div className="mt-3 space-y-2 font-mono">
            <div className="h-2.5 w-1/2 rounded bg-accent-soft" />
            <div className="ml-4 h-2.5 w-2/3 rounded bg-surface-muted" />
            <div className="ml-4 h-2.5 w-3/4 rounded bg-surface-muted" />
            <div className="ml-8 h-2.5 w-1/2 rounded bg-surface-muted" />
            <div className="ml-4 h-2.5 w-1/3 rounded bg-surface-muted" />
            <div className="h-2.5 w-1/4 rounded bg-surface-muted" />
          </div>
          <p className="mt-4 text-xs text-ink-muted">
            You write it. The mentor reviews it against what you&apos;re learning.
          </p>
        </div>

        {/* Mentor panel + progress */}
        <div className="flex flex-col gap-3">
          <div className="flex-1 rounded-lg border border-line bg-surface p-4">
            <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-faint">
              <MessageSquare className="h-3.5 w-3.5" />
              Mentor
            </p>
            <div className="mt-3 space-y-2">
              <div className="h-2.5 w-full rounded bg-surface-muted" />
              <div className="h-2.5 w-5/6 rounded bg-surface-muted" />
            </div>
            <p className="mt-4 text-xs text-ink-muted">
              Progressive hints — questions first, answers only when earned.
            </p>
          </div>
          <div className="rounded-lg border border-line bg-surface p-4">
            <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Progress</p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-muted">
              <div className="h-full w-1/3 rounded-full bg-success" />
            </div>
            <p className="mt-2 text-xs text-ink-muted">Milestones tracked as you complete them.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
