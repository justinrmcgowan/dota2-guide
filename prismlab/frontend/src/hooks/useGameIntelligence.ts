import { useEffect, useRef } from "react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { useRecommendationStore } from "../stores/recommendationStore";
import { useRefreshStore } from "../stores/refreshStore";
import {
  detectTriggers,
  type PreviousState,
  type TriggerEvent,
} from "../utils/triggerDetection";
import { detectLaneResult } from "../utils/laneBenchmarks";
import { findPurchasedKeys } from "../utils/itemMatching";
import { HERO_PLAYSTYLE_MAP } from "../utils/heroPlaystyles";
import { PLAYSTYLE_OPTIONS } from "../utils/constants";
import { api } from "../api/client";
import type { Hero } from "../types/hero";
import type { RecommendRequest } from "../types/recommendation";

/**
 * Best-effort role inference from hero roles array.
 * Returns Dota 2 position number (1-5) or null if ambiguous.
 */
function inferRole(hero: Hero): number | null {
  const roles = hero.roles.map((r) => r.toLowerCase());
  if (roles.includes("carry")) return 1;
  if (
    roles.includes("nuker") &&
    !roles.includes("support") &&
    !roles.includes("durable")
  )
    return 2;
  if (roles.includes("initiator") && roles.includes("durable")) return 3;
  if (roles.includes("support") && roles.includes("disabler")) return 4;
  if (roles.includes("support")) return 5;
  return null; // Ambiguous -- leave unselected, user can choose
}

/**
 * Suggest a playstyle based on hero + role.
 * Checks HERO_PLAYSTYLE_MAP first, falls back to first valid
 * playstyle for the role from PLAYSTYLE_OPTIONS.
 */
function suggestPlaystyle(heroId: number, role: number): string {
  const key = `${heroId}-${role}`;
  const mapped = HERO_PLAYSTYLE_MAP[key];
  if (mapped) return mapped;
  // Fallback: first valid playstyle for this role
  return PLAYSTYLE_OPTIONS[role]?.[0] ?? "balanced";
}

/** 10 minutes -- matches Dota 2's reconnect grace period (D-11). */
const DISCONNECT_TIMEOUT_MS = 10 * 60 * 1000;

/**
 * Consolidated GSI intelligence hook that replaces both useGsiSync and
 * useAutoRefresh. Bridges GSI live state to gameStore (hero/role/playstyle),
 * recommendationStore (purchased items), and refreshStore (event triggers).
 *
 * Uses separate gsiStore.subscribe() calls co-located in the same hook
 * (not merged into a single callback) to prevent cross-store write cascades.
 *
 * Processing order within the main subscription:
 * 1. Hero auto-detection + role inference + playstyle auto-suggest
 * 2. Item auto-marking
 * 3. Lane auto-detection (at 10:00 game clock)
 * 4. Event detection (triggers, cooldown, queue)
 *
 * @param heroes - Array of all heroes from useHeroes()
 */
