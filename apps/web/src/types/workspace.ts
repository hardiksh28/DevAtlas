// Mirrors apps/api/app/modules/workspace/schemas.py — same convention
// as types/projects.ts: plain TS types, not a generated client.

export interface WorkspaceFileMeta {
  id: string;
  path: string;
  size_bytes: number;
  updated_at: string;
}

export interface WorkspaceFileDetail extends WorkspaceFileMeta {
  content: string;
  content_hash: string | null;
}

export interface WorkspaceFileListResponse {
  items: WorkspaceFileMeta[];
}

export type WorkspaceRightRailTab = "lesson" | "chat" | "diagrams";
export type WorkspaceBottomPanelTab = "terminal" | "preview";

export interface WorkspaceLayout {
  open_tabs: string[];
  active_tab_id: string | null;
  panel_sizes: Record<string, number>;
  bottom_panel_visible: boolean;
  right_rail_tab: WorkspaceRightRailTab;
  bottom_panel_tab: WorkspaceBottomPanelTab;
  updated_at: string;
}

export interface CreateWorkspaceFilePayload {
  path: string;
  content?: string;
}

export interface UpdateWorkspaceFileContentPayload {
  content: string;
  expected_content_hash?: string | null;
}

export interface RenameWorkspaceFilePayload {
  new_path: string;
}

export interface UpdateWorkspaceLayoutPayload {
  open_tabs?: string[];
  active_tab_id?: string | null;
  panel_sizes?: Record<string, number>;
  bottom_panel_visible?: boolean;
  right_rail_tab?: WorkspaceRightRailTab;
  bottom_panel_tab?: WorkspaceBottomPanelTab;
}
