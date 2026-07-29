"use client";

import { Archive, FolderPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "ui";

import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { PageHeader } from "@/components/ui/PageHeader";
import { CardSkeleton } from "@/components/ui/Skeleton";
import { useProjects } from "@/hooks/useProjects";
import type { ProjectStatus } from "@/types/projects";

const PAGE_SIZE = 12;
const TABS: { value: ProjectStatus; label: string }[] = [
  { value: "active", label: "Active" },
  { value: "archived", label: "Archived" },
];

export default function ProjectsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<ProjectStatus>("active");
  const [offset, setOffset] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, isError, refetch, isRefetching } = useProjects({
    status,
    limit: PAGE_SIZE,
    offset,
  });

  function selectTab(next: ProjectStatus) {
    setStatus(next);
    setOffset(0);
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <PageHeader
        title="Projects"
        description="Everything you're building with DevAtlas."
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <FolderPlus className="h-4 w-4" aria-hidden="true" />
            New project
          </Button>
        }
      />

      <div role="tablist" aria-label="Project status" className="flex gap-1 border-b border-line">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            role="tab"
            aria-selected={status === tab.value}
            onClick={() => selectTab(tab.value)}
            className={`-mb-px min-h-10 px-3 py-2 text-sm font-medium transition-colors ${
              status === tab.value
                ? "border-b-2 border-accent text-ink"
                : "border-b-2 border-transparent text-ink-muted hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isError && (
        <ErrorState
          title="Couldn't load projects"
          onRetry={() => refetch()}
          retrying={isRefetching}
        />
      )}

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}

      {!isLoading && !isError && data && data.items.length === 0 && (
        <EmptyState
          icon={status === "active" ? FolderPlus : Archive}
          title={status === "active" ? "No active projects" : "No archived projects"}
          description={
            status === "active"
              ? "Create a project to start building — your roadmap and mentoring will attach to it."
              : "Projects you archive will show up here. Archiving hides a project without deleting anything."
          }
          action={
            status === "active" ? (
              <Button onClick={() => setModalOpen(true)}>Create a project</Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          {data.total > PAGE_SIZE && (
            <div className="flex items-center justify-between text-sm text-ink-muted">
              <span className="font-mono text-xs">
                {Math.min(offset + 1, data.total)}–{Math.min(offset + PAGE_SIZE, data.total)} of{" "}
                {data.total}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={offset + PAGE_SIZE >= data.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <CreateProjectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(projectId) => {
          setModalOpen(false);
          router.push(`/projects/${projectId}`);
        }}
      />
    </div>
  );
}
