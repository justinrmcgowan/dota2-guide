import { describe, it, expect, beforeEach } from "vitest";
import { useGameStore } from "./gameStore";
import type { Hero } from "../types/hero";

const mockHero = (id: number, name = `Hero ${id}`): Hero => ({
  id,
  name,
  localized_name: name,
  internal_name: `npc_dota_hero_${id}`,
  primary_attr: "str",
  attack_type: "Melee",
  roles: [],
  base_health: 200,
  base_mana: 75,
  base_armor: 0,
  base_attack_min: 25,
  base_attack_max: 29,
  base_str: 22,
  base_agi: 22,
  base_int: 22,
  str_gain: 2,
  agi_gain: 2,
  int_gain: 2,
  attack_range: 150,
  move_speed: 300,
  img_url: "",
  icon_url: "",
});

beforeEach(() => {
  useGameStore.setState({
    selectedHero: null,
    allies: [null, null, null, null],
    opponents: [null, null, null, null, null],
    role: null,
    playstyle: null,
    side: null,
    lane: null,
    laneOpponents: [],
  });
});

describe("allies", () => {
  it("setAlly(0, hero) sets allies[0] to hero", () => {
    const hero = mockHero(1);
    useGameStore.getState().setAlly(0, hero);
    expect(useGameStore.getState().allies[0]).toEqual(hero);
  });

  it("clearAlly(0) sets allies[0] back to null", () => {
    const hero = mockHero(1);
    useGameStore.getState().setAlly(0, hero);
    useGameStore.getState().clearAlly(0);
    expect(useGameStore.getState().allies[0]).toBeNull();
  });

  it("setAlly with index out of range (4+) does not crash", () => {
    const hero = mockHero(1);
    expect(() => useGameStore.getState().setAlly(4, hero)).not.toThrow();
    expect(useGameStore.getState().allies).toHaveLength(4);
  });
});

describe("opponents", () => {
  it("setOpponent(2, hero) sets opponents[2] to hero", () => {
    const hero = mockHero(10);
    useGameStore.getState().setOpponent(2, hero);
    expect(useGameStore.getState().opponents[2]).toEqual(hero);
  });

  it("clearOpponent(2) sets opponents[2] to null", () => {
    const hero = mockHero(10);
    useGameStore.getState().setOpponent(2, hero);
    useGameStore.getState().clearOpponent(2);
    expect(useGameStore.getState().opponents[2]).toBeNull();
  });

  it("clearOpponent removes that hero from laneOpponents if it was present", () => {
    const hero = mockHero(10);
    useGameStore.getState().setOpponent(2, hero);
    useGameStore.getState().toggleLaneOpponent(hero);
    expect(useGameStore.getState().laneOpponents).toHaveLength(1);
    useGameStore.getState().clearOpponent(2);
    expect(useGameStore.getState().laneOpponents).toHaveLength(0);
  });
});

describe("role", () => {
  it("setRole(1) sets role to 1", () => {
    useGameStore.getState().setRole(1);
    expect(useGameStore.getState().role).toBe(1);
  });

  it("setRole(3) after playstyle 'Farm-first' (Pos 1 only) resets playstyle to null", () => {
    useGameStore.getState().setRole(1);
    useGameStore.getState().setPlaystyle("Farm-first");
    expect(useGameStore.getState().playstyle).toBe("Farm-first");
    useGameStore.getState().setRole(3);
    expect(useGameStore.getState().playstyle).toBeNull();
  });

  it("setRole(1) after playstyle 'Farm-first' (valid for Pos 1) keeps playstyle", () => {
    useGameStore.getState().setRole(1);
    useGameStore.getState().setPlaystyle("Farm-first");
    useGameStore.getState().setRole(1);
    expect(useGameStore.getState().playstyle).toBe("Farm-first");
  });
});

describe("playstyle", () => {
  it("setPlaystyle('Aggressive') sets playstyle to 'Aggressive'", () => {
    useGameStore.getState().setPlaystyle("Aggressive");
    expect(useGameStore.getState().playstyle).toBe("Aggressive");
  });
});

describe("side", () => {
  it("setSide('radiant') sets side to 'radiant'", () => {
    useGameStore.getState().setSide("radiant");
    expect(useGameStore.getState().side).toBe("radiant");
  });

  it("setSide('dire') sets side to 'dire'", () => {
    useGameStore.getState().setSide("dire");
    expect(useGameStore.getState().side).toBe("dire");
  });
});

describe("lane", () => {
  it("setLane('safe') sets lane to 'safe'", () => {
    useGameStore.getState().setLane("safe");
    expect(useGameStore.getState().lane).toBe("safe");
  });

  it("setLane('mid') sets lane to 'mid'", () => {
    useGameStore.getState().setLane("mid");
    expect(useGameStore.getState().lane).toBe("mid");
  });
});

describe("laneOpponents", () => {
  it("toggleLaneOpponent(hero) adds hero", () => {
    const hero = mockHero(20);
    useGameStore.getState().toggleLaneOpponent(hero);
    expect(useGameStore.getState().laneOpponents).toHaveLength(1);
    expect(useGameStore.getState().laneOpponents[0]).toEqual(hero);
  });

  it("toggling again removes hero", () => {
    const hero = mockHero(20);
    useGameStore.getState().toggleLaneOpponent(hero);
    useGameStore.getState().toggleLaneOpponent(hero);
    expect(useGameStore.getState().laneOpponents).toHaveLength(0);
  });

  it("does not add a third lane opponent when already 2", () => {
    const h1 = mockHero(20);
    const h2 = mockHero(21);
    const h3 = mockHero(22);
    useGameStore.getState().toggleLaneOpponent(h1);
    useGameStore.getState().toggleLaneOpponent(h2);
    useGameStore.getState().toggleLaneOpponent(h3);
    expect(useGameStore.getState().laneOpponents).toHaveLength(2);
  });

  it("clearLaneOpponents resets to empty array", () => {
    const h1 = mockHero(20);
    useGameStore.getState().toggleLaneOpponent(h1);
    useGameStore.getState().clearLaneOpponents();
    expect(useGameStore.getState().laneOpponents).toHaveLength(0);
  });
});

describe("existing behavior", () => {
  it("selectHero sets selectedHero", () => {
    const hero = mockHero(1);
    useGameStore.getState().selectHero(hero);
    expect(useGameStore.getState().selectedHero).toEqual(hero);
  });

  it("clearHero clears selectedHero", () => {
    const hero = mockHero(1);
    useGameStore.getState().selectHero(hero);
    useGameStore.getState().clearHero();
    expect(useGameStore.getState().selectedHero).toBeNull();
  });
});
