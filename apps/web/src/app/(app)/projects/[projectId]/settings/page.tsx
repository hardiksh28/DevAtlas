"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { PROJECT_COLOR_CLASSES, PROJECT_COLORS } from "@/components/projects/colors";
import {
  useArchiveProject,
  useDeleteProject,
  useProject,
  useRestoreProject,
  useUpdateProject,
  useUpdateProjectSettings,
} from "@/hooks/useProjects";

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

  function handleDelete() {
    if (!window.confirm(`Delete "${project?.name}"? You can restore it later from your account.`)) {
      return;
    }
    deleteProject.mutate(params.projectId, { onSuccess: () => router.push("/projects") });
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-700">Details</h2>
        <form onSubmit={handleSaveDetails} className="mt-4 flex flex-col gap-4">
          <FormField
            id="settings-name"
            label="Name"
            required
            maxLength={200}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="flex flex-col gap-1">
            <label htmlFor="settings-description" className="text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              id="settings-description"
              rows={3}
              maxLength={4000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </div>
          {updateProject.isError && (
            <p className="text-sm text-red-600">{updateProject.error.message}</p>
          )}
          <div>
            <Button type="submit" disabled={updateProject.isPending || name.trim().length === 0}>
              {updateProject.isPending ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </form>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-700">Appearance</h2>
        <p className="mt-1 text-sm text-slate-500">Shown on project cards throughout the workspace.</p>
        <div className="mt-4 flex gap-2">
          {PROJECT_COLORS.map((color) => {
            const classes = PROJECT_COLOR_CLASSES[color];
            const selected = project.color === color;
            return (
              <button
                key={color}
                type="button"
                aria-label={color}
                aria-pressed={selected}
                disabled={updateSettings.isPending}
                onClick={() => updateSettings.mutate({ color })}
                className={`h-8 w-8 rounded-full ${classes.bg} ${
                  selected ? "ring-2 ring-offset-2 ring-slate-900" : ""
                }`}
              />
            );
          })}
        </div>
      </section>

      <section className="rounded-lg border border-red-200 bg-red-50 p-5">
        <h2 className="text-sm font-semibold text-red-800">Danger zone</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {project.status === "active" && (
            <Button
              variant="secondary"
              disabled={archiveProject.isPending}
              onClick={() => archiveProject.mutate(params.projectId)}
            >
              Archive project
            </Button>
          )}
          {project.status === "archived" && (
            <Button
              variant="secondary"
              disabled={restoreProject.isPending}
              onClick={() => restoreProject.mutate(params.projectId)}
            >
              Restore project
            </Button>
          )}
          <Button variant="danger" disabled={deleteProject.isPending} onClick={handleDelete}>
            Delete project
          </Button>
        </div>
      </section>
    </div>
  );
}
