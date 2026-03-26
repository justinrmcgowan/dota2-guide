import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { useRecommendationStore } from "../stores/recommendationStore";
import type { Hero } from "../types/hero";
import type { RecommendResponse } from "../types/recommendation";
import type { GsiLiveState } from "../stores/gsiStore";

// Must import after stores so the mock is in scope
vi.mock("../utils/itemMatching", () => ({
  findPurchasedKeys: vi.fn(() => new Set<string>()),
}));

import { findPurchasedKeys } from "../utils/itemMatching";
import { useGsiSync } from "./useGsiSync";

const mockFindPurchasedKeys = findPurchasedKeys as ReturnType<typeof vi.fn>;

function makeHero(overrides: Partial<Hero> = {}): Hero {
  return {
    id: 1,
    name: "npc_dota_hero_antimage",
    localized_name: "Anti-Mage",
    internal_name: "antimage",
    primary_attr: "agi",
    attack_type: "Melee",
    roles: ["Carry", "Escape", "Nuker"],
    base_health: 200,
    base_mana: 75,
    base_armor: 0,
    base_attack_min: 29,
    base_attack_max: 33,
    base_str: 23,
    base_agi: 24,
    base_int: 12,
    str_gain: 1.3,
    agi_gain: 2.8,
    int_gain: 1.8,
    attack_range: 150,
    move_speed: 310,
    img_url: "",
    icon_url: "",
    ...overrides,
  };
}

function makeLiveState(overrides: Partial<GsiLiveState> = {}): GsiLiveState {
  return {
    hero_name: "npc_dota_hero_antimage",
    hero_id: 1,
    hero_level: 1,
    gold: 600,
    gpm: 0,
    net_worth: 600,
    kills: 0,
    deaths: 0,
    assists: 0,
    items_inventory: [],
    items_backpack: [],
    items_neutral: "",
    game_clock: 0,
    game_state: "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    team_side: "radiant",
    is_alive: true,
    timestamp: Date.now(),
    ...overrides,
  };
}

function makeRecommendations(): RecommendResponse {
  return {
    phases: [
      {
        phase: "laning",
        items: [
          {
            item_id: 36,
            item_name: "power_treads",
            reasoning: "test",
            priority: "core",
            conditions: null,
            gold_cost: 1400,
          },
          {
            item_id: 116,
            item_name: "bfury",
            reasoning: "test",
            priority: "core",
            conditions: null,
            gold_cost: 4100,
          },
        ],
        timing: null,
        gold_budget: null,
      },
    ],
    overall_strategy: null,
    fallback: false,
    model: null,
    latency_ms: null,
    neutral_items: [],
  };
}

describe("useGsiSync", () => {
  beforeEach(() => {
    // Reset all stores to clean defaults (don't pass true -- keep action methods)
    useGsiStore.setState({
      wsStatus: "disconnected",
      gsiStatus: "idle",
      lastUpdate: null,
      liveState: null,
    });
    useGameStore.setState(
      {
        selectedHero: null,
        role: null,
        playstyle: null,
      },
    );
    useRecommendationStore.setState(
      {
        data: null,
        purchasedItems: new Set<string>(),
      },
    );
    mockFindPurchasedKeys.mockClear();
    mockFindPurchasedKeys.mockReturnValue(new Set<string>());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("auto-detects hero when gsiStore.liveState.hero_id matches a hero in the list", () => {
    const hero = makeHero({ id: 1, roles: ["Carry"] });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 1 }));
    });

    expect(useGameStore.getState().selectedHero).toEqual(hero);
    unmount();
  });

  it("does NOT set selectedHero when hero_id is not found in heroes list", () => {
    const hero = makeHero({ id: 99 });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 999 }));
    });

    expect(useGameStore.getState().selectedHero).toBeNull();
    unmount();
  });

  it("sets role to 1 when hero.roles includes 'Carry'", () => {
    const hero = makeHero({ id: 1, roles: ["Carry", "Escape"] });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 1 }));
    });

    expect(useGameStore.getState().role).toBe(1);
    unmount();
  });

  it("suggests role 5 for a Support hero without Disabler", () => {
    const hero = makeHero({ id: 50, roles: ["Support"] });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 50 }));
    });

    expect(useGameStore.getState().role).toBe(5);
    unmount();
  });

  it("does NOT update gameStore when gsiStatus is not 'connected'", () => {
    const hero = makeHero({ id: 1 });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    // Set liveState directly without going through updateLiveState
    // (which would set gsiStatus to "connected")
    act(() => {
      useGsiStore.setState({
        gsiStatus: "idle",
        liveState: makeLiveState({ hero_id: 1 }),
      });
    });

    expect(useGameStore.getState().selectedHero).toBeNull();
    unmount();
  });

  it("does NOT re-select hero when hero_id does not change between updates", () => {
    const hero = makeHero({ id: 1, roles: ["Carry"] });
    // Track selectHero calls via a counter
    let selectCount = 0;
    const origSelectHero = useGameStore.getState().selectHero;
    useGameStore.setState({
      selectHero: (h: Hero) => {
        selectCount++;
        origSelectHero(h);
      },
    });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    // First update
    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 1 }));
    });
    expect(selectCount).toBe(1);

    // Second update with same hero_id but different gold
    act(() => {
      useGsiStore
        .getState()
        .updateLiveState(makeLiveState({ hero_id: 1, gold: 700 }));
    });
    expect(selectCount).toBe(1); // Still 1 -- guard prevented redundant call

    unmount();
  });

  it("calls togglePurchased for items matched by findPurchasedKeys", () => {
    const hero = makeHero({ id: 1, roles: ["Carry"] });

    const recs = makeRecommendations();
    useRecommendationStore.setState({ data: recs });

    mockFindPurchasedKeys.mockReturnValue(new Set(["laning-36"]));

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(
        makeLiveState({
          hero_id: 1,
          items_inventory: ["power_treads"],
        }),
      );
    });

    expect(mockFindPurchasedKeys).toHaveBeenCalledWith(
      ["power_treads"],
      [],
      recs,
    );
    expect(useRecommendationStore.getState().purchasedItems.has("laning-36")).toBe(true);
    unmount();
  });

  it("does NOT toggle when key is already in purchasedItems", () => {
    const hero = makeHero({ id: 1, roles: ["Carry"] });

    const recs = makeRecommendations();
    useRecommendationStore.setState({
      data: recs,
      purchasedItems: new Set(["laning-36"]),
    });

    mockFindPurchasedKeys.mockReturnValue(new Set(["laning-36"]));

    // Track togglePurchased calls
    let toggleCount = 0;
    const origToggle = useRecommendationStore.getState().togglePurchased;
    useRecommendationStore.setState({
      togglePurchased: (key: string) => {
        toggleCount++;
        origToggle(key);
      },
    });

    const { unmount } = renderHook(() => useGsiSync([hero]));

    act(() => {
      useGsiStore.getState().updateLiveState(
        makeLiveState({
          hero_id: 1,
          items_inventory: ["power_treads"],
        }),
      );
    });

    expect(toggleCount).toBe(0); // Already purchased -- skip
    unmount();
  });

  it("cleans up subscription on unmount", () => {
    const hero = makeHero({ id: 1, roles: ["Carry"] });

    const { unmount } = renderHook(() => useGsiSync([hero]));
    unmount();

    // After unmount, store updates should not trigger selectHero
    act(() => {
      useGsiStore.getState().updateLiveState(makeLiveState({ hero_id: 1 }));
    });

    expect(useGameStore.getState().selectedHero).toBeNull();
  });
});
