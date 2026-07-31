import { create } from "zustand";

import type { WorkspaceBottomPanelTab, WorkspaceLayout, WorkspaceRightRailTab } from "@/types/workspace";

interface WorkspaceUIState {
  openTabIds: string[];
  activeTabId: string | null;
  rightRailTab: WorkspaceRightRailTab;
  bottomPanelVisible: boolean;
  bottomPanelTab: WorkspaceBottomPanelTab;
  // Per-tab uncommitted keystrokes, keyed by file id — the editor's
  // source of truth between "user typed" and "the debounced autosave
  // flushed." Never persisted; server data (saved content) lives in
  // React Query, not here. See useSessionStore's own doc-comment for
  // why mixing the two is the mistake this file avoids.
  dirtyContent: Record<string, string>;

  hydrateFromLayout: (layout: WorkspaceLayout) => void;
  openTab: (fileId: string) => void;
  closeTab: (fileId: string) => void;
  setActiveTab: (fileId: string | null) => void;
  reorderTabs: (openTabIds: string[]) => void;
  setDirtyContent: (fileId: string, content: string) => void;
  clearDirtyContent: (fileId: string) => void;
  setRightRailTab: (tab: WorkspaceRightRailTab) => void;
  setBottomPanelVisible: (visible: boolean) => void;
  setBottomPanelTab: (tab: WorkspaceBottomPanelTab) => void;
}

export const useWorkspaceStore = create<WorkspaceUIState>((set, get) => ({
  openTabIds: [],
  activeTabId: null,
  rightRailTab: "lesson",
  bottomPanelVisible: false,
  bottomPanelTab: "terminal",
  dirtyContent: {},

  hydrateFromLayout: (layout) =>
    set({
      openTabIds: layout.open_tabs,
      activeTabId: layout.active_tab_id,
      rightRailTab: layout.right_rail_tab,
      bottomPanelVisible: layout.bottom_panel_visible,
      bottomPanelTab: layout.bottom_panel_tab,
    }),

  openTab: (fileId) =>
    set((state) => ({
      openTabIds: state.openTabIds.includes(fileId) ? state.openTabIds : [...state.openTabIds, fileId],
      activeTabId: fileId,
    })),

  closeTab: (fileId) => {
    const { openTabIds, activeTabId, dirtyContent } = get();
    const remaining = openTabIds.filter((id) => id !== fileId);
    const { [fileId]: _discarded, ...restDirty } = dirtyContent;
    const closedIndex = openTabIds.indexOf(fileId);
    const nextActive =
      activeTabId !== fileId
        ? activeTabId
        : (remaining[Math.min(closedIndex, remaining.length - 1)] ?? null);
    set({ openTabIds: remaining, activeTabId: nextActive, dirtyContent: restDirty });
  },

  setActiveTab: (fileId) => set({ activeTabId: fileId }),

  reorderTabs: (openTabIds) => set({ openTabIds }),

  setDirtyContent: (fileId, content) =>
    set((state) => ({ dirtyContent: { ...state.dirtyContent, [fileId]: content } })),

  clearDirtyContent: (fileId) =>
    set((state) => {
      const { [fileId]: _discarded, ...rest } = state.dirtyContent;
      return { dirtyContent: rest };
    }),

  setRightRailTab: (tab) => set({ rightRailTab: tab }),
  setBottomPanelVisible: (visible) => set({ bottomPanelVisible: visible }),
  setBottomPanelTab: (tab) => set({ bottomPanelTab: tab }),
}));
