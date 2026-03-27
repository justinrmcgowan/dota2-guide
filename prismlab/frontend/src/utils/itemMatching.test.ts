import { describe, it, expect } from "vitest";
import { findPurchasedKeys } from "./itemMatching";
import type { RecommendResponse } from "../types/recommendation";

/** Helper to create a minimal RecommendResponse with given phases */
function makeRecommendations(
  phases: {
    phase: "starting" | "laning" | "core" | "late_game" | "situational";
    items: { item_id: number; item_name: string }[];
  }[],
): RecommendResponse {
  return {
    phases: phases.map((p) => ({
      phase: p.phase,
      items: p.items.map((i) => ({
        item_id: i.item_id,
        item_name: i.item_name,
        reasoning: "",
        priority: "core" as const,
        conditions: null,
        gold_cost: null,
      })),
      timing: null,
      gold_budget: null,
    })),
    overall_strategy: null,
    fallback: false,
    fallback_reason: null,
    model: null,
    latency_ms: null,
    neutral_items: [],
    timing_data: [],
    build_paths: [],
  };
}

describe("findPurchasedKeys", () => {
  it("returns empty Set for empty inventory and backpack", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "power_treads" }],
      },
    ]);
    const result = findPurchasedKeys([], [], recs);
    expect(result.size).toBe(0);
  });

  it("matches inventory item to recommendation composite key", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "power_treads" }],
      },
    ]);
    const result = findPurchasedKeys(["power_treads"], [], recs);
    expect(result.has("laning-36")).toBe(true);
    expect(result.size).toBe(1);
  });

  it("matches multiple items across multiple phases", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "power_treads" }],
      },
      {
        phase: "core",
        items: [{ item_id: 116, item_name: "black_king_bar" }],
      },
    ]);
    const result = findPurchasedKeys(
      ["power_treads", "black_king_bar"],
      [],
      recs,
    );
    expect(result.has("laning-36")).toBe(true);
    expect(result.has("core-116")).toBe(true);
    expect(result.size).toBe(2);
  });

  it("matches backpack items too", () => {
    const recs = makeRecommendations([
      {
        phase: "core",
        items: [{ item_id: 116, item_name: "black_king_bar" }],
      },
    ]);
    const result = findPurchasedKeys([], ["black_king_bar"], recs);
    expect(result.has("core-116")).toBe(true);
    expect(result.size).toBe(1);
  });

  it("ignores owned items not in recommendations", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "power_treads" }],
      },
    ]);
    const result = findPurchasedKeys(
      ["power_treads", "tango", "ward_observer"],
      [],
      recs,
    );
    expect(result.has("laning-36")).toBe(true);
    expect(result.size).toBe(1);
  });

  it("filters out empty string entries in GSI arrays", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "power_treads" }],
      },
    ]);
    const result = findPurchasedKeys(
      ["", "power_treads", ""],
      ["", ""],
      recs,
    );
    expect(result.has("laning-36")).toBe(true);
    expect(result.size).toBe(1);
  });

  it("adds all matching composite keys when same item appears in multiple phases", () => {
    const recs = makeRecommendations([
      {
        phase: "laning",
        items: [{ item_id: 36, item_name: "magic_wand" }],
      },
      {
        phase: "core",
        items: [{ item_id: 36, item_name: "magic_wand" }],
      },
    ]);
    const result = findPurchasedKeys(["magic_wand"], [], recs);
    expect(result.has("laning-36")).toBe(true);
    expect(result.has("core-36")).toBe(true);
    expect(result.size).toBe(2);
  });
});
