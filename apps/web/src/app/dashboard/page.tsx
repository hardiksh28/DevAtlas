"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Button } from "ui";

import { useCurrentUser, useLogout, useLogoutAll } from "@/hooks/useAuth";

/**
 * Demonstrates a protected page end to end:
 * 1. middleware.ts already redirected any visit with no auth cookie at
 *    all straight to /login before this component ever rendered.
 * 2. This component still calls the API (`useCurrentUser`) and treats a
 *    failure as "not authenticated" — covers the case middleware can't
 *    (a present-but-expired/invalid access token, or a refresh that
 *    itself failed) — matching apiFetch's own no-fallback-left 401
 *    behavior in lib/api-client.ts.
 *
 * Real feature pages don't need to repeat this redirect-on-error
 * boilerplate individually forever — once a second protected page
 * exists, this effect is the natural candidate to extract into a
 * `useRequireAuth()` hook. One page doesn't justify that abstraction yet.
 */
export default function DashboardPage() {
  const router = useRouter();
  const { data: user, isLoading, isError } = useCurrentUser();
  const logout = useLogout();
  const logoutAll = useLogoutAll();

  useEffect(() => {
    if (isError) {
      router.replace("/login");
    }
  }, [isError, router]);

  if (isLoading || isError) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-600">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => logout.mutate()} disabled={logout.isPending}>
            Log out
          </Button>
          <Button
            variant="secondary"
            onClick={() => logoutAll.mutate()}
            disabled={logoutAll.isPending}
          >
            Log out everywhere
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 p-4 text-sm text-slate-700">
        <p>
          Signed in as <span className="font-medium">{user?.display_name}</span> ({user?.email})
        </p>
        <p className="mt-1 text-slate-500">
          Email {user?.email_verified ? "verified" : "not yet verified"}
        </p>
      </div>
    </main>
  );
}
