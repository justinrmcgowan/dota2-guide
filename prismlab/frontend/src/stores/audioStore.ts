import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AudioStore {
  enabled: boolean;
  volume: number; // 0.0 to 1.0
  setEnabled: (v: boolean) => void;
  setVolume: (v: number) => void;
}

export const useAudioStore = create<AudioStore>()(
  persist(
    (set) => ({
      enabled: true,
      volume: 0.7,
      setEnabled: (enabled) => set({ enabled }),
      setVolume: (volume) => set({ volume: Math.max(0, Math.min(1, volume)) }),
    }),
    { name: "prismlab-audio", version: 1 },
  ),
);
