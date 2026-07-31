"use client";

import { useEffect } from "react";

import { ErrorState } from "@/components/ui/ErrorState";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-muted px-4">
      <div className="w-full max-w-sm">
        <ErrorState
          title="Something went wrong"
          message="An unexpected error occurred. You can try again, or head back to the dashboard if it keeps happening."
          onRetry={reset}
        />
      </div>
    </div>
  );
}
