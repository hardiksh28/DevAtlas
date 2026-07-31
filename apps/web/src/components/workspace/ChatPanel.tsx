"use client";

import { Send } from "lucide-react";
import { useState } from "react";
import { Button } from "ui";

import { useMentorMessages, useSendMentorMessage } from "@/hooks/useMentor";
import { useSessionStore } from "@/store/useSessionStore";

export function ChatPanel({ projectId }: { projectId: string }) {
  const { data, isLoading } = useMentorMessages(projectId);
  const sendMessage = useSendMentorMessage(projectId);
  const currentMilestoneId = useSessionStore((s) => s.currentMilestoneId);
  const [draft, setDraft] = useState("");

  function handleSend() {
    const content = draft.trim();
    if (!content || sendMessage.isPending) return;
    setDraft("");
    sendMessage.mutate({ content, milestone_id: currentMilestoneId });
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        {isLoading && <p className="text-sm text-ink-muted">Loading conversation…</p>}
        {!isLoading && (data?.items.length ?? 0) === 0 && (
          <p className="text-sm text-ink-muted">Ask your mentor anything about this project.</p>
        )}
        {data?.items.map((message) => (
          <div
            key={message.id}
            className={`max-w-[90%] rounded-lg px-3 py-2 text-sm ${
              message.role === "user"
                ? "ml-auto bg-accent text-white"
                : "bg-surface-muted text-ink"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ))}
        {sendMessage.isPending && (
          <div className="max-w-[90%] rounded-lg bg-surface-muted px-3 py-2 text-sm text-ink-muted">
            Thinking…
          </div>
        )}
      </div>

      <div className="flex items-end gap-2 border-t border-line p-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask your mentor…"
          rows={2}
          className="min-w-0 flex-1 resize-none rounded-md border border-line bg-canvas px-2 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:border-accent focus:outline-none"
        />
        <Button
          type="button"
          size="sm"
          onClick={handleSend}
          disabled={!draft.trim()}
          loading={sendMessage.isPending}
          aria-label="Send message"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
