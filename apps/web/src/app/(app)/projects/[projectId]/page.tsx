"use client";

import { useParams } from "next/navigation";

import { formatRelativeTime } from "@/lib/format";
import { useProject } from "@/hooks/useProjects";

/**
 * Project overview — deliberately minimal for now. The roadmap,
 * milestones, and mentoring surfaces this tab will eventually host are
 * later steps (ARCHITECTURE.md Section 7's curriculum/taxonomy tables
 * aren't built yet); this page is the workspace shell they'll attach
 * to, not a placeholder for its own sake.
 */
export default function ProjectOverviewPage() {
  const params = useParams<{ projectId: string }>();
  const { data: project } = useProject(params.projectId);

  if (!project) return null;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-700">About</h2>
        <p className="mt-2 text-sm text-slate-600">
          {project.description ?? "No description yet — add one from Settings."}
        </p>
        <p className="mt-4 text-xs text-slate-400">
          Created {formatRelativeTime(project.created_at)}
        </p>
      </div>

      <div className="rounded-lg border border-dashed border-slate-300 p-5 text-sm text-slate-500">
        The roadmap and mentoring workspace for this project will live here.
      </div>
    </div>
  );
}
