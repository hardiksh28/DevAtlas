"use client";

import Link from "next/link";
import { useParams, usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { PROJECT_COLOR_CLASSES } from "@/components/projects/colors";
import { useProject } from "@/hooks/useProjects";

/**
 * Project-scoped chrome: icon/name header + Overview/Settings tabs.
 * Nested one level below app/(app)/layout.tsx (which already handles
 * the Sidebar and the "am I logged in" check) — this layer only adds
 * what's specific to being inside one project.
 */
export default function ProjectLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ projectId: string }>();
  const pathname = usePathname();
  const router = useRouter();
  const { data: project, isLoading, isError } = useProject(params.projectId);

  if (isError) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <p className="text-sm text-slate-600">
          This project doesn&apos;t exist or you don&apos;t have access to it.{" "}
          <button onClick={() => router.push("/projects")} className="font-medium underline">
            Back to projects
          </button>
        </p>
      </div>
    );
  }

  if (isLoading || !project) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <p className="text-sm text-slate-500">Loading…</p>
      </div>
    );
  }

  const colors = PROJECT_COLOR_CLASSES[project.color];
  const basePath = `/projects/${project.id}`;
  const tabs = [
    { href: basePath, label: "Overview", active: pathname === basePath },
    { href: `${basePath}/settings`, label: "Settings", active: pathname.endsWith("/settings") },
  ];

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-8">
      <div className="flex items-center gap-3">
        <span className={`flex h-10 w-10 items-center justify-center rounded-md text-xl ${colors.bg}`}>
          {project.icon}
        </span>
        <div>
          <h1 className="text-xl font-semibold text-slate-900">{project.name}</h1>
          {project.status === "archived" && (
            <span className="text-xs font-medium text-slate-500">Archived</span>
          )}
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className={`px-3 py-2 text-sm font-medium transition-colors ${
              tab.active
                ? "border-b-2 border-slate-900 text-slate-900"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {children}
    </div>
  );
}
