"use client";

import { BookOpen, Eye, MessageSquare, PanelBottom, TerminalSquare, Workflow } from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

import { ChatPanel } from "@/components/workspace/ChatPanel";
import { DiagramsPanel } from "@/components/workspace/DiagramsPanel";
import { FileExplorer } from "@/components/workspace/FileExplorer";
import { LessonPanel } from "@/components/workspace/LessonPanel";
import { LivePreviewPanel } from "@/components/workspace/LivePreviewPanel";
import { SaveStatusIndicator } from "@/components/workspace/SaveStatusIndicator";
import { TabBar } from "@/components/workspace/TabBar";
import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { useUpdateWorkspaceLayout, useWorkspaceLayout } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";

// Monaco and xterm.js both reach for `window`/the DOM directly and are
// multi-MB bundles nobody outside this one page needs — dynamic +
// ssr:false keeps them out of every other route's bundle and off the
// server render entirely.
const EditorPane = dynamic(
  () => import("@/components/workspace/EditorPane").then((m) => m.EditorPane),
  { ssr: false, loading: () => <PaneMessage>Loading editor…</PaneMessage> },
);
const TerminalPanel = dynamic(
  () => import("@/components/workspace/TerminalPanel").then((m) => m.TerminalPanel),
  { ssr: false },
);

interface PanelSizes {
  explorer: number;
  rightRail: number;
  bottomPanel: number;
}

const DEFAULT_PANEL_SIZES: PanelSizes = { explorer: 18, rightRail: 25, bottomPanel: 30 };
const LAYOUT_PERSIST_DEBOUNCE_MS = 500;

