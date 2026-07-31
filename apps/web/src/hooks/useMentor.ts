"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api-client";
import { listMentorMessages, sendMentorMessage } from "@/lib/mentor-api";
import type { MessageListResponse, SendMessageRequest, SendMessageResponse } from "@/types/mentor";

const messagesKey = (projectId: string) => ["mentor", projectId, "messages"] as const;

export function useMentorMessages(projectId: string) {
  return useQuery({
    queryKey: messagesKey(projectId),
    queryFn: () => listMentorMessages(projectId),
    enabled: Boolean(projectId),
  });
}

export function useSendMentorMessage(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<SendMessageResponse, ApiError, SendMessageRequest>({
    mutationFn: (payload) => sendMentorMessage(projectId, payload),
    onSuccess: ({ user_message, reply }) => {
      queryClient.setQueryData(messagesKey(projectId), (existing: MessageListResponse | undefined) => {
        const items = [...(existing?.items ?? []), user_message, reply];
        return { items, total: items.length, limit: existing?.limit ?? 50, offset: existing?.offset ?? 0 };
      });
    },
  });
}
