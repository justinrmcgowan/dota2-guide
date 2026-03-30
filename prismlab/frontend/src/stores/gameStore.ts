import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Hero } from "../types/hero";
import type { EnemyContext } from "../types/recommendation";
import { PLAYSTYLE_OPTIONS } from "../utils/constants";

interface GameStore {
  selectedHero: Hero | null;
  allies: (Hero | null)[];
  opponents: (Hero | null)[];
  role: number | null;
  playstyle: string | null;
  side: "radiant" | "dire" | null;
  lane: "safe" | "mid" | "off" | null;
  laneOpponents: Hero[];

  // Game mode
  turbo: boolean;

  // Mid-game adaptation state
  laneResult: "won" | "even" | "lost" | null;
  damageProfile: { physical: number; magical: number; pure: number } | null;
  enemyItemsSpotted: string[];
  enemyContext: EnemyContext[];

  selectHero: (hero: Hero) => void;
  clearHero: () => void;
  setAlly: (index: number, hero: Hero) => void;
  clearAlly: (index: number) => void;
  setOpponent: (index: number, hero: Hero) => void;
  clearOpponent: (index: number) => void;
  setRole: (role: number) => void;
  setPlaystyle: (playstyle: string) => void;
  setSide: (side: "radiant" | "dire") => void;
  setLane: (lane: "safe" | "mid" | "off") => void;
  toggleLaneOpponent: (hero: Hero) => void;
  clearLaneOpponents: () => void;

  // Mid-game adaptation actions
  setLaneResult: (result: "won" | "even" | "lost") => void;
  setDamageProfile: (profile: {
    physical: number;
    magical: number;
    pure: number;
  }) => void;
  toggleEnemyItem: (itemName: string) => void;
  setEnemyItemsSpotted: (items: string[]) => void;
  setTurbo: (turbo: boolean) => void;
  setEnemyContext: (ctx: EnemyContext[]) => void;
  clearMidGameState: () => void;
  clear: () => void;
}

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
  selectedHero: null,
  allies: [null, null, null, null],
  opponents: [null, null, null, null, null],
  role: null,
  playstyle: null,
  side: null,
  lane: null,
  laneOpponents: [],
  turbo: false,
  laneResult: null,
  damageProfile: null,
  enemyItemsSpotted: [],
  enemyContext: [],

  selectHero: (hero) => set({ selectedHero: hero }),
  clearHero: () => set({ selectedHero: null }),

  setAlly: (index, hero) => {
    if (index < 0 || index >= 4) return;
    const allies = [...get().allies];
    allies[index] = hero;
    set({ allies });
  },

  clearAlly: (index) => {
    if (index < 0 || index >= 4) return;
    const allies = [...get().allies];
    allies[index] = null;
    set({ allies });
  },

  setOpponent: (index, hero) => {
    if (index < 0 || index >= 5) return;
    const opponents = [...get().opponents];
    opponents[index] = hero;
    set({ opponents });
  },

  clearOpponent: (index) => {
    if (index < 0 || index >= 5) return;
    const state = get();
    const oldHero = state.opponents[index];
    const opponents = [...state.opponents];
    opponents[index] = null;

    // Remove from laneOpponents if the cleared hero was there
    let laneOpponents = state.laneOpponents;
    if (oldHero) {
      laneOpponents = laneOpponents.filter((h) => h.id !== oldHero.id);
    }

    set({ opponents, laneOpponents });
  },

  setRole: (role) => {
    const { playstyle } = get();
    const validPlaystyles = PLAYSTYLE_OPTIONS[role] ?? [];
    const newPlaystyle =
      playstyle && validPlaystyles.includes(playstyle) ? playstyle : null;
    set({ role, playstyle: newPlaystyle });
  },

  setPlaystyle: (playstyle) => set({ playstyle }),

  setSide: (side) => set({ side }),

  setLane: (lane) => set({ lane }),

  toggleLaneOpponent: (hero) => {
    const { laneOpponents } = get();
    const exists = laneOpponents.some((h) => h.id === hero.id);
    if (exists) {
      set({ laneOpponents: laneOpponents.filter((h) => h.id !== hero.id) });
    } else if (laneOpponents.length < 2) {
      set({ laneOpponents: [...laneOpponents, hero] });
    }
  },

  clearLaneOpponents: () => set({ laneOpponents: [] }),

  // Mid-game adaptation actions
  setLaneResult: (result) => set({ laneResult: result }),

  setDamageProfile: (profile) => set({ damageProfile: profile }),

  toggleEnemyItem: (itemName) => {
    const { enemyItemsSpotted } = get();
    if (enemyItemsSpotted.includes(itemName)) {
      set({
        enemyItemsSpotted: enemyItemsSpotted.filter((n) => n !== itemName),
      });
    } else {
      set({ enemyItemsSpotted: [...enemyItemsSpotted, itemName] });
    }
  },

  setTurbo: (turbo) => set({ turbo }),

  setEnemyItemsSpotted: (items) => set({ enemyItemsSpotted: items }),

  setEnemyContext: (ctx) => set({ enemyContext: ctx }),

  clearMidGameState: () =>
    set({ laneResult: null, damageProfile: null, enemyItemsSpotted: [], enemyContext: [] }),

  clear: () =>
    set({
      selectedHero: null,
      allies: [null, null, null, null],
      opponents: [null, null, null, null, null],
      role: null,
      playstyle: null,
      side: null,
      lane: null,
      laneOpponents: [],
      turbo: false,
      laneResult: null,
      damageProfile: null,
      enemyItemsSpotted: [],
      enemyContext: [],
    }),
    }),
    {
      name: "prismlab-game",
      version: 1,
    },
  ),
);
