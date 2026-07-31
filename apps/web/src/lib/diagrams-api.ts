import { apiFetch } from "@/lib/api-client";
import type { DiagramListResponse, DiagramRead, GenerateDiagramRequest } from "@/types/diagrams";

export function listDiagrams(
  projectId: string,
  limit = 20,
  offset = 0,
): Promise<DiagramListResponse> {
  return apiFetch<DiagramListResponse>(
    `/v1/projects/${projectId}/diagrams?limit=${limit}&offset=${offset}`,
  );
}

export function generateDiagram(
  projectId: string,
  payload: GenerateDiagramRequest,
): Promise<DiagramRead> {
  return apiFetch<DiagramRead>(`/v1/projects/${projectId}/diagrams`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
