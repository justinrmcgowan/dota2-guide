import { create } from "zustand";

export interface GsiLiveState {
  hero_name: string;
  hero_id: number;
  hero_level: number;
  gold: number;
  gpm: number;
  net_worth: number;
  kills: number;
  deaths: number;
  assists: number;
  items_inventory: string[];
  items_backpack: string[];
  items_neutral: string;
  has_aghanims_shard: boolean;
  has_aghanims_scepter: boolean;
  game_clock: number;
  game_state: string;
  match_id: string;
  team_side: string;
  is_alive: boolean;
  timestamp: number;
  roshan_state: string;
  radiant_tower_count: number;
  dire_tower_count: number;
  win_team: string;
}

interface GsiStore {
  // Connection state
  wsStatus: "connected" | "disconnected" | "connecting";
  gsiStatus: "connected" | "idle" | "lost" | "reconnecting";
  lastUpdate: number | null;

  // Live game data
  liveState: GsiLiveState | null;
  matchId: string | null;

  // Actions
  setWsStatus: (
    status: "connected" | "disconnected" | "connecting",
  ) => void;
  updateLiveState: (data: GsiLiveState) => void;
  clearLiveState: () => void;
}

export const useGsiStore = create<GsiStore>()((set, get) => ({
  wsStatus: "disconnected",
  gsiStatus: "idle",
  lastUpdate: null,
  liveState: null,
  matchId: null,

  setWsStatus: (wsStatus) => {
    const prev = get().gsiStatus;
    // If WS disconnects and we had GSI data, enter "reconnecting" state.
    // "lost" is reserved for post-timeout expiry (D-11).
    let gsiStatus = prev;
    if (wsStatus === "disconnected" && prev === "connected") {
      gsiStatus = "reconnecting";
    }
    set({ wsStatus, gsiStatus });
  },

  updateLiveState: (data) =>
    set({
      liveState: data,
      gsiStatus: "connected",
      lastUpdate: Date.now(),
      ...(data.match_id ? { matchId: data.match_id } : {}),
    }),

  clearLiveState: () =>
    set({
      liveState: null,
      gsiStatus: "idle",
      lastUpdate: null,
    }),
}));
