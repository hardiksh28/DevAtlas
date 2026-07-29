"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "ui";

import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { EmptyState } from "@/components/projects/EmptyState";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { useDashboard } from "@/hooks/useProjects";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { data, isLoading } = useDashboard();
  const [modalOpen, setModalOpen] = useState(false);

  const hasAnyProjects = (data?.active_count ?? 0) + (data?.archived_count ?? 0) > 0;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <Button onClick={() => setModalOpen(true)}>New project</Button>
      </div>

      {!isLoading && data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <StatCard label="Active projects" value={data.active_count} />
          <StatCard label="Archived projects" value={data.archived_count} />
        </div>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Recent projects</h2>

        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}

        {!isLoading && !hasAnyProjects && (
          <EmptyState
            title="No projects yet"
            description="Create your first project to start building something real, with a mentor guiding you the whole way."
            action={<Button onClick={() => setModalOpen(true)}>Create a project</Button>}
          />
        )}

        {!isLoading && hasAnyProjects && data && data.recent_projects.length === 0 && (
          <EmptyState
            title="Nothing viewed yet"
            description="Open a project and it'll show up here."
          />
        )}

        {!isLoading && data && data.recent_projects.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.recent_projects.map((entry) => (
              <ProjectCard key={entry.project.id} project={entry.project} />
            ))}
          </div>
        )}
      </div>

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
