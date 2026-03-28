import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useGsiStore } from "../../stores/gsiStore";
import type { GsiLiveState } from "../../stores/gsiStore";
import LiveStatsBar from "./LiveStatsBar";

function makeLiveState(overrides: Partial<GsiLiveState> = {}): GsiLiveState {
  return {
    hero_name: "npc_dota_hero_antimage",
    hero_id: 1,
    hero_level: 10,
    gold: 2500,
    gpm: 450,
    net_worth: 8000,
    kills: 5,
    deaths: 2,
    assists: 3,
    items_inventory: ["power_treads", "bfury"],
    items_backpack: [],
    items_neutral: "",
    game_clock: 900,
    game_state: "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    team_side: "radiant",
    is_alive: true,
    timestamp: Date.now(),
    roshan_state: "alive",
    radiant_tower_count: 11,
    dire_tower_count: 11,
    has_aghanims_shard: false,
    has_aghanims_scepter: false,
    match_id: "test123",
    ...overrides,
  };
}

describe("LiveStatsBar", () => {
  beforeEach(() => {
    useGsiStore.setState({
      wsStatus: "disconnected",
      gsiStatus: "idle",
      lastUpdate: null,
      liveState: null,
    });
  });

  it("renders null when gsiStatus is 'idle'", () => {
    const { container } = render(<LiveStatsBar />);
    expect(screen.queryByTestId("live-stats-bar")).toBeNull();
    expect(container.innerHTML).toBe("");
  });

  it("renders null when gsiStatus is 'connected' but game_state is not in progress", () => {
    useGsiStore.setState({
      gsiStatus: "connected",
      liveState: makeLiveState({
        game_state: "DOTA_GAMERULES_STATE_HERO_SELECTION",
      }),
    });

    render(<LiveStatsBar />);
    expect(screen.queryByTestId("live-stats-bar")).toBeNull();
  });

  it("renders gold, GPM, and NW when connected with valid in-game state", () => {
    useGsiStore.setState({
      gsiStatus: "connected",
      liveState: makeLiveState({
        gold: 2500,
        gpm: 450,
        net_worth: 8000,
      }),
    });

    render(<LiveStatsBar />);
    const bar = screen.getByTestId("live-stats-bar");
    expect(bar).toBeTruthy();

    // Check that the formatted values are in the text content
    expect(bar.textContent).toContain("2,500");
    expect(bar.textContent).toContain("450");
    expect(bar.textContent).toContain("8,000");
  });

  it("renders KDA values when connected", () => {
    useGsiStore.setState({
      gsiStatus: "connected",
      liveState: makeLiveState({
        kills: 5,
        deaths: 2,
        assists: 3,
      }),
    });

    render(<LiveStatsBar />);
    const bar = screen.getByTestId("live-stats-bar");

    // KDA should display in text
    expect(bar.textContent).toContain("5");
    expect(bar.textContent).toContain("2");
    expect(bar.textContent).toContain("3");
  });
});
