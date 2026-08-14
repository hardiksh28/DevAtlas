import { apiFetch } from "@/lib/api-client";
import type { BuildPlanRead, BuildPlanStepRead, StepBuildMode, StepStatus } from "@/types/build-plan";

export function fetchBuildPlan(projectId: string): Promise<BuildPlanRead> {
  return apiFetch<BuildPlanRead>(`/v1/projects/${projectId}/build-plan`);
}

export function generateBuildPlan(
  projectId: string,
  additionalContext: string | null,
): Promise<BuildPlanRead> {
  return apiFetch<BuildPlanRead>(`/v1/projects/${projectId}/build-plan/generate`, {
    method: "POST",
    body: JSON.stringify({ additional_context: additionalContext }),
  });
}

export function updateStepMode(
  projectId: string,
  stepId: string,
  buildMode: StepBuildMode,
): Promise<BuildPlanStepRead> {
  return apiFetch<BuildPlanStepRead>(`/v1/projects/${projectId}/build-plan/steps/${stepId}/mode`, {
    method: "PATCH",
    body: JSON.stringify({ build_mode: buildMode }),
  });
}

export function updateStepStatus(
  projectId: string,
  stepId: string,
  status: StepStatus,
): Promise<BuildPlanStepRead> {
  return apiFetch<BuildPlanStepRead>(`/v1/projects/${projectId}/build-plan/steps/${stepId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
