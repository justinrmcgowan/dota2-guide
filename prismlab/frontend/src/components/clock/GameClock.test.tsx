import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useGsiStore } from "../../stores/gsiStore";
import GameClock from "./GameClock";

function setGsiState(overrides: Partial<ReturnType<typeof useGsiStore.getState>>) {
  useGsiStore.setState({
    wsStatus: "disconnected",
    gsiStatus: "idle",
    lastUpdate: null,
    liveState: null,
    ...overrides,
  });
}

function makeLiveState(overrides: Record<string, unknown> = {}) {
  return {
    hero_name: "npc_dota_hero_antimage",
    hero_id: 1,
    hero_level: 12,
    gold: 1523,
    gpm: 456,
    net_worth: 12500,
    kills: 3,
    deaths: 1,
    assists: 7,
    items_inventory: [],
    items_backpack: [],
    items_neutral: "",
    game_clock: 0,
    game_state: "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    team_side: "radiant",
    is_alive: true,
    timestamp: 1700000000,
    roshan_state: "alive",
    radiant_tower_count: 11,
    dire_tower_count: 11,
    win_team: "",
    has_aghanims_shard: false,
    has_aghanims_scepter: false,
    match_id: "test123",
    ...overrides,
  };
}

describe("GameClock", () => {
  beforeEach(() => {
    setGsiState({});
  });

  it("renders nothing when gsiStatus is idle", () => {
    setGsiState({ gsiStatus: "idle" });
    const { container } = render(<GameClock />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when gsiStatus is connected but game_state is not in progress", () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({
        game_state: "DOTA_GAMERULES_STATE_HERO_SELECTION",
      }),
    });
    const { container } = render(<GameClock />);
    expect(container.firstChild).toBeNull();
  });

  it('renders "12:34" when game_clock is 754', () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({ game_clock: 754 }),
    });
    render(<GameClock />);
    expect(screen.getByTestId("game-clock").textContent).toBe("12:34");
  });

  it('renders "0:00" when game_clock is 0', () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({ game_clock: 0 }),
    });
    render(<GameClock />);
    expect(screen.getByTestId("game-clock").textContent).toBe("0:00");
  });

  it('renders "-1:30" when game_clock is -90 (negative pre-horn time)', () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({ game_clock: -90 }),
    });
    render(<GameClock />);
    expect(screen.getByTestId("game-clock").textContent).toBe("-1:30");
  });

  it('renders "1:00" when game_clock is 60', () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({ game_clock: 60 }),
    });
    render(<GameClock />);
    expect(screen.getByTestId("game-clock").textContent).toBe("1:00");
  });

  it('renders "61:01" when game_clock is 3661 (past 60 min)', () => {
    setGsiState({
      gsiStatus: "connected",
      liveState: makeLiveState({ game_clock: 3661 }),
    });
    render(<GameClock />);
    expect(screen.getByTestId("game-clock").textContent).toBe("61:01");
  });
});
