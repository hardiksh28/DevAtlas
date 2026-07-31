// Mirrors apps/api/app/modules/curriculum/schemas.py — the Lesson Panel's
// data shape. Only the fields the workspace's Lesson Panel actually
// renders; roadmap generation/regeneration lives on the project's own
// (separate, pre-existing) curriculum surface, not the workspace.

export type ExperienceLevel = "beginner" | "intermediate" | "advanced";
export type MilestoneStatus = "locked" | "available" | "in_progress" | "completed";

export interface Exercise {
  prompt: string;
  hint: string | null;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface LessonContent {
  explanation: string;
  key_points: string[];
  exercises: Exercise[];
  quiz: QuizQuestion[];
}

export interface MilestoneRead {
  id: string;
  roadmap_id: string;
  concept_id: string;
  sequence_index: number;
  status: MilestoneStatus;
  title: string;
  estimated_minutes: number;
  has_content: boolean;
  content_version: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MilestoneDetailRead extends MilestoneRead {
  lesson_content: LessonContent | null;
}

export interface RoadmapRead {
  id: string;
  project_id: string;
  stack: string;
  stack_version: string;
  experience_level: ExperienceLevel;
  status: "active" | "archived";
  version: number;
  estimated_total_minutes: number;
  milestones: MilestoneRead[];
  created_at: string;
  updated_at: string;
}
