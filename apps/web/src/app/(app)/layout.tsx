"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Button } from "ui";

import { Sidebar } from "@/components/layout/Sidebar";
import { useCurrentUser, useLogout } from "@/hooks/useAuth";

/**
 * The "Workspace Layout" — shared chrome for every authenticated page
 * (dashboard, project list, a project's own pages). Centralizes the
 * auth-redirect-on-error handling that dashboard/page.tsx used to do
 * on its own (see that page's old comment); now that a second and
 * third protected page exist, this is the shared home for it instead
 * of copy-pasting the effect per page.
 *
 * middleware.ts already redirected any visit with no auth cookie at
 * all before this ever renders — this covers the case it can't (a
 * present-but-expired/invalid access token).
 */
export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();

  useEffect(() => {
    if (isError) router.replace("/login");
  }, [isError, router]);

  if (isLoading || isError) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-600">Loading…</p>
      </main>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-end gap-3 border-b border-slate-200 bg-white px-6 py-3">
          <span className="text-sm text-slate-600">{user?.display_name}</span>
          <Button variant="secondary" onClick={() => logout.mutate()} disabled={logout.isPending}>
            Log out
          </Button>
        </header>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
