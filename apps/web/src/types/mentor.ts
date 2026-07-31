// Mirrors apps/api/app/modules/mentoring/schemas.py — the AI Chat
// panel's data shape.

export interface MessageRead {
  id: string;
  role: "user" | "assistant";
  content: string;
  milestone_id: string | null;
  misconceptions_detected: string[];
  created_at: string;
}

export interface MessageListResponse {
  items: MessageRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface SendMessageRequest {
  content: string;
  milestone_id?: string | null;
}

export interface SendMessageResponse {
  user_message: MessageRead;
  reply: MessageRead;
}
