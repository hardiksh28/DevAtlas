"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { PROJECT_COLOR_CLASSES, PROJECT_COLORS } from "@/components/projects/colors";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { TextArea } from "@/components/ui/TextArea";
import {
  useArchiveProject,
  useDeleteProject,
  useProject,
  useRestoreProject,
  useUpdateProject,
  useUpdateProjectSettings,
} from "@/hooks/useProjects";

// Curated identity glyphs (stored by the API as the project's icon
// string — user-chosen content, not UI iconography).
const PROJECT_ICONS = ["📁", "🧭", "🤖", "📚", "🔍", "💬", "🗺️", "🧪", "📊", "🚀"];

export default function ProjectSettingsPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const { data: project } = useProject(params.projectId);

  const updateProject = useUpdateProject(params.projectId);
  const updateSettings = useUpdateProjectSettings(params.projectId);
  const archiveProject = useArchiveProject();
  const restoreProject = useRestoreProject();
  const deleteProject = useDeleteProject();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    if (project) {
      setName(project.name);
      setDescription(project.description ?? "");
    }
  }, [project]);

  if (!project) return null;

  function handleSaveDetails(event: React.FormEvent) {
    event.preventDefault();
    updateProject.mutate({ name, description: description.trim() || null });
  }

  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="details-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="details-heading" className="text-sm font-semibold text-ink-secondary">
          Details
        </h2>
        <form onSubmit={handleSaveDetails} className="mt-4 flex max-w-lg flex-col gap-4">
          <FormField
            id="settings-name"
            label="Name"
            required
            maxLength={200}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <TextArea
            id="settings-description"
            label="Description"
            optional
            rows={3}
            maxLength={4000}
            value={description}
            hint="What the project should do, and for whom — the future roadmap generator works from this."
            onChange={(e) => setDescription(e.target.value)}
          />
          {updateProject.isError && (
            <p role="alert" className="text-sm text-danger-ink">
              {updateProject.error.message}
            </p>
          )}
          <div className="flex items-center gap-3">
            <Button
              type="submit"
              loading={updateProject.isPending}
              disabled={name.trim().length === 0}
            >
              Save changes
            </Button>
            {updateProject.isSuccess && !updateProject.isPending && (
              <p role="status" className="text-sm text-success-ink">
                Changes saved.
              </p>
            )}
          </div>
        </form>
      </section>

      <section aria-labelledby="appearance-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="appearance-heading" className="text-sm font-semibold text-ink-secondary">
          Appearance
        </h2>
        <p className="mt-1 text-sm text-ink-muted">
          The icon and color shown on this project&apos;s cards throughout the workspace.
        </p>

        <p className="mt-4 text-xs font-medium uppercase tracking-wide text-ink-faint">Icon</p>
        <div className="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label="Project icon">
          {PROJECT_ICONS.map((icon) => {
            const selected = project.icon === icon;
            return (
              <button
                key={icon}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-label={`Icon ${icon}`}
                disabled={updateSettings.isPending}
                onClick={() => updateSettings.mutate({ icon })}
                className={`flex h-10 w-10 items-center justify-center rounded-md border text-lg transition-colors ${
                  selected
                    ? "border-accent bg-accent-soft"
                    : "border-line hover:bg-surface-muted"
                }`}
              >
                {icon}
              </button>
            );
          })}
        </div>

        <p className="mt-5 text-xs font-medium uppercase tracking-wide text-ink-faint">Color</p>
        <div className="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label="Project color">
          {PROJECT_COLORS.map((color) => {
            const classes = PROJECT_COLOR_CLASSES[color];
            const selected = project.color === color;
            return (
              <button
                key={color}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-label={`Color ${color}`}
                disabled={updateSettings.isPending}
                onClick={() => updateSettings.mutate({ color })}
                className={`flex h-10 w-10 items-center justify-center rounded-md border transition-colors ${
                  selected ? "border-accent bg-accent-soft" : "border-line hover:bg-surface-muted"
                }`}
              >
                <span className={`h-5 w-5 rounded-full ${classes.swatch}`} aria-hidden="true" />
              </button>
            );
          })}
        </div>
        {updateSettings.isError && (
          <p role="alert" className="mt-3 text-sm text-danger-ink">
            {updateSettings.error.message}
          </p>
        )}
      </section>

      <section aria-labelledby="archive-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="archive-heading" className="text-sm font-semibold text-ink-secondary">
          {project.status === "archived" ? "Restore" : "Archive"}
        </h2>
        <p className="mt-1 max-w-lg text-sm text-ink-muted">
          {project.status === "archived"
            ? "Bring this project back to your active workspace."
            : "Hide this project from your active workspace without deleting anything. You can restore it any time."}
        </p>
        {(archiveProject.isError || restoreProject.isError) && (
          <p role="alert" className="mt-2 text-sm text-danger-ink">
            {archiveProject.error?.message ?? restoreProject.error?.message}
          </p>
        )}
        <div className="mt-4">
          {project.status === "active" ? (
            <Button
              variant="secondary"
              loading={archiveProject.isPending}
              onClick={() => archiveProject.mutate(params.projectId)}
            >
              Archive project
            </Button>
          ) : (
            <Button
              variant="secondary"
              loading={restoreProject.isPending}
              onClick={() => restoreProject.mutate(params.projectId)}
            >
              Restore project
            </Button>
          )}
        </div>
      </section>

      <section
        aria-labelledby="danger-heading"
        className="rounded-lg border border-danger/30 bg-surface p-5"
      >
        <h2 id="danger-heading" className="text-sm font-semibold text-danger-ink">
          Danger zone
        </h2>
        <p className="mt-1 max-w-lg text-sm text-ink-muted">
          Deleting removes this project from your workspace. It can be restored from your account
          for a limited time.
        </p>
        <div className="mt-4">
          <Button variant="danger" onClick={() => setDeleteOpen(true)}>
            Delete project
          </Button>
        </div>
      </section>

      <ConfirmDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={() =>
          deleteProject.mutate(params.projectId, {
            onSuccess: () => router.push("/projects"),
          })
        }
        title={`Delete "${project.name}"?`}
        description="The project will be removed from your workspace. You can restore it later from your account."
        confirmLabel="Delete project"
        destructive
        pending={deleteProject.isPending}
        error={deleteProject.isError ? deleteProject.error.message : null}
      />
    </div>
  );
}
