import Link from "next/link";

import { PROJECT_COLOR_CLASSES } from "@/components/projects/colors";
import { formatRelativeTime } from "@/lib/format";
import type { Project } from "@/types/projects";

export function ProjectCard({ project }: { project: Project }) {
  const colors = PROJECT_COLOR_CLASSES[project.color];

  return (
    <Link
      href={`/projects/${project.id}`}
      className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 transition-colors hover:border-slate-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-lg ${colors.bg}`}
        >
          {project.icon}
        </span>
        {project.status === "archived" && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
            Archived
          </span>
        )}
      </div>

      <div>
        <h3 className="truncate text-sm font-semibold text-slate-900">{project.name}</h3>
        {project.description && (
          <p className="mt-1 line-clamp-2 text-sm text-slate-500">{project.description}</p>
        )}
      </div>

      <p className="mt-auto text-xs text-slate-400">Updated {formatRelativeTime(project.updated_at)}</p>
    </Link>
  );
}
