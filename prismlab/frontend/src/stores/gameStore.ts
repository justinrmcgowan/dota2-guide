import { create } from "zustand";
import type { Hero } from "../types/hero";

interface GameStore {
  selectedHero: Hero | null;
  selectHero: (hero: Hero) => void;
  clearHero: () => void;
}

export const useGameStore = create<GameStore>()((set) => ({
  selectedHero: null,
  selectHero: (hero) => set({ selectedHero: hero }),
  clearHero: () => set({ selectedHero: null }),
}));
