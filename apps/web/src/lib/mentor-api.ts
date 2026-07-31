import { apiFetch } from "@/lib/api-client";
import type { MessageListResponse, SendMessageRequest, SendMessageResponse } from "@/types/mentor";

export function listMentorMessages(
  projectId: string,
  limit = 50,
  offset = 0,
): Promise<MessageListResponse> {
  return apiFetch<MessageListResponse>(
    `/v1/projects/${projectId}/mentor/messages?limit=${limit}&offset=${offset}`,
  );
}

export function sendMentorMessage(
  projectId: string,
  payload: SendMessageRequest,
): Promise<SendMessageResponse> {
  return apiFetch<SendMessageResponse>(`/v1/projects/${projectId}/mentor/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
