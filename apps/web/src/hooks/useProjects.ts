"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api-client";
import {
  archiveProject,
  createProject,
  deleteProject,
  fetchDashboard,
  fetchProject,
  fetchProjectSettings,
  fetchRecentProjects,
  listProjects,
  restoreProject,
  updateProject,
  updateProjectSettings,
} from "@/lib/projects-api";
import type {
  CreateProjectPayload,
  ListProjectsParams,
  Project,
  ProjectSettings,
  UpdateProjectPayload,
  UpdateProjectSettingsPayload,
} from "@/types/projects";

// Every project-scoped query is nested under the "projects" key so a
// single `invalidateQueries({ queryKey: ["projects"] })` after any
// mutation below catches the list, the recent rail, and every
// individual project/settings query at once — the dashboard and
// project pages never show stale state after a create/rename/archive/
// delete/restore.
const projectsKey = ["projects"] as const;
const projectsListKey = (params: ListProjectsParams) => [...projectsKey, "list", params] as const;
const projectRecentKey = (limit: number) => [...projectsKey, "recent", limit] as const;
const projectKey = (projectId: string) => [...projectsKey, projectId] as const;
const projectSettingsKey = (projectId: string) => [...projectsKey, projectId, "settings"] as const;
const dashboardKey = ["dashboard"] as const;

export function useProjects(params: ListProjectsParams = {}) {
  return useQuery({
    queryKey: projectsListKey(params),
    queryFn: () => listProjects(params),
  });
}

export function useRecentProjects(limit = 5) {
  return useQuery({
    queryKey: projectRecentKey(limit),
    queryFn: () => fetchRecentProjects(limit),
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: dashboardKey,
    queryFn: fetchDashboard,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectKey(projectId),
    queryFn: () => fetchProject(projectId),
    enabled: Boolean(projectId),
  });
}

export function useProjectSettings(projectId: string) {
  return useQuery({
    queryKey: projectSettingsKey(projectId),
    queryFn: () => fetchProjectSettings(projectId),
    enabled: Boolean(projectId),
  });
}

function useInvalidateProjects() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: projectsKey });
    queryClient.invalidateQueries({ queryKey: dashboardKey });
  };
}

export function useCreateProject() {
  const invalidate = useInvalidateProjects();
  return useMutation<Project, ApiError, CreateProjectPayload>({
    mutationFn: createProject,
    onSuccess: invalidate,
  });
}

export function useUpdateProject(projectId: string) {
  const invalidate = useInvalidateProjects();
  return useMutation<Project, ApiError, UpdateProjectPayload>({
    mutationFn: (payload) => updateProject(projectId, payload),
    onSuccess: invalidate,
  });
}

export function useArchiveProject() {
  const invalidate = useInvalidateProjects();
  return useMutation<Project, ApiError, string>({
    mutationFn: archiveProject,
    onSuccess: invalidate,
  });
}

export function useRestoreProject() {
  const invalidate = useInvalidateProjects();
  return useMutation<Project, ApiError, string>({
    mutationFn: restoreProject,
    onSuccess: invalidate,
  });
}

export function useDeleteProject() {
  const invalidate = useInvalidateProjects();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteProject,
    onSuccess: invalidate,
  });
}

export function useUpdateProjectSettings(projectId: string) {
  const invalidate = useInvalidateProjects();
  return useMutation<ProjectSettings, ApiError, UpdateProjectSettingsPayload>({
    mutationFn: (payload) => updateProjectSettings(projectId, payload),
    onSuccess: invalidate,
  });
}
