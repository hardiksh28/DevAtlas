"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { Button } from "ui";

import { Badge } from "@/components/ui/Badge";
import { MermaidDiagram } from "@/components/workspace/MermaidDiagram";
import { useDiagrams, useGenerateDiagram } from "@/hooks/useDiagrams";
import { formatRelativeTime } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";
import { DIAGRAM_TYPE_LABELS, type DiagramType } from "@/types/diagrams";

const DIAGRAM_TYPES = Object.keys(DIAGRAM_TYPE_LABELS) as DiagramType[];

/** Generates and browses Mermaid diagrams for the project — a third
 * right-rail tab alongside Lesson/Chat (see WorkspaceShell.tsx). Diagrams
 * render entirely client-side via MermaidDiagram; this panel only owns
 * the generate form and the history list. */
export function DiagramsPanel({ projectId }: { projectId: string }) {
  const { data, isLoading } = useDiagrams(projectId);
  const generate = useGenerateDiagram(projectId);
  const currentMilestoneId = useSessionStore((s) => s.currentMilestoneId);

  const [diagramType, setDiagramType] = useState<DiagramType>("flowchart");
  const [subject, setSubject] = useState("");

  function handleGenerate() {
    const trimmed = subject.trim();
    if (!trimmed && !currentMilestoneId) return;
    generate.mutate(
      { diagram_type: diagramType, subject: trimmed || null, milestone_id: currentMilestoneId },
      { onSuccess: () => setSubject("") },
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="space-y-2 border-b border-line p-3">
        <select
          value={diagramType}
          onChange={(e) => setDiagramType(e.target.value as DiagramType)}
          className="w-full rounded-md border border-line bg-canvas px-2 py-1.5 text-sm text-ink focus:border-accent focus:outline-none"
        >
          {DIAGRAM_TYPES.map((type) => (
            <option key={type} value={type}>
              {DIAGRAM_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
        <textarea
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder={
            currentMilestoneId
              ? "Optional — add detail, or leave blank to diagram the current milestone"
              : "What should this diagram explain?"
          }
          rows={2}
          className="w-full resize-none rounded-md border border-line bg-canvas px-2 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:border-accent focus:outline-none"
        />
        <Button
          type="button"
          size="sm"
          className="w-full"
          onClick={handleGenerate}
          disabled={!subject.trim() && !currentMilestoneId}
          loading={generate.isPending}
        >
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Generate diagram
        </Button>
        {generate.isError && (
          <p className="text-xs text-danger-ink">{generate.error.message}</p>
        )}
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-3">
        {isLoading && <p className="text-sm text-ink-muted">Loading diagrams…</p>}
        {!isLoading && (data?.items.length ?? 0) === 0 && (
          <p className="text-sm text-ink-muted">
            No diagrams yet — generate one above to visualize a concept, flow, or schema.
          </p>
        )}
        {data?.items.map((diagram) => (
          <div key={diagram.id} className="space-y-2 rounded-lg border border-line p-2">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-ink">{diagram.title}</p>
              <Badge variant="outline">{DIAGRAM_TYPE_LABELS[diagram.diagram_type]}</Badge>
            </div>
            <MermaidDiagram source={diagram.mermaid_source} />
            <p className="text-xs text-ink-faint">{formatRelativeTime(diagram.created_at)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
