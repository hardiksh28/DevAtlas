import type { ProjectColor } from "@/types/projects";

// Maps the closed `ProjectColor` enum (apps/api's
// `ck_project_settings_color` constraint) onto Tailwind's own color
// family names 1:1 — deliberate, so this table is the only place that
// can ever drift from the backend's closed set, and adding a color is
// a two-line change (here + the DB CHECK constraint), not a design
// decision made twice. These are the one sanctioned exception to the
// "semantic tokens only" rule: they're user-chosen content colors
// (project identity), not UI chrome, so each carries its own dark
// variant here.
export const PROJECT_COLOR_CLASSES: Record<
  ProjectColor,
  { bg: string; text: string; swatch: string }
> = {
  slate: {
    bg: "bg-slate-100 dark:bg-slate-500/20",
    text: "text-slate-700 dark:text-slate-300",
    swatch: "bg-slate-400",
  },
  blue: {
    bg: "bg-blue-100 dark:bg-blue-500/20",
    text: "text-blue-700 dark:text-blue-300",
    swatch: "bg-blue-500",
  },
  green: {
    bg: "bg-green-100 dark:bg-green-500/20",
    text: "text-green-700 dark:text-green-300",
    swatch: "bg-green-500",
  },
  amber: {
    bg: "bg-amber-100 dark:bg-amber-500/20",
    text: "text-amber-700 dark:text-amber-300",
    swatch: "bg-amber-500",
  },
  rose: {
    bg: "bg-rose-100 dark:bg-rose-500/20",
    text: "text-rose-700 dark:text-rose-300",
    swatch: "bg-rose-500",
  },
  violet: {
    bg: "bg-violet-100 dark:bg-violet-500/20",
    text: "text-violet-700 dark:text-violet-300",
    swatch: "bg-violet-500",
  },
};

export const PROJECT_COLORS: ProjectColor[] = ["slate", "blue", "green", "amber", "rose", "violet"];
