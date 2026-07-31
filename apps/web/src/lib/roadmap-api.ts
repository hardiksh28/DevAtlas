import { apiFetch } from "@/lib/api-client";
import type { MilestoneDetailRead, RoadmapRead } from "@/types/roadmap";

export function fetchRoadmap(projectId: string): Promise<RoadmapRead> {
  return apiFetch<RoadmapRead>(`/v1/projects/${projectId}/roadmap`);
}

export function fetchMilestone(
  projectId: string,
  milestoneId: string,
): Promise<MilestoneDetailRead> {
  return apiFetch<MilestoneDetailRead>(
    `/v1/projects/${projectId}/roadmap/milestones/${milestoneId}`,
  );
}

export function generateMilestoneContent(
  projectId: string,
  milestoneId: string,
): Promise<MilestoneDetailRead> {
  return apiFetch<MilestoneDetailRead>(
    `/v1/projects/${projectId}/roadmap/milestones/${milestoneId}/content`,
    { method: "POST" },
  );
}
