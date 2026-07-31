"use client";

import { useWorkspaceStore } from "@/store/useWorkspaceStore";

/** Saved/Unsaved — driven by the store's per-file dirty buffer, which
 * is cleared the moment EditorPane's debounced autosave succeeds. No
 * separate "Saving…" state: with an ~800ms debounce there's nothing
 * useful to show in that narrow a window that "Unsaved" doesn't already
 * communicate. */
export function SaveStatusIndicator({ fileId }: { fileId: string | null }) {
  const isDirty = useWorkspaceStore((s) => (fileId ? fileId in s.dirtyContent : false));

  if (!fileId) return null;

  return (
    <span className="flex items-center gap-1.5 text-xs text-ink-muted">
      <span
        className={`h-1.5 w-1.5 rounded-full ${isDirty ? "bg-ink-faint" : "bg-success"}`}
        aria-hidden="true"
      />
      {isDirty ? "Unsaved" : "Saved"}
    </span>
  );
}
