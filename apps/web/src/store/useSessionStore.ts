import { create } from "zustand";

interface SessionState {
  activeProjectId: string | null;
  currentMilestoneId: string | null;
  setActiveProject: (projectId: string | null) => void;
  setCurrentMilestone: (milestoneId: string | null) => void;
}

/**
 * Client-only UI/session state — which project and milestone the learner
 * currently has open. Deliberately does NOT hold server data (mastery
 * profiles, review comments, lesson content): that's React Query's job.
 * Mixing the two is the most common Zustand mistake — it leads to two
 * disagreeing sources of truth for the same server-owned data the moment
 * a background refetch updates one but not the other.
 */
export const useSessionStore = create<SessionState>((set) => ({
  activeProjectId: null,
  currentMilestoneId: null,
  setActiveProject: (projectId) => set({ activeProjectId: projectId, currentMilestoneId: null }),
  setCurrentMilestone: (milestoneId) => set({ currentMilestoneId: milestoneId }),
}));
