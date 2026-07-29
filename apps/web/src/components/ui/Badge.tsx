import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "neutral" | "accent" | "success" | "outline";
  className?: string;
}

/** Small status label — project state, "Available now", "Coming soon". */
export function Badge({ children, variant = "neutral", className }: BadgeProps) {
  const variants = {
    neutral: "bg-surface-muted text-ink-secondary",
    accent: "bg-accent-soft text-accent-ink",
    success: "bg-success-soft text-success-ink",
    outline: "border border-line text-ink-muted",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${variants[variant]} ${className ?? ""}`}
    >
      {children}
    </span>
  );
}
