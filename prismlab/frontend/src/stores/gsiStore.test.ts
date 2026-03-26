import { describe, it, expect, beforeEach, vi } from "vitest";
import { useGsiStore, type GsiLiveState } from "./gsiStore";

const mockLiveState: GsiLiveState = {
  hero_name: "npc_dota_hero_antimage",
  hero_id: 1,
  hero_level: 12,
  gold: 1523,
  gpm: 456,
  net_worth: 12500,
  kills: 3,
  deaths: 1,
  assists: 7,
  items_inventory: ["item_power_treads", "item_bfury"],
  items_backpack: [],
  items_neutral: "item_mysterious_hat",
  game_clock: 600,
  game_state: "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
  team_side: "radiant",
  is_alive: true,
  timestamp: 1700000000,
  roshan_state: "alive",
  radiant_tower_count: 11,
  dire_tower_count: 11,
};

describe("gsiStore", () => {
  beforeEach(() => {
    useGsiStore.setState({
      wsStatus: "disconnected",
      gsiStatus: "idle",
      lastUpdate: null,
      liveState: null,
    });
  });

  it("initializes with idle gsiStatus and disconnected wsStatus", () => {
    const state = useGsiStore.getState();
    expect(state.gsiStatus).toBe("idle");
    expect(state.wsStatus).toBe("disconnected");
    expect(state.lastUpdate).toBeNull();
    expect(state.liveState).toBeNull();
  });

  it("updateLiveState sets liveState and gsiStatus to connected", () => {
    useGsiStore.getState().updateLiveState(mockLiveState);
    const state = useGsiStore.getState();
    expect(state.liveState).toEqual(mockLiveState);
    expect(state.gsiStatus).toBe("connected");
  });

  it("updateLiveState sets lastUpdate to current timestamp", () => {
    const now = 1700000000000;
    vi.spyOn(Date, "now").mockReturnValue(now);
    useGsiStore.getState().updateLiveState(mockLiveState);
    expect(useGsiStore.getState().lastUpdate).toBe(now);
    vi.restoreAllMocks();
  });

  it("setWsStatus updates wsStatus field", () => {
    useGsiStore.getState().setWsStatus("connected");
    expect(useGsiStore.getState().wsStatus).toBe("connected");

    useGsiStore.getState().setWsStatus("connecting");
    expect(useGsiStore.getState().wsStatus).toBe("connecting");
  });

  it("gsiStatus becomes lost when WS disconnects while GSI was connected", () => {
    // First, get GSI to connected state
    useGsiStore.getState().updateLiveState(mockLiveState);
    expect(useGsiStore.getState().gsiStatus).toBe("connected");

    // Now disconnect WS -- gsiStatus should go to "lost"
    useGsiStore.getState().setWsStatus("disconnected");
    expect(useGsiStore.getState().gsiStatus).toBe("lost");
  });

  it("updateLiveState preserves roshan_state and tower counts", () => {
    const stateWithTowers: GsiLiveState = {
      ...mockLiveState,
      roshan_state: "respawn_base",
      radiant_tower_count: 9,
      dire_tower_count: 10,
    };
    useGsiStore.getState().updateLiveState(stateWithTowers);
    const state = useGsiStore.getState();
    expect(state.liveState?.roshan_state).toBe("respawn_base");
    expect(state.liveState?.radiant_tower_count).toBe(9);
    expect(state.liveState?.dire_tower_count).toBe(10);
  });

  it("clearLiveState resets liveState and gsiStatus to idle", () => {
    useGsiStore.getState().updateLiveState(mockLiveState);
    expect(useGsiStore.getState().gsiStatus).toBe("connected");

    useGsiStore.getState().clearLiveState();
    const state = useGsiStore.getState();
    expect(state.liveState).toBeNull();
    expect(state.gsiStatus).toBe("idle");
    expect(state.lastUpdate).toBeNull();
  });
});
