// Mirrors apps/api/app/modules/build_plan/schemas.py exactly.

export type StepStatus = "pending" | "in_progress" | "completed";
export type StepBuildMode = "guided" | "generated";

export interface RecommendedStackItem {
  name: string;
  reason: string;
}

export interface BuildPlanStepRead {
  id: string;
  build_plan_id: string;
  sequence_index: number;
  title: string;
  description: string;
  status: StepStatus;
  build_mode: StepBuildMode | null;
  created_at: string;
  updated_at: string;
}

export interface BuildPlanRead {
  id: string;
  project_id: string;
  summary: string;
  recommended_stack: RecommendedStackItem[];
  version: number;
  steps: BuildPlanStepRead[];
  created_at: string;
  updated_at: string;
}
