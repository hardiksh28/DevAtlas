import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

/**
 * Shared across apps/web (and any future client) so button styling has
 * one source of truth instead of drifting per-page. This package is not
 * meant to become a full design system in V1 — just the handful of
 * primitives actually reused today.
 */
export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  const base = "rounded-md px-4 py-2 text-sm font-medium transition-colors";
  const variants = {
    primary: "bg-slate-900 text-white hover:bg-slate-700",
    secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200",
  };

  return <button className={`${base} ${variants[variant]} ${className ?? ""}`} {...props} />;
}
