"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "ui";

import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { EmptyState } from "@/components/projects/EmptyState";
import { ProjectCard } from "@/components/projects/ProjectCard";
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

  const { data, isLoading } = useProjects({ status, limit: PAGE_SIZE, offset });

  function selectTab(next: ProjectStatus) {
    setStatus(next);
    setOffset(0);
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Projects</h1>
        <Button onClick={() => setModalOpen(true)}>New project</Button>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => selectTab(tab.value)}
            className={`px-3 py-2 text-sm font-medium transition-colors ${
              status === tab.value
                ? "border-b-2 border-slate-900 text-slate-900"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {!isLoading && data && data.items.length === 0 && (
        <EmptyState
          title={status === "active" ? "No active projects" : "No archived projects"}
          description={
            status === "active"
              ? "Create a project to get started."
              : "Projects you archive will show up here."
          }
          action={
            status === "active" ? (
              <Button onClick={() => setModalOpen(true)}>Create a project</Button>
            ) : undefined
          }
        />
      )}

      {!isLoading && data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>
              {Math.min(offset + 1, data.total)}–{Math.min(offset + PAGE_SIZE, data.total)} of{" "}
              {data.total}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={offset + PAGE_SIZE >= data.total}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </div>
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
