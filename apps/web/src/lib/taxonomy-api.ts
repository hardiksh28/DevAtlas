import { apiFetch } from "@/lib/api-client";

export interface StackSummary {
  stack: string;
  stack_version: string;
  concept_count: number;
}

export function fetchStacks(): Promise<{ items: StackSummary[] }> {
  return apiFetch<{ items: StackSummary[] }>("/v1/taxonomy/stacks");
}
