import { apiFetch } from "@/lib/api-client";
import type {
  CreateProjectPayload,
  DashboardSummary,
  ListProjectsParams,
  Project,
  ProjectListResponse,
  ProjectSettings,
  RecentProjectEntry,
  UpdateProjectPayload,
  UpdateProjectSettingsPayload,
} from "@/types/projects";

function queryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listProjects(params: ListProjectsParams = {}): Promise<ProjectListResponse> {
  return apiFetch<ProjectListResponse>(
    `/v1/projects${queryString({ status: params.status, limit: params.limit, offset: params.offset })}`,
  );
}

export function fetchRecentProjects(limit = 5): Promise<RecentProjectEntry[]> {
  return apiFetch<RecentProjectEntry[]>(`/v1/projects/recent${queryString({ limit })}`);
}

export function fetchDashboard(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/v1/dashboard");
}

export function fetchProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${projectId}`);
}

export function createProject(payload: CreateProjectPayload): Promise<Project> {
  return apiFetch<Project>("/v1/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(projectId: string, payload: UpdateProjectPayload): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${projectId}/archive`, { method: "POST" });
}

export function restoreProject(projectId: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${projectId}/restore`, { method: "POST" });
}

export function deleteProject(projectId: string): Promise<void> {
  return apiFetch<void>(`/v1/projects/${projectId}`, { method: "DELETE" });
}

export function fetchProjectSettings(projectId: string): Promise<ProjectSettings> {
  return apiFetch<ProjectSettings>(`/v1/projects/${projectId}/settings`);
}

export function updateProjectSettings(
  projectId: string,
  payload: UpdateProjectSettingsPayload,
): Promise<ProjectSettings> {
  return apiFetch<ProjectSettings>(`/v1/projects/${projectId}/settings`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
