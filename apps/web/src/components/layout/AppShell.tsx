"use client";

import { Menu, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { DevAtlasLogo, DevAtlasMark } from "@/components/brand/Logo";
import { CompanionWidget } from "@/components/companion/CompanionWidget";
import { SidebarNav } from "@/components/layout/SidebarNav";
import { UserMenu } from "@/components/layout/UserMenu";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useProject } from "@/hooks/useProjects";
import type { User } from "@/types/auth";

const COLLAPSE_KEY = "devatlas:sidebar-collapsed";

/** Topbar context: section title, or a Projects → name breadcrumb when
 * inside a project. Lives here (not per-page) so every protected page
 * gets it for free. */
function TopbarContext() {
  const pathname = usePathname();
  const params = useParams<{ projectId?: string }>();
  // useProject is disabled when projectId is absent, so this costs
  // nothing outside project routes.
  const { data: project } = useProject(params.projectId ?? "");

  if (params.projectId) {
    return (
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-sm">
        <Link
          href="/projects"
          className="rounded-sm text-ink-muted transition-colors hover:text-ink"
        >
          Projects
        </Link>
        <span aria-hidden="true" className="text-ink-faint">
          /
        </span>
        <span className="truncate font-medium text-ink">{project?.name ?? "…"}</span>
      </nav>
    );
  }

  const titles: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/projects": "Projects",
    "/settings": "Settings",
  };
  const title = Object.entries(titles).find(
    ([path]) => pathname === path || pathname.startsWith(`${path}/`),
  )?.[1];

  return <span className="truncate text-sm font-medium text-ink">{title ?? ""}</span>;
}

/**
 * Shared chrome for every authenticated page: collapsible desktop
 * sidebar, mobile drawer, and a topbar with page context, theme toggle,
 * and the user menu. Pages render inside a readable max-width container
 * they control themselves.
 */
export function AppShell({ user, children }: { user: User; children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Restore the collapse preference after mount (SSR can't read
  // localStorage; a brief expanded flash beats a hydration mismatch).
  useEffect(() => {
    setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      localStorage.setItem(COLLAPSE_KEY, prev ? "0" : "1");
      return !prev;
    });
  }

  // Close the drawer on any route change.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen bg-canvas">
      {/* Desktop sidebar */}
      <aside
        className={`sticky top-0 hidden h-screen shrink-0 flex-col border-r border-line bg-surface transition-[width] duration-200 lg:flex ${
          collapsed ? "w-16" : "w-60"
        }`}
      >
        <div
          className={`flex h-16 items-center border-b border-line ${
            collapsed ? "justify-center px-2" : "justify-between px-4"
          }`}
        >
          <Link href="/dashboard" aria-label="DevAtlas dashboard" className="rounded-md">
            {collapsed ? (
              <DevAtlasMark className="h-6 w-6 text-ink" />
            ) : (
              <DevAtlasLogo size={24} />
            )}
          </Link>
          {!collapsed && (
            <button
              type="button"
              onClick={toggleCollapsed}
              aria-label="Collapse sidebar"
              className="flex h-10 w-10 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
            >
              <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>
        <SidebarNav collapsed={collapsed} />
        {collapsed && (
          <div className="flex justify-center border-t border-line py-3">
            <button
              type="button"
              onClick={toggleCollapsed}
              aria-label="Expand sidebar"
              className="flex h-10 w-10 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
            >
              <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div
            className="absolute inset-0 bg-ink/40"
            onClick={() => setDrawerOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-line bg-surface shadow-overlay">
            <div className="flex h-16 items-center justify-between border-b border-line px-4">
              <DevAtlasLogo size={24} />
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close navigation"
                className="flex h-10 w-10 items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            <SidebarNav onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b border-line bg-canvas/95 px-4 backdrop-blur-sm sm:px-6">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
            className="flex h-10 w-10 items-center justify-center rounded-md text-ink-secondary transition-colors hover:bg-surface-muted hover:text-ink lg:hidden"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <Link href="/dashboard" aria-label="DevAtlas dashboard" className="rounded-md lg:hidden">
            <DevAtlasMark className="h-6 w-6 text-ink" />
          </Link>
          <div className="ml-1 min-w-0 flex-1">
            <TopbarContext />
          </div>
          <ThemeToggle />
          <UserMenu user={user} />
        </header>
        <main className="flex-1">{children}</main>
      </div>

      <CompanionWidget />
    </div>
  );
}
