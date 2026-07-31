"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api-client";
import {
  createWorkspaceFile,
  deleteWorkspaceFile,
  fetchWorkspaceFile,
  fetchWorkspaceLayout,
  fetchWorkspaceTree,
  renameWorkspaceFile,
  updateWorkspaceFileContent,
  updateWorkspaceLayout,
} from "@/lib/workspace-api";
import type {
  CreateWorkspaceFilePayload,
  RenameWorkspaceFilePayload,
  UpdateWorkspaceFileContentPayload,
  UpdateWorkspaceLayoutPayload,
  WorkspaceFileDetail,
  WorkspaceFileMeta,
  WorkspaceLayout,
} from "@/types/workspace";

// Nested the same way useProjects.ts nests under "projects" — one
// invalidation root per project's workspace.
const workspaceKey = (projectId: string) => ["workspace", projectId] as const;
const treeKey = (projectId: string) => [...workspaceKey(projectId), "tree"] as const;
const fileKey = (projectId: string, fileId: string) =>
  [...workspaceKey(projectId), "file", fileId] as const;
const layoutKey = (projectId: string) => [...workspaceKey(projectId), "layout"] as const;

export function useWorkspaceTree(projectId: string) {
  return useQuery({
    queryKey: treeKey(projectId),
    queryFn: () => fetchWorkspaceTree(projectId),
    enabled: Boolean(projectId),
  });
}

export function useWorkspaceFile(projectId: string, fileId: string | null) {
  return useQuery({
    queryKey: fileKey(projectId, fileId ?? ""),
    queryFn: () => fetchWorkspaceFile(projectId, fileId as string),
    enabled: Boolean(projectId) && Boolean(fileId),
  });
}

export function useWorkspaceLayout(projectId: string) {
  return useQuery({
    queryKey: layoutKey(projectId),
    queryFn: () => fetchWorkspaceLayout(projectId),
    enabled: Boolean(projectId),
  });
}

// Patches the one row this file already occupies in the cached tree
// list, rather than invalidating and refetching the whole tree — the
// tree only needs to move when a file is created/renamed/deleted, not
// on every autosave.
function patchTreeEntry(
  queryClient: ReturnType<typeof useQueryClient>,
  projectId: string,
  file: WorkspaceFileMeta,
) {
  queryClient.setQueryData(treeKey(projectId), (existing: { items: WorkspaceFileMeta[] } | undefined) => {
    if (!existing) return existing;
    const withoutFile = existing.items.filter((item) => item.id !== file.id);
    return { items: [...withoutFile, file].sort((a, b) => a.path.localeCompare(b.path)) };
  });
}

export function useCreateWorkspaceFile(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<WorkspaceFileDetail, ApiError, CreateWorkspaceFilePayload>({
    mutationFn: (payload) => createWorkspaceFile(projectId, payload),
    onSuccess: (file) => {
      queryClient.setQueryData(fileKey(projectId, file.id), file);
      patchTreeEntry(queryClient, projectId, file);
    },
  });
}

export function useUpdateWorkspaceFileContent(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    WorkspaceFileDetail,
    ApiError,
    { fileId: string; payload: UpdateWorkspaceFileContentPayload }
  >({
    mutationFn: ({ fileId, payload }) => updateWorkspaceFileContent(projectId, fileId, payload),
    onSuccess: (file) => {
      queryClient.setQueryData(fileKey(projectId, file.id), file);
      patchTreeEntry(queryClient, projectId, file);
    },
  });
}

export function useRenameWorkspaceFile(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    WorkspaceFileDetail,
    ApiError,
    { fileId: string; payload: RenameWorkspaceFilePayload }
  >({
    mutationFn: ({ fileId, payload }) => renameWorkspaceFile(projectId, fileId, payload),
    onSuccess: (file) => {
      queryClient.setQueryData(fileKey(projectId, file.id), file);
      patchTreeEntry(queryClient, projectId, file);
    },
  });
}

export function useDeleteWorkspaceFile(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (fileId) => deleteWorkspaceFile(projectId, fileId),
    onSuccess: (_data, fileId) => {
      queryClient.removeQueries({ queryKey: fileKey(projectId, fileId) });
      queryClient.setQueryData(treeKey(projectId), (existing: { items: WorkspaceFileMeta[] } | undefined) => {
        if (!existing) return existing;
        return { items: existing.items.filter((item) => item.id !== fileId) };
      });
      // A deleted file may have been pruned from open_tabs/active_tab_id
      // server-side (see workspace/service.py's delete_file) — the
      // layout cache can't patch that locally, so refetch it.
      queryClient.invalidateQueries({ queryKey: layoutKey(projectId) });
    },
  });
}

export function useUpdateWorkspaceLayout(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<WorkspaceLayout, ApiError, UpdateWorkspaceLayoutPayload>({
    mutationFn: (payload) => updateWorkspaceLayout(projectId, payload),
    onSuccess: (layout) => {
      queryClient.setQueryData(layoutKey(projectId), layout);
    },
  });
}
