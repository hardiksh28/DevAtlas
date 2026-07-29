import type { ProjectColor } from "@/types/projects";

// Maps the closed `ProjectColor` enum (apps/api's
// `ck_project_settings_color` constraint) onto Tailwind's own color
// family names 1:1 — deliberate, so this table is the only place that
// can ever drift from the backend's closed set, and adding a color is
// a two-line change (here + the DB CHECK constraint), not a design
// decision made twice.
export const PROJECT_COLOR_CLASSES: Record<ProjectColor, { bg: string; text: string; ring: string }> = {
  slate: { bg: "bg-slate-100", text: "text-slate-700", ring: "ring-slate-200" },
  blue: { bg: "bg-blue-100", text: "text-blue-700", ring: "ring-blue-200" },
  green: { bg: "bg-green-100", text: "text-green-700", ring: "ring-green-200" },
  amber: { bg: "bg-amber-100", text: "text-amber-700", ring: "ring-amber-200" },
  rose: { bg: "bg-rose-100", text: "text-rose-700", ring: "ring-rose-200" },
  violet: { bg: "bg-violet-100", text: "text-violet-700", ring: "ring-violet-200" },
};

export const PROJECT_COLORS: ProjectColor[] = ["slate", "blue", "green", "amber", "rose", "violet"];
