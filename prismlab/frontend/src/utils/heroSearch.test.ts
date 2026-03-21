import { describe, it, expect } from "vitest";
import { createHeroSearcher, searchHeroes } from "./heroSearch";
import type { Hero } from "../types/hero";

// Minimal hero fixtures -- only the fields Fuse.js indexes on
const makeHero = (overrides: Partial<Hero> & { id: number; localized_name: string }): Hero => ({
  name: overrides.localized_name,
  internal_name: `npc_dota_hero_${overrides.localized_name.toLowerCase().replace(/[^a-z]/g, "_")}`,
  primary_attr: "agi",
  attack_type: "Melee",
  roles: [],
  base_health: 200,
  base_mana: 75,
  base_armor: 0,
  base_attack_min: 30,
  base_attack_max: 34,
  base_str: 20,
  base_agi: 20,
  base_int: 20,
  str_gain: 2,
  agi_gain: 2,
  int_gain: 2,
  attack_range: 150,
  move_speed: 300,
  img_url: "",
  icon_url: "",
  ...overrides,
});

const testHeroes: Hero[] = [
  makeHero({ id: 1, localized_name: "Anti-Mage", primary_attr: "agi", roles: ["Carry", "Escape"] }),
  makeHero({ id: 2, localized_name: "Axe", primary_attr: "str", roles: ["Initiator", "Durable"] }),
  makeHero({ id: 5, localized_name: "Crystal Maiden", primary_attr: "int", roles: ["Support", "Nuker"] }),
  makeHero({ id: 8, localized_name: "Juggernaut", primary_attr: "agi", roles: ["Carry", "Pusher"] }),
  makeHero({ id: 10, localized_name: "Morphling", primary_attr: "agi", roles: ["Carry", "Escape"] }),
  makeHero({ id: 25, localized_name: "Lina", primary_attr: "int", roles: ["Support", "Nuker"] }),
];

describe("heroSearch", () => {
  const fuse = createHeroSearcher(testHeroes);

  it("finds Anti-Mage when searching 'am'", () => {
    const results = searchHeroes(fuse, "am");
    const names = results.map((h) => h.localized_name);
    expect(names).toContain("Anti-Mage");
  });

  it("finds Juggernaut when searching 'jug'", () => {
    const results = searchHeroes(fuse, "jug");
    const names = results.map((h) => h.localized_name);
    expect(names).toContain("Juggernaut");
  });

  it("finds Crystal Maiden when searching 'crystal'", () => {
    const results = searchHeroes(fuse, "crystal");
    const names = results.map((h) => h.localized_name);
    expect(names).toContain("Crystal Maiden");
  });

  it("returns empty array for empty query", () => {
    const results = searchHeroes(fuse, "");
    expect(results).toEqual([]);
  });

  it("returns empty array for whitespace-only query", () => {
    const results = searchHeroes(fuse, "   ");
    expect(results).toEqual([]);
  });

  it("createHeroSearcher returns a usable Fuse instance", () => {
    const searcher = createHeroSearcher(testHeroes);
    const results = searchHeroes(searcher, "Lina");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].localized_name).toBe("Lina");
  });
});
