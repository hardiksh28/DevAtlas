import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
};

/**
 * Shared across apps/web (and any future client) so button styling has
 * one source of truth instead of drifting per-page. This package is not
 * meant to become a full design system in V1 — just the handful of
 * primitives actually reused today. `danger` was added alongside the
 * project workspace's settings page (destructive actions: delete) —
 * every variant's colors are complete Tailwind class strings so a
 * consumer passing `className` for layout (width, margin) never has to
 * fight the variant's own colors for specificity.
 */
export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  const base =
    "rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-slate-900 text-white hover:bg-slate-700",
    secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200",
    danger: "bg-red-50 text-red-700 border border-red-200 hover:bg-red-100",
  };

  return <button className={`${base} ${variants[variant]} ${className ?? ""}`} {...props} />;
}
