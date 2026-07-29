"use client";

import { ArrowRight, Circle, CheckCircle2, FolderPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "ui";

import { CreateProjectModal } from "@/components/projects/CreateProjectModal";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { PageHeader } from "@/components/ui/PageHeader";
import { CardSkeleton, Skeleton } from "@/components/ui/Skeleton";
import { useCurrentUser } from "@/hooks/useAuth";
import { useDashboard } from "@/hooks/useProjects";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <p className="text-sm text-ink-muted">{label}</p>
      <p className="mt-1 font-mono text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

/** Honest onboarding checklist: only "create a project" is a real,
 * completable step today — the rest are labeled as upcoming modules. */
function NextSteps({ hasProject, onCreate }: { hasProject: boolean; onCreate: () => void }) {
  return (
    <section aria-labelledby="next-steps-heading">
      <h2 id="next-steps-heading" className="mb-3 text-sm font-semibold text-ink-secondary">
        Your next steps
      </h2>
      <ol className="divide-y divide-line rounded-lg border border-line bg-surface">
        <li className="flex items-center gap-3 p-4">
          {hasProject ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-success-ink" aria-hidden="true" />
          ) : (
            <Circle className="h-5 w-5 shrink-0 text-ink-faint" aria-hidden="true" />
          )}
          <div className="min-w-0 flex-1">
            <p className={`text-sm font-medium ${hasProject ? "text-ink-muted" : "text-ink"}`}>
              Create a project
            </p>
            <p className="text-xs text-ink-muted">
              Everything in DevAtlas — roadmap, lessons, mentoring — attaches to a project.
            </p>
          </div>
          {!hasProject && (
            <Button size="sm" variant="secondary" onClick={onCreate}>
              Create
            </Button>
          )}
        </li>
        <li className="flex items-center gap-3 p-4">
          <Circle className="h-5 w-5 shrink-0 text-ink-faint" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink-muted">Add documentation</p>
            <p className="text-xs text-ink-muted">
              Ground your mentor in your project&apos;s docs and repository.
            </p>
          </div>
          <Badge variant="outline">Coming next</Badge>
        </li>
        <li className="flex items-center gap-3 p-4">
          <Circle className="h-5 w-5 shrink-0 text-ink-faint" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink-muted">Generate a roadmap</p>
            <p className="text-xs text-ink-muted">
              Get a milestone plan from idea to deployment.
            </p>
          </div>
          <Badge variant="outline">Coming next</Badge>
        </li>
      </ol>
    </section>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const { data, isLoading, isError, refetch, isRefetching } = useDashboard();
  const [modalOpen, setModalOpen] = useState(false);

  const hasAnyProjects = (data?.active_count ?? 0) + (data?.archived_count ?? 0) > 0;
  const firstName = user?.display_name.split(" ")[0];

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-6 sm:px-6 sm:py-8">
      <PageHeader
        title={firstName ? `Welcome back, ${firstName}` : "Welcome back"}
        description={
          hasAnyProjects
            ? "Keep building — your projects are below."
            : "Your engineering workspace starts with a project."
        }
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <FolderPlus className="h-4 w-4" aria-hidden="true" />
            New project
          </Button>
        }
      />

      {isError && (
        <ErrorState
          title="Couldn't load your dashboard"
          onRetry={() => refetch()}
          retrying={isRefetching}
        />
      )}

      {isLoading && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:max-w-md">
            <Skeleton className="h-[92px]" />
            <Skeleton className="h-[92px]" />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </>
      )}

      {!isLoading && !isError && data && (
        <>
          {hasAnyProjects && (
            <div className="grid grid-cols-2 gap-4 sm:max-w-md">
              <StatCard label="Active projects" value={data.active_count} />
              <StatCard label="Archived" value={data.archived_count} />
            </div>
          )}

          <section aria-labelledby="recent-heading">
            <div className="mb-3 flex items-center justify-between">
              <h2 id="recent-heading" className="text-sm font-semibold text-ink-secondary">
                Recent projects
              </h2>
              {hasAnyProjects && (
                <Link
                  href="/projects"
                  className="inline-flex items-center gap-1 rounded-sm text-sm text-accent-ink hover:underline"
                >
                  View all
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              )}
            </div>

            {!hasAnyProjects && (
              <EmptyState
                icon={FolderPlus}
                title="Your engineering workspace starts with a project"
                description="Pick something you genuinely want to build — an API, an agent, a retrieval service. DevAtlas will help you take it from idea to production."
                action={
                  <Button onClick={() => setModalOpen(true)}>Create your first project</Button>
                }
                hint="Next, you'll add documentation and get a learning roadmap as those modules land."
              />
            )}

            {hasAnyProjects && data.recent_projects.length === 0 && (
              <EmptyState
                title="Nothing viewed yet"
                description="Open a project and it'll show up here."
              />
            )}

            {data.recent_projects.length > 0 && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.recent_projects.map((entry) => (
                  <ProjectCard key={entry.project.id} project={entry.project} />
                ))}
              </div>
            )}
          </section>

          <NextSteps hasProject={hasAnyProjects} onCreate={() => setModalOpen(true)} />
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
