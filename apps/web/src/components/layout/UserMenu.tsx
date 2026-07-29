"use client";

import { LogOut, Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useLogout } from "@/hooks/useAuth";
import type { User } from "@/types/auth";

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || "?";
}

/** Avatar button + small dropdown: identity, settings link, sign out. */
export function UserMenu({ user }: { user: User }) {
  const router = useRouter();
  const logout = useLogout();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
        className="flex h-10 w-10 items-center justify-center rounded-md transition-colors hover:bg-surface-muted"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent-ink">
          {initials(user.display_name)}
        </span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-40 mt-1 w-56 rounded-lg border border-line bg-surface p-1.5 shadow-overlay"
        >
          <div className="border-b border-line px-3 pb-2.5 pt-1.5">
            <p className="truncate text-sm font-medium text-ink">{user.display_name}</p>
            <p className="truncate text-xs text-ink-muted">{user.email}</p>
          </div>
          <Link
            href="/settings"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="mt-1 flex min-h-10 items-center gap-2.5 rounded-md px-3 py-2 text-sm text-ink-secondary transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <Settings className="h-4 w-4" aria-hidden="true" />
            Settings
          </Link>
          <button
            type="button"
            role="menuitem"
            disabled={logout.isPending}
            onClick={() =>
              logout.mutate(undefined, { onSuccess: () => router.push("/login") })
            }
            className="flex min-h-10 w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-ink-secondary transition-colors hover:bg-surface-muted hover:text-ink disabled:opacity-60"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            {logout.isPending ? "Signing out…" : "Sign out"}
          </button>
        </div>
      )}
    </div>
  );
}
