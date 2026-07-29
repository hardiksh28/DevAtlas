"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { useCreateProject } from "@/hooks/useProjects";

interface CreateProjectModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (projectId: string) => void;
}

/**
 * Hand-rolled overlay, not a dialog/portal library — package.json has
 * none yet (no Radix, no shadcn), and this is the only modal in the
 * app so far. Revisit if a second, more complex modal shows up and
 * reimplementing focus-trap/escape/outside-click by hand starts
 * costing more than a dependency would.
 */
export function CreateProjectModal({ open, onClose, onCreated }: CreateProjectModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const nameInputRef = useRef<HTMLInputElement>(null);
  const createProject = useCreateProject();

  useEffect(() => {
    if (!open) return;
    setName("");
    setDescription("");
    createProject.reset();
    nameInputRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!open) return null;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    createProject.mutate(
      { name, description: description.trim() || null },
      { onSuccess: (project) => onCreated(project.id) },
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-project-title"
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="create-project-title" className="text-lg font-semibold text-slate-900">
          Create a project
        </h2>
        <p className="mt-1 text-sm text-slate-600">Give it a name — you can change everything later.</p>

        <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-4">
          <FormField
            id="project-name"
            label="Name"
            ref={nameInputRef}
            required
            maxLength={200}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <div className="flex flex-col gap-1">
            <label htmlFor="project-description" className="text-sm font-medium text-slate-700">
              Description <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              id="project-description"
              rows={3}
              maxLength={4000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            />
          </div>

          {createProject.isError && (
            <p className="text-sm text-red-600">{createProject.error.message}</p>
          )}

          <div className="mt-1 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createProject.isPending || name.trim().length === 0}>
              {createProject.isPending ? "Creating…" : "Create project"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
