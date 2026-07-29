import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "md" | "sm";
  /** Shows a spinner and disables the button while a mutation runs. */
  loading?: boolean;
};

/**
 * Shared across apps/web (and any future client) so button styling has
 * one source of truth instead of drifting per-page. Colors are the
 * app's semantic theme tokens (see apps/web/tailwind.config.ts) —
 * every variant is a complete class string so a consumer passing
 * `className` for layout (width, margin) never fights the variant's
 * own colors for specificity. Minimum hit target is 40px on `md`.
 */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors " +
    "disabled:opacity-60 disabled:cursor-not-allowed select-none";
  const sizes = {
    md: "min-h-10 px-4 py-2 text-sm",
    sm: "min-h-8 px-3 py-1.5 text-sm",
  };
  const variants = {
    primary: "bg-accent text-white hover:bg-accent-hover disabled:hover:bg-accent",
    secondary:
      "border border-line bg-surface text-ink hover:bg-surface-muted disabled:hover:bg-surface",
    ghost: "text-ink-secondary hover:bg-surface-muted hover:text-ink",
    danger:
      "border border-danger/30 bg-danger-soft text-danger-ink hover:bg-danger hover:text-white hover:border-danger disabled:hover:bg-danger-soft disabled:hover:text-danger-ink",
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${className ?? ""}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="h-4 w-4 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
          <path
            d="M12 2a10 10 0 0 1 10 10"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
