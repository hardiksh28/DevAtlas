"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { DevAtlasMark } from "@/components/brand/Logo";
import { AppShell } from "@/components/layout/AppShell";
import { useCurrentUser } from "@/hooks/useAuth";

/**
 * The "Workspace Layout" — shared chrome for every authenticated page
 * (dashboard, project list, a project's own pages, settings) via
 * AppShell. Centralizes the auth-redirect-on-error handling.
 *
 * middleware.ts already redirected any visit with no auth cookie at
 * all before this ever renders — this covers the case it can't (a
 * present-but-expired/invalid access token).
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (isError) router.replace("/login");
  }, [isError, router]);

  if (isLoading || isError || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-canvas">
        <div className="flex flex-col items-center gap-3 text-ink-muted">
          <DevAtlasMark className="h-8 w-8 animate-pulse" aria-hidden="true" />
          <p className="text-sm">Loading your workspace…</p>
        </div>
      </main>
    );
  }

  return <AppShell user={user}>{children}</AppShell>;
}
