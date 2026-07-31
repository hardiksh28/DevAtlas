// Mirrors apps/api/app/modules/visuals/schemas.py — the Diagrams panel's
// data shape.

export type DiagramType = "erd" | "flowchart" | "architecture" | "state" | "sequence" | "component";

export interface DiagramRead {
  id: string;
  project_id: string;
  milestone_id: string | null;
  diagram_type: DiagramType;
  title: string;
  subject: string;
  mermaid_source: string;
  created_at: string;
}

export interface DiagramListResponse {
  items: DiagramRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface GenerateDiagramRequest {
  diagram_type: DiagramType;
  subject?: string | null;
  milestone_id?: string | null;
  code?: string | null;
}

export const DIAGRAM_TYPE_LABELS: Record<DiagramType, string> = {
  erd: "Database (ERD)",
  flowchart: "Flowchart",
  architecture: "System architecture",
  state: "State diagram",
  sequence: "Sequence diagram",
  component: "Component diagram",
};
