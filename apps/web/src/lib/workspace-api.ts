import { apiFetch } from "@/lib/api-client";
import type {
  CreateWorkspaceFilePayload,
  RenameWorkspaceFilePayload,
  UpdateWorkspaceFileContentPayload,
  UpdateWorkspaceLayoutPayload,
  WorkspaceFileDetail,
  WorkspaceFileListResponse,
  WorkspaceLayout,
} from "@/types/workspace";

function base(projectId: string): string {
  return `/v1/projects/${projectId}/workspace`;
}

export function fetchWorkspaceTree(projectId: string): Promise<WorkspaceFileListResponse> {
  return apiFetch<WorkspaceFileListResponse>(`${base(projectId)}/tree`);
}

export function fetchWorkspaceFile(projectId: string, fileId: string): Promise<WorkspaceFileDetail> {
  return apiFetch<WorkspaceFileDetail>(`${base(projectId)}/files/${fileId}`);
}

export function createWorkspaceFile(
  projectId: string,
  payload: CreateWorkspaceFilePayload,
): Promise<WorkspaceFileDetail> {
  return apiFetch<WorkspaceFileDetail>(`${base(projectId)}/files`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateWorkspaceFileContent(
  projectId: string,
  fileId: string,
  payload: UpdateWorkspaceFileContentPayload,
): Promise<WorkspaceFileDetail> {
  return apiFetch<WorkspaceFileDetail>(`${base(projectId)}/files/${fileId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function renameWorkspaceFile(
  projectId: string,
  fileId: string,
  payload: RenameWorkspaceFilePayload,
): Promise<WorkspaceFileDetail> {
  return apiFetch<WorkspaceFileDetail>(`${base(projectId)}/files/${fileId}/path`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteWorkspaceFile(projectId: string, fileId: string): Promise<void> {
  return apiFetch<void>(`${base(projectId)}/files/${fileId}`, { method: "DELETE" });
}

export function fetchWorkspaceLayout(projectId: string): Promise<WorkspaceLayout> {
  return apiFetch<WorkspaceLayout>(`${base(projectId)}/layout`);
}

export function updateWorkspaceLayout(
  projectId: string,
  payload: UpdateWorkspaceLayoutPayload,
): Promise<WorkspaceLayout> {
  return apiFetch<WorkspaceLayout>(`${base(projectId)}/layout`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
