import { apiFetch } from "@/lib/api-client";
import type { ExperienceLevel, MilestoneDetailRead, RoadmapRead } from "@/types/roadmap";

export interface GenerateRoadmapPayload {
  stack: string;
  stack_version: string;
  experience_level: ExperienceLevel;
}

export function fetchRoadmap(projectId: string): Promise<RoadmapRead> {
  return apiFetch<RoadmapRead>(`/v1/projects/${projectId}/roadmap`);
}

/** Generates the roadmap, or regenerates it in place (progress-preserving
 * merge) if one already exists — same endpoint either way. */
export function generateRoadmap(
  projectId: string,
  payload: GenerateRoadmapPayload,
): Promise<RoadmapRead> {
  return apiFetch<RoadmapRead>(`/v1/projects/${projectId}/roadmap/generate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