export function useGameIntelligence(heroes: Hero[]): void {
  // --- Refs (combined from both hooks) ---
  const heroesRef = useRef<Hero[]>(heroes);
  const prevHeroIdRef = useRef<number>(0);
  const prevStateRef = useRef<PreviousState>({
    deaths: 0,
    netWorthAtLastRefresh: 0,
    roshanState: "alive",
    radiantTowers: 11,
    direTowers: 11,
  });
  const firedPhasesRef = useRef<Set<number>>(new Set());
  const cooldownEndRef = useRef<number>(0);
  const queuedEventRef = useRef<TriggerEvent | null>(null);
  const laneAutoDetectedRef = useRef<boolean>(false);
  const prevMatchIdRef = useRef<string>("");
  const prevGsiStatusRef = useRef<string>("idle");
  const disconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /**
   * Fire a recommendation refresh -- replicates useRecommendation.recommend()
   * but using direct store access (hooks can't be called inside effects).
   */
  async function fireRefresh(event: TriggerEvent, currentNetWorth: number) {
    const game = useGameStore.getState();
    const recStore = useRecommendationStore.getState();

    // Guard: need hero, role, and playstyle
    if (!game.selectedHero || game.role === null || game.playstyle === null)
      return;
    // Guard: don't overlap with in-progress recommendation
    if (recStore.isLoading) return;

    // Set cooldown immediately (before async work)
    cooldownEndRef.current = Date.now() + 120_000;
    useRefreshStore.getState().startCooldown();

    // Update prev state baseline
    prevStateRef.current.netWorthAtLastRefresh = currentNetWorth;
    const live = useGsiStore.getState().liveState;
    if (live) {
      prevStateRef.current.deaths = live.deaths;
      prevStateRef.current.roshanState = live.roshan_state;
      prevStateRef.current.radiantTowers = live.radiant_tower_count;
      prevStateRef.current.direTowers = live.dire_tower_count;
    }

    // Clear queue
    queuedEventRef.current = null;
    useRefreshStore.getState().clearQueue();

    // Show toast
    useRefreshStore.getState().showToast(event.message);

    // Fire recommendation
    recStore.clearResults();
    recStore.setLoading(true);

    const purchasedItemIds = recStore.getPurchasedItemIds();

    const request: RecommendRequest = {
      hero_id: game.selectedHero.id,
      role: game.role,
      playstyle: game.playstyle ?? PLAYSTYLE_OPTIONS[game.role]?.[0] ?? "Farm-first",
      side: game.side ?? "radiant",
      lane: game.lane ?? "safe",
      lane_opponents: game.laneOpponents.map((h) => h.id),
      allies: game.allies.filter(Boolean).map((h) => h!.id),
      lane_result: game.laneResult,
      damage_profile: game.damageProfile,
      enemy_items_spotted:
        game.enemyItemsSpotted.length > 0
          ? game.enemyItemsSpotted
          : undefined,
      purchased_items:
        purchasedItemIds.length > 0 ? purchasedItemIds : undefined,
      enemy_context:
        game.enemyContext.length > 0 ? game.enemyContext : undefined,
    };

    try {
      const response = await api.recommend(request);
      useRecommendationStore.getState().setData(response);
    } catch (err) {
      useRecommendationStore
        .getState()
        .setError(
          err instanceof Error
            ? err.message
            : "Failed to get recommendations",
        );
    }
  }

  // Keep heroesRef in sync when the heroes prop changes
  useEffect(() => {
    heroesRef.current = heroes;
  }, [heroes]);

  // --- FIRST useEffect: gsiStore subscription ---
  // Handles: hero detection, playstyle auto-suggest, item marking,
  // lane detection, event detection, cooldown, 1Hz interval
  useEffect(() => {
    const unsubscribe = useGsiStore.subscribe((state) => {
      // Track GSI status transitions for reconnect handling
      const prevStatus = prevGsiStatusRef.current;
      prevGsiStatusRef.current = state.gsiStatus;

      // --- Disconnect timeout management (D-11, D-12, D-13) ---
      if (state.gsiStatus === "reconnecting" && !disconnectTimerRef.current) {
        // Start 10-minute countdown
        disconnectTimerRef.current = setTimeout(() => {
          // Auto-clear match state (D-12)
          useGameStore.getState().clear();
          useRecommendationStore.getState().clear();
          useRefreshStore.getState().resetCooldown();
          useGsiStore.getState().clearLiveState(); // Sets gsiStatus to "idle"

          // Reset refs
          prevHeroIdRef.current = 0;
          prevMatchIdRef.current = "";
          firedPhasesRef.current = new Set();
          laneAutoDetectedRef.current = false;
          cooldownEndRef.current = 0;
          queuedEventRef.current = null;
          prevStateRef.current = {
            deaths: 0,
            netWorthAtLastRefresh: 0,
            roshanState: "alive",
            radiantTowers: 11,
            direTowers: 11,
          };
          disconnectTimerRef.current = null;

          // Show "Session expired" toast (D-12)
          useRefreshStore
            .getState()
            .showToast(
              "Session expired -- match state cleared after 10 minutes",
            );
        }, DISCONNECT_TIMEOUT_MS);
      }

      // Cancel timer on reconnect (D-13)
      if (state.gsiStatus === "connected" && disconnectTimerRef.current) {
        clearTimeout(disconnectTimerRef.current);
        disconnectTimerRef.current = null;
      }

      // Guard: only process when GSI is connected
      if (state.gsiStatus !== "connected") return;
      const live = state.liveState;
      if (!live) return;

      // Handle GSI reconnect: sync prev state to current to avoid false triggers
      if (prevStatus !== "connected") {
        prevStateRef.current = {
          ...prevStateRef.current,
          deaths: live.deaths,
          roshanState: live.roshan_state,
          radiantTowers: live.radiant_tower_count,
          direTowers: live.dire_tower_count,
        };
        // Still continue processing below (hero detection should work on reconnect)
      }

      // --- 0. New game detection (match_id change) ---
      const matchId = live.match_id;
      if (matchId && prevMatchIdRef.current && matchId !== prevMatchIdRef.current) {
        const isHeroSelection = live.game_state === "DOTA_GAMERULES_STATE_HERO_SELECTION";
        if (!isHeroSelection) {
          console.info(
            `New match detected (${prevMatchIdRef.current} -> ${matchId}) without hero selection state (state: ${live.game_state})`,
          );
        }

        // Full match reset
        useGameStore.getState().clear();
        useRecommendationStore.getState().clear();
        useRefreshStore.getState().resetCooldown();

        // Reset all refs to initial state
        prevHeroIdRef.current = 0;
        firedPhasesRef.current = new Set();
        laneAutoDetectedRef.current = false;
        cooldownEndRef.current = 0;
        queuedEventRef.current = null;
        prevStateRef.current = {
          deaths: 0,
          netWorthAtLastRefresh: 0,
          roshanState: "alive",
          radiantTowers: 11,
          direTowers: 11,
        };
      }
      // Always track the latest match ID
      if (matchId) {
        prevMatchIdRef.current = matchId;
      }

      // --- 1. Hero auto-detection + role inference + playstyle auto-suggest ---
      if (live.hero_id > 0 && live.hero_id !== prevHeroIdRef.current) {
        const hero = heroesRef.current.find((h) => h.id === live.hero_id);
        if (hero) {
          useGameStore.getState().selectHero(hero);
          prevHeroIdRef.current = live.hero_id;

          // Role suggestion
          const role = inferRole(hero);
          if (role !== null) {
            useGameStore.getState().setRole(role);
            // Playstyle auto-suggest: setRole may clear playstyle if invalid,
            // so immediately set the suggested playstyle after setRole
            const playstyle = suggestPlaystyle(hero.id, role);
            useGameStore.getState().setPlaystyle(playstyle);
          }
        } else {
          console.warn(
            `GSI hero_id ${live.hero_id} not found in heroes list`,
          );
        }
      }

      // --- 2. Item auto-marking ---
      const recStore = useRecommendationStore.getState();
      const recommendations = recStore.data;
      if (recommendations) {
        // Detect consumed items (not in inventory but hero has the buff)
        const consumedItems = new Set<string>();
        if (live.has_aghanims_shard) consumedItems.add("aghanims_shard");
        if (live.has_aghanims_scepter) consumedItems.add("ultimate_scepter");

        const matchedKeys = findPurchasedKeys(
          live.items_inventory,
          live.items_backpack,
          recommendations,
          consumedItems,
        );

        const currentPurchased = recStore.purchasedItems;
        for (const key of matchedKeys) {
          // Only ADD items, never remove -- prevents flickering
          if (!currentPurchased.has(key)) {
            useRecommendationStore.getState().togglePurchased(key);
          }
        }
      }

      // Guards for event-related processing: only during active game,
      // with existing recommendations, not loading
      if (live.game_state !== "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS") return;
      if (!useRecommendationStore.getState().data) return;
      if (useRecommendationStore.getState().isLoading) return;

      // On reconnect, skip event detection on the first tick to avoid false triggers
      if (prevStatus !== "connected") return;

      // --- 3. Lane auto-detection at 10:00 ---
      if (live.game_clock >= 600 && !laneAutoDetectedRef.current) {
        const role = useGameStore.getState().role;
        if (role !== null) {
          const result = detectLaneResult(live.gpm, role);
          useGameStore.getState().setLaneResult(result);
          laneAutoDetectedRef.current = true;
          useRefreshStore.getState().setLaneAutoDetected(true);
          // The 10:00 phase transition trigger will handle the re-evaluation
        }
      }

      // --- 4. Event detection ---
      const currentState = {
        deaths: live.deaths,
        net_worth: live.net_worth,
        roshan_state: live.roshan_state,
        radiant_tower_count: live.radiant_tower_count,
        dire_tower_count: live.dire_tower_count,
        game_clock: live.game_clock,
      };

      const event = detectTriggers(
        currentState,
        prevStateRef.current,
        firedPhasesRef.current,
      );

      if (!event) {
        // Update non-trigger prev state (deaths, roshan, towers)
        // But NOT netWorthAtLastRefresh -- that only resets on refresh (D-04)
        prevStateRef.current.deaths = live.deaths;
        prevStateRef.current.roshanState = live.roshan_state;
        prevStateRef.current.radiantTowers = live.radiant_tower_count;
        prevStateRef.current.direTowers = live.dire_tower_count;
        return;
      }

      // --- Cooldown check ---
      const now = Date.now();
      if (now < cooldownEndRef.current) {
        // Queue the event (latest replaces previous per D-08)
        queuedEventRef.current = event;
        useRefreshStore.getState().queueEvent(event);
        // Update prev state for non-gold fields to avoid re-detection
        prevStateRef.current.deaths = live.deaths;
        prevStateRef.current.roshanState = live.roshan_state;
        prevStateRef.current.radiantTowers = live.radiant_tower_count;
        prevStateRef.current.direTowers = live.dire_tower_count;
        return;
      }

      // Fire immediately
      fireRefresh(event, live.net_worth);
    });

    // --- Cooldown expiry check (1Hz interval) ---
    const interval = setInterval(() => {
      const now = Date.now();

      // Update countdown display
      useRefreshStore.getState().tick(now);

      // Check if queued event should fire
      const queued = queuedEventRef.current;
      if (queued && now >= cooldownEndRef.current) {
        queuedEventRef.current = null;
        useRefreshStore.getState().clearQueue();

        // Get current net worth for baseline reset
        const live = useGsiStore.getState().liveState;
        const nw =
          live?.net_worth ?? prevStateRef.current.netWorthAtLastRefresh;
        fireRefresh(queued, nw);
      }
    }, 1000);

    return () => {
      unsubscribe();
      clearInterval(interval);
      if (disconnectTimerRef.current) clearTimeout(disconnectTimerRef.current);
    };
  }, []);

  // --- SECOND useEffect: recommendationStore subscription ---
  // Track when manual recommend completes to reset cooldown (D-09)
  useEffect(() => {
    let wasLoading = false;
    const unsubscribe = useRecommendationStore.subscribe((state) => {
      // Detect transition from loading -> not loading (recommend completed)
      if (wasLoading && !state.isLoading && state.data) {
        // Reset cooldown timer (D-09)
        cooldownEndRef.current = Date.now() + 120_000;
        useRefreshStore.getState().startCooldown();

        // Reset gold baseline (D-04)
        const live = useGsiStore.getState().liveState;
        if (live) {
          prevStateRef.current.netWorthAtLastRefresh = live.net_worth;
        }

        // Clear any queued event
        queuedEventRef.current = null;
        useRefreshStore.getState().clearQueue();
      }
      wasLoading = state.isLoading;
    });
    return unsubscribe;
  }, []);
}
