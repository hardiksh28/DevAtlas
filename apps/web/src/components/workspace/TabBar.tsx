"use client";

import { X } from "lucide-react";

import { useWorkspaceTree } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";

function basename(path: string): string {
  return path.split("/").pop() ?? path;
}

export function TabBar({ projectId }: { projectId: string }) {
  const { data: tree } = useWorkspaceTree(projectId);
  const openTabIds = useWorkspaceStore((s) => s.openTabIds);
  const activeTabId = useWorkspaceStore((s) => s.activeTabId);
  const setActiveTab = useWorkspaceStore((s) => s.setActiveTab);
  const closeTab = useWorkspaceStore((s) => s.closeTab);
  const dirtyContent = useWorkspaceStore((s) => s.dirtyContent);

  const pathById = new Map((tree?.items ?? []).map((f) => [f.id, f.path]));

  if (openTabIds.length === 0) {
    return (
      <div className="flex h-10 items-center border-b border-line px-3 text-xs text-ink-muted">
        No files open — pick one from the explorer.
      </div>
    );
  }

  return (
    <div role="tablist" className="flex h-10 items-stretch overflow-x-auto border-b border-line">
      {openTabIds.map((fileId) => {
        const path = pathById.get(fileId) ?? "…";
        const active = fileId === activeTabId;
        const dirty = fileId in dirtyContent;
        return (
          <div
            key={fileId}
            role="tab"
            aria-selected={active}
            className={`flex shrink-0 items-center border-r border-line text-sm transition-colors ${
              active ? "bg-surface text-ink" : "text-ink-muted hover:bg-surface-muted hover:text-ink"
            }`}
          >
            <button
              type="button"
              onClick={() => setActiveTab(fileId)}
              title={path}
              className="flex min-w-0 items-center gap-2 py-2 pl-3 pr-1.5"
            >
              <span className="max-w-[10rem] truncate">{basename(path)}</span>
              {dirty && (
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ink-faint" aria-hidden="true" />
              )}
            </button>
            <button
              type="button"
              onClick={() => closeTab(fileId)}
              aria-label={`Close ${path}`}
              className="mr-2 rounded-sm p-1 text-ink-faint hover:bg-surface-muted hover:text-ink"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
