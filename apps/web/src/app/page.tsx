"use client";

import { useQuery } from "@tanstack/react-query";
import { Button } from "ui";

import { apiFetch } from "@/lib/api-client";
import { useSessionStore } from "@/store/useSessionStore";

interface HealthResponse {
  status: string;
  environment: string;
}

export default function HomePage() {
  const activeProjectId = useSessionStore((s) => s.activeProjectId);
  const setActiveProject = useSessionStore((s) => s.setActiveProject);

  // Smoke test for the whole stack: web -> api -> (implicitly) config.
  // If this renders "ok", CORS, the API container, and env wiring all work.
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<HealthResponse>("/health"),
  });

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-semibold text-slate-900">AI Engineering Workspace</h1>

      <p className="text-sm text-slate-600">
        API health:{" "}
        {isLoading ? "checking…" : isError ? "unreachable" : `${data?.status} (${data?.environment})`}
      </p>

      <Button
        variant={activeProjectId ? "secondary" : "primary"}
        onClick={() => setActiveProject(activeProjectId ? null : "demo-project")}
      >
        {activeProjectId ? "Clear active project" : "Set demo active project"}
      </Button>
    </main>
  );
}
