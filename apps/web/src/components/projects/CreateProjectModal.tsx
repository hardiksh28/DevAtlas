"use client";

import { useEffect, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { Dialog } from "@/components/ui/Dialog";
import { TextArea } from "@/components/ui/TextArea";
import { useCreateProject } from "@/hooks/useProjects";

interface CreateProjectModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (projectId: string) => void;
}

export function CreateProjectModal({ open, onClose, onCreated }: CreateProjectModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const createProject = useCreateProject();
  const { reset } = createProject;

  // Fresh form each time the dialog opens.
  useEffect(() => {
    if (open) {
      setName("");
      setDescription("");
      reset();
    }
  }, [open, reset]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    createProject.mutate(
      { name, description: description.trim() || null },
      { onSuccess: (project) => onCreated(project.id) },
    );
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Create a project"
      description="Pick something you actually want to exist — the best learning projects solve a problem you care about."
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <FormField
          id="project-name"
          label="Name"
          required
          maxLength={200}
          autoFocus
          value={name}
          placeholder="e.g. Support-ticket triage agent"
          onChange={(e) => setName(e.target.value)}
        />
        <TextArea
          id="project-description"
          label="Description"
          optional
          rows={3}
          maxLength={4000}
          value={description}
          placeholder="What should it do, and for whom?"
          hint="A concrete goal helps your future roadmap — you can change everything later."
          onChange={(e) => setDescription(e.target.value)}
        />

        {createProject.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {createProject.error.message}
          </p>
        )}

        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={createProject.isPending}
            disabled={name.trim().length === 0}
          >
            Create project
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
