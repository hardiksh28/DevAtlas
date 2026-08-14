import { create } from "zustand";

interface CompanionNotification {
  id: number;
  message: string;
}

interface CompanionState {
  notification: CompanionNotification | null;
  /** Bumped on every notify() — PixelPet's bounceKey prop keys off this
   * to retrigger the pop animation even if the message text repeats. */
  bounceTick: number;
  notify: (message: string) => void;
  dismiss: () => void;
}

let nextId = 1;

/** Client-only UI state for the floating AI companion widget (see
 * components/companion/CompanionWidget.tsx) — which notification bubble
 * is showing, if any. Deliberately separate from useSessionStore: this
 * is presentation state for a cross-cutting UI element, not
 * project/workspace session state. */
export const useCompanionStore = create<CompanionState>((set) => ({
  notification: null,
  bounceTick: 0,
  notify: (message) =>
    set((state) => ({ notification: { id: nextId++, message }, bounceTick: state.bounceTick + 1 })),
  dismiss: () => set({ notification: null }),
}));
