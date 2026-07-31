"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api-client";
import { generateDiagram, listDiagrams } from "@/lib/diagrams-api";
import type { DiagramListResponse, DiagramRead, GenerateDiagramRequest } from "@/types/diagrams";

const diagramsKey = (projectId: string) => ["diagrams", projectId] as const;

export function useDiagrams(projectId: string) {
  return useQuery({
    queryKey: diagramsKey(projectId),
    queryFn: () => listDiagrams(projectId),
    enabled: Boolean(projectId),
  });
}

export function useGenerateDiagram(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<DiagramRead, ApiError, GenerateDiagramRequest>({
    mutationFn: (payload) => generateDiagram(projectId, payload),
    onSuccess: (diagram) => {
      queryClient.setQueryData(diagramsKey(projectId), (existing: DiagramListResponse | undefined) => {
        const items = [diagram, ...(existing?.items ?? [])];
        return { items, total: (existing?.total ?? 0) + 1, limit: existing?.limit ?? 20, offset: 0 };
      });
    },
  });
}
