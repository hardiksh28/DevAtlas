"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/Skeleton";

let renderCounter = 0;

/**
 * Renders Mermaid diagram source to SVG entirely client-side — no
 * server-side rendering pipeline (headless browser, Kroki, etc). `mermaid`
 * is imported dynamically inside an effect rather than at module scope,
 * since it reaches for `window` on load — same reasoning as
 * EditorPane/TerminalPanel in WorkspaceShell.tsx.
 *
 * `securityLevel: "strict"` is pinned explicitly (it's mermaid's own
 * default, but pinning it here means a future mermaid upgrade can't
 * silently change that default and start executing HTML/script found in a
 * label) — `source` originates from an LLM, so this is the client-side
 * half of the sanitization app/modules/visuals/content_builder.py already
 * applies server-side. `mermaid.render`'s returned SVG string is mermaid's
 * own sanitized output, not `source` itself, which is what makes the
 * `dangerouslySetInnerHTML` below safe.
 */
export function MermaidDiagram({ source, className }: { source: string; className?: string }) {
  const { resolvedTheme } = useTheme();
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setSvg(null);
    setError(null);

    import("mermaid").then(async ({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        theme: resolvedTheme === "dark" ? "dark" : "default",
      });
      try {
        const { svg: rendered } = await mermaid.render(`mermaid-${++renderCounter}`, source);
        if (!cancelled) setSvg(rendered);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to render diagram.");
        }
      }
    });

    return () => {
      cancelled = true;
    };
  }, [source, resolvedTheme]);

  if (error) {
    return (
      <div
        role="alert"
        className={`rounded-md border border-danger-soft bg-danger-soft/30 p-3 text-xs ${className ?? ""}`}
      >
        <p className="mb-2 font-medium text-danger-ink">Couldn&apos;t render this diagram.</p>
        <pre className="overflow-x-auto whitespace-pre-wrap text-ink-muted">{source}</pre>
      </div>
    );
  }

  if (!svg) {
    return <Skeleton className={`h-40 w-full ${className ?? ""}`} />;
  }

  return (
    <div
      className={`[&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full ${className ?? ""}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
