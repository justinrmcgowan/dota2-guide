import { create } from "zustand";
import type { ParsedHero, ParsedItem } from "../types/screenshot";

interface ScreenshotStore {
  // Modal state
  isOpen: boolean;
  imageData: string | null; // raw base64 (no data URL prefix)
  mimeType: string | null; // "image/png" | "image/jpeg" | etc.

  // Parse state
  parsedHeroes: ParsedHero[];
  isLoading: boolean;
  error: string | null;
  latencyMs: number | null;

  // Actions
  openModal: (imageData: string, mimeType: string) => void;
  closeModal: () => void;
  setParsedHeroes: (heroes: ParsedHero[]) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
  setLatency: (ms: number | null) => void;

  // Edit actions for confirmation UI (per D-07)
  removeItem: (heroIdx: number, itemIdx: number) => void;
  addItem: (heroIdx: number, item: ParsedItem) => void;
  removeHero: (heroIdx: number) => void;
  reset: () => void;
}

const initialState = {
  isOpen: false,
  imageData: null,
  mimeType: null,
  parsedHeroes: [] as ParsedHero[],
  isLoading: false,
  error: null as string | null,
  latencyMs: null as number | null,
};

export const useScreenshotStore = create<ScreenshotStore>()((set, get) => ({
  ...initialState,

  openModal: (imageData, mimeType) =>
    set({
      isOpen: true,
      imageData,
      mimeType,
      parsedHeroes: [],
      isLoading: false,
      error: null,
      latencyMs: null,
    }),

  closeModal: () => set({ ...initialState }),

  setParsedHeroes: (heroes) => set({ parsedHeroes: heroes }),
  setLoading: (v) => set({ isLoading: v }),
  setError: (msg) => set({ error: msg }),
  setLatency: (ms) => set({ latencyMs: ms }),

  removeItem: (heroIdx, itemIdx) => {
    const heroes = [...get().parsedHeroes];
    if (heroes[heroIdx]) {
      const hero = {
        ...heroes[heroIdx],
        items: [...heroes[heroIdx].items],
      };
      hero.items.splice(itemIdx, 1);
      heroes[heroIdx] = hero;
      set({ parsedHeroes: heroes });
    }
  },

  addItem: (heroIdx, item) => {
    const heroes = [...get().parsedHeroes];
    if (heroes[heroIdx] && heroes[heroIdx].items.length < 6) {
      const hero = {
        ...heroes[heroIdx],
        items: [...heroes[heroIdx].items, item],
      };
      heroes[heroIdx] = hero;
      set({ parsedHeroes: heroes });
    }
  },

  removeHero: (heroIdx) => {
    const heroes = get().parsedHeroes.filter((_, i) => i !== heroIdx);
    set({ parsedHeroes: heroes });
  },

  reset: () => set({ ...initialState }),
}));
