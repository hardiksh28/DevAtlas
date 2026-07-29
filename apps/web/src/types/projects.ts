// Mirrors apps/api/app/modules/projects/schemas.py — same convention as
// types/auth.ts: plain TS types, not a generated client, since this is
// the only frontend consuming the API today.

export type ProjectStatus = "active" | "archived" | "deleted";
export type ProjectColor = "slate" | "blue" | "green" | "amber" | "rose" | "violet";

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  // Flattened from the project's ProjectSettings row by the API's
  // ProjectRead.from_model — see apps/api/app/modules/projects/schemas.py.
  icon: string;
  color: ProjectColor;
  archived_at: string | null;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProjectSettings {
  project_id: string;
  icon: string;
  color: ProjectColor;
  settings: Record<string, unknown>;
  updated_at: string;
}

export interface RecentProjectEntry {
  project: Project;
  last_viewed_at: string;
}

export interface DashboardSummary {
  active_count: number;
  archived_count: number;
  recent_projects: RecentProjectEntry[];
}

export interface CreateProjectPayload {
  name: string;
  description?: string | null;
}

export interface UpdateProjectPayload {
  name?: string;
  description?: string | null;
}

export interface UpdateProjectSettingsPayload {
  icon?: string;
  color?: ProjectColor;
  settings?: Record<string, unknown>;
}

export interface ListProjectsParams {
  status?: ProjectStatus;
  limit?: number;
  offset?: number;
}
