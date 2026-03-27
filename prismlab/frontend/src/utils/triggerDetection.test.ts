import { describe, it, expect } from "vitest";
import type { PreviousState, CurrentState } from "./triggerDetection";
import { detectTriggers } from "./triggerDetection";

function makeCurrentState(overrides: Partial<CurrentState> = {}): CurrentState {
  return {
    deaths: 0,
    net_worth: 5000,
    roshan_state: "alive",
    radiant_tower_count: 11,
    dire_tower_count: 11,
    game_clock: 0,
    ...overrides,
  };
}

function makePrevState(overrides: Partial<PreviousState> = {}): PreviousState {
  return {
    deaths: 0,
    netWorthAtLastRefresh: 5000,
    roshanState: "alive",
    radiantTowers: 11,
    direTowers: 11,
    ...overrides,
  };
}

describe("detectTriggers", () => {
  // --- Death detection ---

  it("detects death when current.deaths > prev.deaths", () => {
    const result = detectTriggers(
      makeCurrentState({ deaths: 2 }),
      makePrevState({ deaths: 1 }),
      new Set(),
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("death");
    expect(result!.message).toBe("Death -- reassessing priorities");
  });

  it("no death event when deaths unchanged", () => {
    const result = detectTriggers(
      makeCurrentState({ deaths: 1 }),
      makePrevState({ deaths: 1 }),
      new Set(),
    );
    // No trigger at all when nothing changed
    expect(result).toBeNull();
  });

  // --- Gold swing detection ---

  it("detects gold swing when net_worth delta >= 2000", () => {
    const result = detectTriggers(
      makeCurrentState({ net_worth: 7500 }),
      makePrevState({ netWorthAtLastRefresh: 5000 }),
      new Set(),
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("gold_swing");
    expect(result!.message).toContain("Gold swing:");
    expect(result!.message).toContain("+");
  });

  it("no gold swing when delta < 2000", () => {
    const result = detectTriggers(
      makeCurrentState({ net_worth: 6500 }),
      makePrevState({ netWorthAtLastRefresh: 5000 }),
      new Set(),
    );
    expect(result).toBeNull();
  });

  it("negative gold swing (lost gold) also triggers", () => {
    const result = detectTriggers(
      makeCurrentState({ net_worth: 3000 }),
      makePrevState({ netWorthAtLastRefresh: 5000 }),
      new Set(),
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("gold_swing");
    expect(result!.message).toContain("Gold swing:");
  });

  // --- Phase transition detection ---

  it("phase transition at 600s (10 min) fires once, sets it in firedPhases", () => {
    const firedPhases = new Set<number>();
    const result = detectTriggers(
      makeCurrentState({ game_clock: 600 }),
      makePrevState(),
      firedPhases,
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("phase_transition");
    expect(result!.message).toContain("10:00");
    expect(firedPhases.has(600)).toBe(true);
  });

  it("phase transition at 1200s (20 min) fires once", () => {
    const firedPhases = new Set<number>([600]); // 10-min already fired
    const result = detectTriggers(
      makeCurrentState({ game_clock: 1200 }),
      makePrevState(),
      firedPhases,
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("phase_transition");
    expect(result!.message).toContain("20:00");
    expect(firedPhases.has(1200)).toBe(true);
  });

  it("phase transition at 2100s (35 min) fires once", () => {
    const firedPhases = new Set<number>([600, 1200]);
    const result = detectTriggers(
      makeCurrentState({ game_clock: 2100 }),
      makePrevState(),
      firedPhases,
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("phase_transition");
    expect(result!.message).toContain("35:00");
    expect(firedPhases.has(2100)).toBe(true);
  });

  it("same phase transition does not fire twice (firedPhases prevents)", () => {
    const firedPhases = new Set<number>([600]);
    const result = detectTriggers(
      makeCurrentState({ game_clock: 700 }),
      makePrevState(),
      firedPhases,
    );
    // 600 already fired, no other trigger
    expect(result).toBeNull();
  });

  // --- Tower kill detection ---

  it("tower kill detected when tower count decreases", () => {
    const result = detectTriggers(
      makeCurrentState({ radiant_tower_count: 10, dire_tower_count: 11 }),
      makePrevState({ radiantTowers: 11, direTowers: 11 }),
      new Set(),
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("tower_kill");
    expect(result!.message).toBe("Tower destroyed -- map changed");
  });

  it("no tower event when counts unchanged", () => {
    const result = detectTriggers(
      makeCurrentState({ radiant_tower_count: 11, dire_tower_count: 11 }),
      makePrevState({ radiantTowers: 11, direTowers: 11 }),
      new Set(),
    );
    expect(result).toBeNull();
  });

  // --- Roshan kill detection ---

  it("roshan kill detected when roshan_state transitions from alive to respawn_base", () => {
    const result = detectTriggers(
      makeCurrentState({ roshan_state: "respawn_base" }),
      makePrevState({ roshanState: "alive" }),
      new Set(),
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("roshan_kill");
    expect(result!.message).toBe("Roshan killed -- updating");
  });

  it("no roshan event when roshan_state stays alive", () => {
    const result = detectTriggers(
      makeCurrentState({ roshan_state: "alive" }),
      makePrevState({ roshanState: "alive" }),
      new Set(),
    );
    expect(result).toBeNull();
  });

  // --- Priority order ---

  it("priority: phase_transition > death > roshan > tower > gold_swing", () => {
    // All triggers present at once -- phase_transition should win
    const firedPhases = new Set<number>();
    const result = detectTriggers(
      makeCurrentState({
        game_clock: 600,
        deaths: 2,
        roshan_state: "respawn_base",
        radiant_tower_count: 10,
        net_worth: 8000,
      }),
      makePrevState({
        deaths: 1,
        roshanState: "alive",
        radiantTowers: 11,
        netWorthAtLastRefresh: 5000,
      }),
      firedPhases,
    );
    expect(result).not.toBeNull();
    expect(result!.type).toBe("phase_transition");
  });

  // --- No events ---

  it("returns null when no events detected", () => {
    const result = detectTriggers(
      makeCurrentState(),
      makePrevState(),
      new Set(),
    );
    expect(result).toBeNull();
  });
});
