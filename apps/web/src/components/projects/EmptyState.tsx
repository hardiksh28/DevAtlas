import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

/** Shared empty-state shell — dashboard (no projects at all), the
 * project list (no projects in the current status filter), and the
 * recent-projects rail (nothing viewed yet) all render one of these
 * instead of an empty grid. */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-slate-300 px-6 py-16 text-center">
      <p className="text-sm font-medium text-slate-900">{title}</p>
      <p className="max-w-sm text-sm text-slate-500">{description}</p>
      {action}
    </div>
  );
}
