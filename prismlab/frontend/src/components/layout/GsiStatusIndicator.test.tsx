import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useGsiStore } from "../../stores/gsiStore";
import GsiStatusIndicator from "./GsiStatusIndicator";

describe("GsiStatusIndicator", () => {
  beforeEach(() => {
    useGsiStore.setState({
      wsStatus: "disconnected",
      gsiStatus: "idle",
      lastUpdate: null,
      liveState: null,
    });
  });

  it("renders GSI label text", () => {
    render(<GsiStatusIndicator />);
    expect(screen.getByText("GSI")).toBeTruthy();
  });

  it("shows gray dot when gsiStatus is idle", () => {
    render(<GsiStatusIndicator />);
    const dot = screen.getByTestId("gsi-dot");
    expect(dot.className).toContain("bg-gray-500");
  });

  it("shows green dot when gsiStatus is connected", () => {
    useGsiStore.setState({ gsiStatus: "connected" });
    render(<GsiStatusIndicator />);
    const dot = screen.getByTestId("gsi-dot");
    expect(dot.className).toContain("bg-radiant");
  });

  it("shows red dot when gsiStatus is lost", () => {
    useGsiStore.setState({ gsiStatus: "lost" });
    render(<GsiStatusIndicator />);
    const dot = screen.getByTestId("gsi-dot");
    expect(dot.className).toContain("bg-dire");
  });

  it("tooltip shows GSI status and WebSocket status", () => {
    useGsiStore.setState({ gsiStatus: "idle", wsStatus: "disconnected" });
    render(<GsiStatusIndicator />);
    const container = screen.getByTestId("gsi-status");
    const title = container.getAttribute("title") ?? "";
    expect(title).toContain("GSI: Idle");
    expect(title).toContain("WebSocket: disconnected");
  });

  it("tooltip shows game time when connected with liveState", () => {
    useGsiStore.setState({
      gsiStatus: "connected",
      wsStatus: "connected",
      lastUpdate: Date.now(),
      liveState: {
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
        game_clock: 600,
        game_state: "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
        team_side: "radiant",
        is_alive: true,
        timestamp: 1700000000,
      },
    });
    render(<GsiStatusIndicator />);
    const container = screen.getByTestId("gsi-status");
    const title = container.getAttribute("title") ?? "";
    expect(title).toContain("Game time: 10:00");
  });
});
