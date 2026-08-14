"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api-client";
import {
  fetchMilestone,
  fetchRoadmap,
  generateMilestoneContent,
  generateRoadmap,
  type GenerateRoadmapPayload,
} from "@/lib/roadmap-api";
import { fetchStacks } from "@/lib/taxonomy-api";
import type { MilestoneDetailRead, RoadmapRead } from "@/types/roadmap";

const roadmapKey = (projectId: string) => ["roadmap", projectId] as const;
const milestoneKey = (projectId: string, milestoneId: string) =>
  [...roadmapKey(projectId), "milestone", milestoneId] as const;

export function useRoadmap(projectId: string) {
  return useQuery({
    queryKey: roadmapKey(projectId),
    queryFn: () => fetchRoadmap(projectId),
    enabled: Boolean(projectId),
    // No roadmap yet is a normal, common 404 (see curriculum's
    // RoadmapNotFoundError) — don't burn retries on it.
    retry: false,
  });
}

export function useMilestone(projectId: string, milestoneId: string | null) {
  return useQuery({
    queryKey: milestoneKey(projectId, milestoneId ?? ""),
    queryFn: () => fetchMilestone(projectId, milestoneId as string),
    enabled: Boolean(projectId) && Boolean(milestoneId),
  });
}

export function useGenerateMilestoneContent(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<MilestoneDetailRead, ApiError, string>({
    mutationFn: (milestoneId) => generateMilestoneContent(projectId, milestoneId),
    onSuccess: (milestone) => {
      queryClient.setQueryData(milestoneKey(projectId, milestone.id), milestone);
    },
  });
}

/** Available (stack, stack_version) pairs from the seeded taxonomy —
 * drives the generate-roadmap form's dropdown so it can never offer a
 * combination the curriculum engine has no concepts for. */
export function useStacks() {
  return useQuery({
    queryKey: ["taxonomy", "stacks"] as const,
    queryFn: fetchStacks,
    staleTime: 5 * 60_000, // curated content, changes rarely
  });
}

export function useGenerateRoadmap(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<RoadmapRead, ApiError, GenerateRoadmapPayload>({
    mutationFn: (payload) => generateRoadmap(projectId, payload),
    onSuccess: (roadmap) => {
      queryClient.setQueryData(roadmapKey(projectId), roadmap);
    },
  });
}
