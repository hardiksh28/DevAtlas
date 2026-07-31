"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  // Fires only when the root layout itself throws, so — unlike
  // app/error.tsx — it can't rely on that layout's <html>/<body> or
  // providers (fonts, ThemeProvider) and has to redeclare its own.
  return (
    <html lang="en">
      <body>
        <div
          role="alert"
          style={{
            display: "flex",
            minHeight: "100vh",
            alignItems: "center",
            justifyContent: "center",
            padding: "1rem",
            fontFamily: "system-ui, sans-serif",
            textAlign: "center",
          }}
        >
          <div>
            <p style={{ fontWeight: 600, marginBottom: "0.5rem" }}>Something went wrong</p>
            <p style={{ color: "#666", marginBottom: "1rem" }}>
              An unexpected error occurred. Please try again.
            </p>
            <button
              onClick={reset}
              style={{
                border: "1px solid #ccc",
                borderRadius: "0.375rem",
                padding: "0.5rem 1rem",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