function PaneMessage({ children }: { children: ReactNode }) {
  return <div className="flex h-full items-center justify-center text-sm text-ink-muted">{children}</div>;
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs font-medium transition-colors ${
        active ? "bg-surface-muted text-ink" : "text-ink-muted hover:text-ink"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

/**
 * The VS-Code-shaped shell: File Explorer (left) | Editor+Tabs / Terminal-
 * Preview (center, split vertically) | Lesson/Chat (right rail).
 * Panel sizes and open tabs persist to `workspace_layouts` (debounced,
 * same pattern as autosave) — see
 * docs/architecture/interactive-workspace-v1.md.
 */
export function WorkspaceShell({ projectId }: { projectId: string }) {
  const { data: layout } = useWorkspaceLayout(projectId);
  const updateLayout = useUpdateWorkspaceLayout(projectId);
  const hydrateFromLayout = useWorkspaceStore((s) => s.hydrateFromLayout);
  const openTabIds = useWorkspaceStore((s) => s.openTabIds);
  const activeTabId = useWorkspaceStore((s) => s.activeTabId);
  const rightRailTab = useWorkspaceStore((s) => s.rightRailTab);
  const setRightRailTab = useWorkspaceStore((s) => s.setRightRailTab);
  const bottomPanelVisible = useWorkspaceStore((s) => s.bottomPanelVisible);
  const setBottomPanelVisible = useWorkspaceStore((s) => s.setBottomPanelVisible);
  const bottomPanelTab = useWorkspaceStore((s) => s.bottomPanelTab);
  const setBottomPanelTab = useWorkspaceStore((s) => s.setBottomPanelTab);

  const hydratedRef = useRef(false);
  const [panelSizes, setPanelSizes] = useState<PanelSizes | null>(null);

  // Hydrate once from the persisted layout — guarded so a later
  // background refetch of this query never stomps in-progress local
  // UI state (an open tab the user just clicked) with stale server data.
  useEffect(() => {
    if (layout && !hydratedRef.current) {
      hydrateFromLayout(layout);
      setPanelSizes({
        explorer: layout.panel_sizes.explorer ?? DEFAULT_PANEL_SIZES.explorer,
        rightRail: layout.panel_sizes.rightRail ?? DEFAULT_PANEL_SIZES.rightRail,
        bottomPanel: layout.panel_sizes.bottomPanel ?? DEFAULT_PANEL_SIZES.bottomPanel,
      });
      hydratedRef.current = true;
    }
  }, [layout, hydrateFromLayout]);

  const persistLayout = useDebouncedCallback(() => {
    if (!panelSizes) return;
    updateLayout.mutate({
      open_tabs: openTabIds,
      active_tab_id: activeTabId,
      panel_sizes: { ...panelSizes },
      bottom_panel_visible: bottomPanelVisible,
      right_rail_tab: rightRailTab,
      bottom_panel_tab: bottomPanelTab,
    });
  }, LAYOUT_PERSIST_DEBOUNCE_MS);

  useEffect(() => {
    if (!hydratedRef.current) return;
    persistLayout();
    // Deliberately omits `persistLayout`/`updateLayout` — see
    // useDebouncedCallback's own note on why identity churn there is fine.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openTabIds, activeTabId, panelSizes, bottomPanelVisible, rightRailTab, bottomPanelTab]);

  if (!layout || !panelSizes) {
    return <PaneMessage>Loading workspace…</PaneMessage>;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="flex h-10 shrink-0 items-center justify-between border-b border-line bg-surface px-3">
        <span className="text-xs font-medium text-ink-muted">Workspace</span>
        <div className="flex items-center gap-3">
          <SaveStatusIndicator fileId={activeTabId} />
          <button
            type="button"
            onClick={() => setBottomPanelVisible(!bottomPanelVisible)}
            aria-label="Toggle terminal/preview panel"
            title="Toggle terminal/preview"
            className={`rounded-sm p-1 hover:bg-surface-muted ${
              bottomPanelVisible ? "text-ink" : "text-ink-muted"
            }`}
          >
            <PanelBottom className="h-4 w-4" />
          </button>
        </div>
      </div>

      <PanelGroup
        direction="horizontal"
        className="flex-1"
        onLayout={(sizes) =>
          setPanelSizes((prev) =>
            prev
              ? {
                  ...prev,
                  explorer: sizes[0] ?? prev.explorer,
                  rightRail: sizes[2] ?? prev.rightRail,
                }
              : prev,
          )
        }
      >
        <Panel id="explorer" order={1} defaultSize={panelSizes.explorer} minSize={12} collapsible>
          <FileExplorer projectId={projectId} />
        </Panel>
        <PanelResizeHandle className="w-1 bg-line transition-colors hover:bg-accent" />

        <Panel id="center" order={2} minSize={30}>
          <PanelGroup
            direction="vertical"
            onLayout={(sizes) => {
              const bottomSize = sizes[1];
              if (bottomSize !== undefined) {
                setPanelSizes((prev) => (prev ? { ...prev, bottomPanel: bottomSize } : prev));
              }
            }}
          >
            <Panel id="editor" order={1} minSize={30}>
              <div className="flex h-full flex-col">
                <TabBar projectId={projectId} />
                <div className="min-h-0 flex-1">
                  {activeTabId ? (
                    // Remounted per file (key=fileId) rather than kept
                    // alive and fed a new fileId — EditorPane's refs
                    // (latest content/hash, pending debounce) are only
                    // ever valid for one file; remounting is what makes
                    // "flush on tab switch" (its unmount effect) correct
                    // instead of racing the new file's load against the
                    // old file's pending save.
                    <EditorPane key={activeTabId} projectId={projectId} fileId={activeTabId} />
                  ) : (
                    <PaneMessage>Select a file to start editing.</PaneMessage>
                  )}
                </div>
              </div>
            </Panel>

            {bottomPanelVisible && (
              <>
                <PanelResizeHandle className="h-1 bg-line transition-colors hover:bg-accent" />
                <Panel id="bottomPanel" order={2} defaultSize={panelSizes.bottomPanel} minSize={15}>
                  <div className="flex h-full flex-col">
                    <div className="flex h-9 shrink-0 items-center gap-1 border-b border-line px-2">
                      <TabButton
                        active={bottomPanelTab === "terminal"}
                        onClick={() => setBottomPanelTab("terminal")}
                        icon={<TerminalSquare className="h-3.5 w-3.5" aria-hidden="true" />}
                        label="Terminal"
                      />
                      <TabButton
                        active={bottomPanelTab === "preview"}
                        onClick={() => setBottomPanelTab("preview")}
                        icon={<Eye className="h-3.5 w-3.5" aria-hidden="true" />}
                        label="Preview"
                      />
                    </div>
                    <div className="min-h-0 flex-1">
                      {bottomPanelTab === "terminal" ? (
                        <TerminalPanel />
                      ) : (
                        <LivePreviewPanel projectId={projectId} />
                      )}
                    </div>
                  </div>
                </Panel>
              </>
            )}
          </PanelGroup>
        </Panel>
        <PanelResizeHandle className="w-1 bg-line transition-colors hover:bg-accent" />

        <Panel id="rightRail" order={3} defaultSize={panelSizes.rightRail} minSize={18} collapsible>
          <div className="flex h-full flex-col">
            <div className="flex h-9 shrink-0 items-center gap-1 border-b border-line px-2">
              <TabButton
                active={rightRailTab === "lesson"}
                onClick={() => setRightRailTab("lesson")}
                icon={<BookOpen className="h-3.5 w-3.5" aria-hidden="true" />}
                label="Lesson"
              />
              <TabButton
                active={rightRailTab === "chat"}
                onClick={() => setRightRailTab("chat")}
                icon={<MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />}
                label="Chat"
              />
              <TabButton
                active={rightRailTab === "diagrams"}
                onClick={() => setRightRailTab("diagrams")}
                icon={<Workflow className="h-3.5 w-3.5" aria-hidden="true" />}
                label="Diagrams"
              />
            </div>
            <div className="min-h-0 flex-1">
              {rightRailTab === "lesson" && <LessonPanel projectId={projectId} />}
              {rightRailTab === "chat" && <ChatPanel projectId={projectId} />}
              {rightRailTab === "diagrams" && <DiagramsPanel projectId={projectId} />}
            </div>
          </div>
        </Panel>
      </PanelGroup>
    </div>
  );
}
