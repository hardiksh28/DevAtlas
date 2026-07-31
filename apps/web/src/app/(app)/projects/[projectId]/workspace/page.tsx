"use client";

import { Monitor } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";

// Matches AppShell's `lg` breakpoint for desktop-only chrome. The
// Monaco/panel/terminal layout has no responsive treatment of its own,
// so below this width it's gated behind a notice instead — checked here
// (not just hidden via CSS) so mobile visitors never trigger Monaco's
// bundle load or the workspace's data fetching for a UI they can't use.
const DESKTOP_MEDIA_QUERY = "(min-width: 1024px)";

function useIsDesktop(): boolean {
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(DESKTOP_MEDIA_QUERY);
    setIsDesktop(mql.matches);
    const onChange = (e: MediaQueryListEvent) => setIsDesktop(e.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isDesktop;
}

export default function WorkspacePage() {
  const params = useParams<{ projectId: string }>();
  const isDesktop = useIsDesktop();

  if (!isDesktop) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-accent-ink">
          <Monitor className="h-6 w-6" aria-hidden="true" />
        </span>
        <p className="text-sm font-semibold text-ink">The workspace needs a larger screen</p>
        <p className="max-w-sm text-sm text-ink-muted">
          The in-browser editor, file tree, and terminal need more room than a phone or narrow
          tablet can offer. Open this project on a laptop or desktop to continue.
        </p>
      </div>
    );
  }

  return <WorkspaceShell projectId={params.projectId} />;
}
