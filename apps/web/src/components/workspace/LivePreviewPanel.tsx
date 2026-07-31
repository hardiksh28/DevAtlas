"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useWorkspaceFile, useWorkspaceTree } from "@/hooks/useWorkspace";
import { fetchWorkspaceFile } from "@/lib/workspace-api";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";

function isHtmlPath(path: string): boolean {
  return /\.html?$/i.test(path);
}

function resolveRelative(basePath: string, relative: string): string {
  const baseDir = basePath.includes("/") ? basePath.slice(0, basePath.lastIndexOf("/")) : "";
  const segments = [...baseDir.split("/").filter(Boolean), ...relative.split("/")];
  const resolved: string[] = [];
  for (const segment of segments) {
    if (segment === "." || segment === "") continue;
    if (segment === "..") resolved.pop();
    else resolved.push(segment);
  }
  return resolved.join("/");
}

// ponytail: regex-based tag matching, not a real HTML parser — covers
// the common `<link rel="stylesheet" href="...">` / `<script src="...">`
// authoring order (attribute order matters, self-closing `<script/>`
// won't match). Good enough for lesson-scoped HTML/CSS/JS previews;
// upgrade to a DOM-based rewrite (parse via DOMParser) if lessons ever
// need more exotic markup.
const STYLESHEET_LINK_RE = /<link[^>]+rel=["']stylesheet["'][^>]+href=["']([^"']+)["'][^>]*>/gi;
const SCRIPT_SRC_RE = /<script[^>]+src=["']([^"']+)["'][^>]*><\/script>/gi;

/** Real, client-only Live Preview: renders the active (or first) HTML
 * file directly in a sandboxed iframe, inlining same-workspace
 * stylesheet/script references so a multi-file HTML/CSS/JS lesson
 * genuinely live-previews. No server execution involved — see
 * docs/architecture/interactive-workspace-v1.md's deferred-execution
 * section for why this, and not a dev-server-backed preview, is what
 * ships in this phase. */
export function LivePreviewPanel({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const { data: tree } = useWorkspaceTree(projectId);
  const activeTabId = useWorkspaceStore((s) => s.activeTabId);

  const activeFile = tree?.items.find((f) => f.id === activeTabId);
  const htmlMeta =
    activeFile && isHtmlPath(activeFile.path) ? activeFile : tree?.items.find((f) => isHtmlPath(f.path));

  const { data: htmlDetail } = useWorkspaceFile(projectId, htmlMeta?.id ?? null);
  const [srcDoc, setSrcDoc] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function inlineAssets(html: string, regex: RegExp, wrap: (content: string) => string) {
      if (!htmlMeta || !tree) return html;
      const pathToId = new Map(tree.items.map((f) => [f.path, f.id]));
      let result = html;
      for (const match of html.matchAll(regex)) {
        const relativeRef = match[1];
        if (!relativeRef || /^https?:\/\//i.test(relativeRef)) continue;
        const fileId = pathToId.get(resolveRelative(htmlMeta.path, relativeRef));
        if (!fileId) continue;
        const asset = await queryClient.fetchQuery({
          queryKey: ["workspace", projectId, "file", fileId],
          queryFn: () => fetchWorkspaceFile(projectId, fileId),
        });
        result = result.replace(match[0], wrap(asset.content));
      }
      return result;
    }

    async function build() {
      if (!htmlDetail) {
        setSrcDoc("");
        return;
      }
      let html = await inlineAssets(htmlDetail.content, STYLESHEET_LINK_RE, (css) => `<style>${css}</style>`);
      html = await inlineAssets(html, SCRIPT_SRC_RE, (js) => `<script>${js}</script>`);
      if (!cancelled) setSrcDoc(html);
    }

    build();
    return () => {
      cancelled = true;
    };
  }, [htmlDetail, htmlMeta, tree, projectId, queryClient]);

  if (!htmlMeta) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-center text-sm text-ink-muted">
        Open (or create) an HTML file to see a live preview.
      </div>
    );
  }

  return (
    <iframe
      title="Live preview"
      sandbox="allow-scripts"
      srcDoc={srcDoc}
      className="h-full w-full border-0 bg-white"
    />
  );
}
