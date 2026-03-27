import { create } from "zustand";
import type { TriggerEvent } from "../utils/triggerDetection";

export type { TriggerEvent } from "../utils/triggerDetection";

interface RefreshStore {
  // Cooldown state (D-07, D-08)
  cooldownEnd: number | null;
  queuedEvent: TriggerEvent | null;
  secondsRemaining: number;

  // Toast state (D-15, D-16, D-17)
  lastToast: { message: string; timestamp: number } | null;

  // Lane auto-detection state (D-12)
  laneAutoDetected: boolean;

  // Actions
  startCooldown: () => void;
  queueEvent: (event: TriggerEvent) => void;
  clearQueue: () => void;
  showToast: (message: string) => void;
  dismissToast: () => void;
  tick: (now: number) => void;
  resetCooldown: () => void;
  setLaneAutoDetected: (v: boolean) => void;
}

export const useRefreshStore = create<RefreshStore>()((set, get) => ({
  cooldownEnd: null,
  queuedEvent: null,
  secondsRemaining: 0,
  lastToast: null,
  laneAutoDetected: false,

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

  setLaneAutoDetected: (v) => set({ laneAutoDetected: v }),
}));
