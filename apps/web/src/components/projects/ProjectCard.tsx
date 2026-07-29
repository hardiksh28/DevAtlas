import Link from "next/link";

import { PROJECT_COLOR_CLASSES } from "@/components/projects/colors";
import { Badge } from "@/components/ui/Badge";
import { formatRelativeTime } from "@/lib/format";
import type { Project } from "@/types/projects";

export function ProjectCard({ project }: { project: Project }) {
  const colors = PROJECT_COLOR_CLASSES[project.color];

  return (
    <Link
      href={`/projects/${project.id}`}
      className="flex flex-col gap-3 rounded-lg border border-line bg-surface p-4 transition-colors hover:border-line-strong"
    >
      <div className="flex items-start justify-between gap-2">
        <span
          aria-hidden="true"
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-lg ${colors.bg}`}
        >
          {project.icon}
        </span>
        {project.status === "archived" && <Badge>Archived</Badge>}
      </div>

      <div>
        <h3 className="truncate text-sm font-semibold text-ink" title={project.name}>
          {project.name}
        </h3>
        {project.description && (
          <p className="mt-1 line-clamp-2 text-sm text-ink-muted">{project.description}</p>
        )}
      </div>

      <p className="mt-auto font-mono text-xs text-ink-faint">
        Updated {formatRelativeTime(project.updated_at)}
      </p>
    </Link>
  );
}
