"use client";

import { AlertCircle } from "lucide-react";
import { Button } from "ui";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retrying?: boolean;
}

/** Recovery state for failed queries — always offers a way forward. */
export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load this right now. Check your connection and try again.",
  onRetry,
  retrying = false,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-lg border border-line bg-surface px-6 py-12 text-center"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-danger-soft text-danger-ink">
        <AlertCircle className="h-5 w-5" aria-hidden="true" />
      </span>
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="max-w-sm text-sm text-ink-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} loading={retrying}>
          Try again
        </Button>
      )}
    </div>
  );
}
