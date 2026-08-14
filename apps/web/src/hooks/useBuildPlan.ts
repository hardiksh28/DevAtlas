"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { CURRENT_USER_QUERY_KEY } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api-client";
import {
  fetchBuildPlan,
  generateBuildPlan,
  updateStepMode,
  updateStepStatus,
} from "@/lib/build-plan-api";
import { getCompanionDisplayName } from "@/lib/companion";
import { useCompanionStore } from "@/store/useCompanionStore";
import type { BuildPlanRead, BuildPlanStepRead, StepBuildMode, StepStatus } from "@/types/build-plan";
import type { User } from "@/types/auth";

const buildPlanKey = (projectId: string) => ["buildPlan", projectId] as const;

export function useBuildPlan(projectId: string) {
  return useQuery({
    queryKey: buildPlanKey(projectId),
    queryFn: () => fetchBuildPlan(projectId),
    enabled: Boolean(projectId),
    // No plan yet is a normal, common 404 (ProjectDescriptionMissingError's
    // sibling case) — don't burn retries on it, same reasoning as useRoadmap.
    retry: false,
  });
}

export function useGenerateBuildPlan(projectId: string) {
  const queryClient = useQueryClient();
  const notify = useCompanionStore((s) => s.notify);
  return useMutation<BuildPlanRead, ApiError, string | null>({
    mutationFn: (additionalContext) => generateBuildPlan(projectId, additionalContext),
    onSuccess: (plan) => {
      queryClient.setQueryData(buildPlanKey(projectId), plan);
      // A generation call takes long enough that the learner may have
      // scrolled or tabbed away — the floating companion surfaces
      // completion the same way a background-task notification would,
      // rather than only the inline section update they might not see.
      const user = queryClient.getQueryData<User>(CURRENT_USER_QUERY_KEY);
      notify(`${getCompanionDisplayName(user?.companion_name)} finished your build plan`);
    },
  });
}

function patchStepInCache(
  queryClient: ReturnType<typeof useQueryClient>,
  projectId: string,
  step: BuildPlanStepRead,
) {
  queryClient.setQueryData<BuildPlanRead>(buildPlanKey(projectId), (plan) =>
    plan
      ? { ...plan, steps: plan.steps.map((s) => (s.id === step.id ? step : s)) }
      : plan,
  );
}

export function useUpdateStepMode(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<
    BuildPlanStepRead,
    ApiError,
    { stepId: string; buildMode: StepBuildMode }
  >({
    mutationFn: ({ stepId, buildMode }) => updateStepMode(projectId, stepId, buildMode),
    onSuccess: (step) => patchStepInCache(queryClient, projectId, step),
  });
}

export function useUpdateStepStatus(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<BuildPlanStepRead, ApiError, { stepId: string; status: StepStatus }>({
    mutationFn: ({ stepId, status }) => updateStepStatus(projectId, stepId, status),
    onSuccess: (step) => patchStepInCache(queryClient, projectId, step),
  });
}
