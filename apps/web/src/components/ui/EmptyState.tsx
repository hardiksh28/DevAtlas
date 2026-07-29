import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: ReactNode;
  /** Extra context below the action, e.g. what happens after the CTA. */
  hint?: string;
}

/**
 * Shared empty-state shell — dashboard (no projects at all), the
 * project list (no projects in the current status filter), and the
 * recent-projects rail (nothing viewed yet) all render one of these
 * instead of an empty grid.
 */
export function EmptyState({ title, description, icon: Icon, action, hint }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-line-strong px-6 py-14 text-center">
      {Icon && (
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-muted text-ink-muted">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      )}
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="max-w-sm text-sm text-ink-muted">{description}</p>
      {action && <div className="mt-1">{action}</div>}
      {hint && <p className="max-w-sm text-xs text-ink-faint">{hint}</p>}
    </div>
  );
}
