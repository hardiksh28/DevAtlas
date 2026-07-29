"use client";

import { Eye, EyeOff } from "lucide-react";
import { forwardRef, useState, type InputHTMLAttributes } from "react";

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  /** Quiet guidance under the field (e.g. password requirements). */
  hint?: string;
  /** Inline validation error — announced via aria and shown in danger ink. */
  error?: string;
};

/**
 * Shared across every auth form (login/register/forgot/reset) and the
 * project forms — one source of truth for label + input + focus ring +
 * validation styling. `type="password"` fields get a visibility toggle
 * automatically. `forwardRef` so callers (e.g. the create-project
 * modal autofocusing its first field) can reach the underlying input.
 */
export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(function FormField(
  { label, id, hint, error, type, className, ...props },
  ref,
) {
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";
  const resolvedType = isPassword && visible ? "text" : type;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink-secondary">
        {label}
      </label>
      <div className="relative">
        <input
          ref={ref}
          id={id}
          type={resolvedType}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          className={`min-h-10 w-full rounded-md border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-faint transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0 ${
            error
              ? "border-danger/50 focus:border-danger focus:ring-danger/30"
              : "border-line-strong focus:border-accent focus:ring-accent/30"
          } ${isPassword ? "pr-11" : ""} ${className ?? ""}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-md text-ink-muted transition-colors hover:text-ink"
          >
            {visible ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        )}
      </div>
      {error ? (
        <p id={`${id}-error`} role="alert" className="text-sm text-danger-ink">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="text-xs text-ink-faint">
            {hint}
          </p>
        )
      )}
    </div>
  );
});
