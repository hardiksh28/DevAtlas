"use client";

import Editor from "@monaco-editor/react";
import { useTheme } from "next-themes";
import { useEffect, useRef } from "react";

import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { useUpdateWorkspaceFileContent, useWorkspaceFile } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";

const AUTOSAVE_DEBOUNCE_MS = 800;

const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  js: "javascript",
  jsx: "javascript",
  mjs: "javascript",
  ts: "typescript",
  tsx: "typescript",
  py: "python",
  json: "json",
  html: "html",
  htm: "html",
  css: "css",
  scss: "scss",
  md: "markdown",
  yml: "yaml",
  yaml: "yaml",
  sh: "shell",
  sql: "sql",
};

function languageForPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return LANGUAGE_BY_EXTENSION[ext] ?? "plaintext";
}

/**
 * One Monaco instance for the currently active tab — remounted (via
 * the `key={fileId}` the caller supplies) rather than kept alive per
 * open tab and fed a new model, trading undo-history-across-tab-
 * switches for a much smaller component. Autosave debounces 800ms
 * after the last keystroke and flushes immediately on unmount (tab
 * switch/close) or `beforeunload`, so no more than ~800ms of typing is
 * ever at risk — see docs/architecture/interactive-workspace-v1.md's
 * file synchronization section.
 */
export function EditorPane({ projectId, fileId }: { projectId: string; fileId: string }) {
  const { data: file, isLoading } = useWorkspaceFile(projectId, fileId);
  const updateContent = useUpdateWorkspaceFileContent(projectId);
  const setDirtyContent = useWorkspaceStore((s) => s.setDirtyContent);
  const clearDirtyContent = useWorkspaceStore((s) => s.clearDirtyContent);
  const { resolvedTheme } = useTheme();

  const latestContentRef = useRef<string>("");
  const latestHashRef = useRef<string | null>(null);

  useEffect(() => {
    if (file) {
      latestContentRef.current = file.content;
      latestHashRef.current = file.content_hash;
    }
  }, [file]);

  const save = useDebouncedCallback(() => {
    updateContent.mutate(
      {
        fileId,
        payload: { content: latestContentRef.current, expected_content_hash: latestHashRef.current },
      },
      {
        onSuccess: (saved) => {
          latestHashRef.current = saved.content_hash;
          clearDirtyContent(fileId);
        },
      },
    );
  }, AUTOSAVE_DEBOUNCE_MS);

  useEffect(() => {
    window.addEventListener("beforeunload", save.flush);
    return () => {
      window.removeEventListener("beforeunload", save.flush);
      save.flush();
    };
    // Deliberately fileId-only: `save` is recreated every render, but
    // its pending timeout lives in a stable ref, so re-subscribing on
    // every render isn't needed — only when the active file changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]);

  function handleChange(value: string | undefined) {
    const content = value ?? "";
    latestContentRef.current = content;
    setDirtyContent(fileId, content);
    save();
  }

  if (isLoading || !file) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-ink-muted">
        Loading file…
      </div>
    );
  }

  return (
    <Editor
      height="100%"
      language={languageForPath(file.path)}
      defaultValue={file.content}
      onChange={handleChange}
      theme={resolvedTheme === "light" ? "light" : "vs-dark"}
      options={{ minimap: { enabled: false }, fontSize: 13, automaticLayout: true }}
    />
  );
}
