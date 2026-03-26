import { create } from "zustand";

export interface TriggerEvent {
  type:
    | "death"
    | "gold_swing"
    | "tower_kill"
    | "roshan_kill"
    | "phase_transition";
  message: string;
}

interface RefreshStore {
  // Cooldown state (D-07, D-08)
  cooldownEnd: number | null;
  queuedEvent: TriggerEvent | null;
  secondsRemaining: number;

  // Toast state (D-15, D-16, D-17)
  lastToast: { message: string; timestamp: number } | null;

  // Actions
  startCooldown: () => void;
  queueEvent: (event: TriggerEvent) => void;
  clearQueue: () => void;
  showToast: (message: string) => void;
  dismissToast: () => void;
  tick: (now: number) => void;
  resetCooldown: () => void;
}

export const useRefreshStore = create<RefreshStore>()((set, get) => ({
  cooldownEnd: null,
  queuedEvent: null,
  secondsRemaining: 0,
  lastToast: null,

  startCooldown: () => set({ cooldownEnd: Date.now() + 120_000 }),

  queueEvent: (event) => set({ queuedEvent: event }),

  clearQueue: () => set({ queuedEvent: null }),

  showToast: (message) =>
    set({ lastToast: { message, timestamp: Date.now() } }),

  dismissToast: () => set({ lastToast: null }),

  tick: (now) => {
    const { cooldownEnd } = get();
    if (cooldownEnd === null || now >= cooldownEnd) {
      set({ secondsRemaining: 0 });
    } else {
      set({ secondsRemaining: Math.ceil((cooldownEnd - now) / 1000) });
    }
  },

  resetCooldown: () =>
    set({ cooldownEnd: null, queuedEvent: null, secondsRemaining: 0 }),
}));
