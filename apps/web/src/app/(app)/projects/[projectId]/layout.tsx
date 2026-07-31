"use client";

import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { PROJECT_COLOR_CLASSES } from "@/components/projects/colors";
import { Badge } from "@/components/ui/Badge";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useProject } from "@/hooks/useProjects";

/**
 * Project-scoped chrome: icon/name header + Overview/Settings tabs.
 * Nested one level below app/(app)/layout.tsx (which already handles
 * the AppShell and the "am I logged in" check) — this layer only adds
 * what's specific to being inside one project.
 */
export default function ProjectLayout({ children }: { children: ReactNode }) {
  const params = useParams<{ projectId: string }>();
  const pathname = usePathname();
  const { data: project, isLoading, isError } = useProject(params.projectId);

  if (isError) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        <ErrorState
          title="Project not found"
          message="This project doesn't exist or you don't have access to it."
        />
        <div className="mt-4 text-center">
          <Link href="/projects" className="rounded-sm text-sm font-medium text-accent-ink hover:underline">
            Back to projects
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading || !project) {
    return (
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
        <div className="flex items-center gap-3">
          <Skeleton className="h-11 w-11" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-3 w-64" />
          </div>
        </div>
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const colors = PROJECT_COLOR_CLASSES[project.color];
  const basePath = `/projects/${project.id}`;

  // The workspace is a full-bleed VS-Code-style surface (Monaco, file
  // tree, resizable panels) — it needs the full viewport, not this
  // layout's padded max-w-5xl reading column + tab strip. AppShell's
  // <main> has no padding of its own, so skipping this wrapper is the
  // only change needed to go full-bleed.
  if (pathname.endsWith("/workspace")) {
    return <>{children}</>;
  }

  const tabs = [
    { href: basePath, label: "Overview", active: pathname === basePath },
    { href: `${basePath}/settings`, label: "Settings", active: pathname.endsWith("/settings") },
  ];

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-xl ${colors.bg}`}
        >
          {project.icon}
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-xl font-semibold tracking-tight text-ink">
              {project.name}
            </h1>
            {project.status === "archived" && <Badge>Archived</Badge>}
          </div>
          {project.description && (
            <p className="mt-0.5 line-clamp-2 max-w-2xl text-sm text-ink-muted">
              {project.description}
            </p>
          )}
        </div>
      </div>

      <div className="flex gap-1 border-b border-line">
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={tab.active ? "page" : undefined}
            className={`-mb-px min-h-10 px-3 py-2 text-sm font-medium transition-colors ${
              tab.active
                ? "border-b-2 border-accent text-ink"
                : "border-b-2 border-transparent text-ink-muted hover:text-ink"
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
