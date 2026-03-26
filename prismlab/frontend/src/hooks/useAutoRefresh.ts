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
import { api } from "../api/client";
import type { RecommendRequest } from "../types/recommendation";

/**
 * Auto-refresh hook that detects game events from GSI data and triggers
 * recommendation refreshes with rate limiting.
 *
 * Subscribes to gsiStore outside the render cycle (same pattern as useGsiSync).
 * Uses refs for mutable state to avoid stale closures.
 *
 * Event types detected (via detectTriggers):
 * - Phase transitions (10/20/35 min)
 * - Player death
 * - Roshan kill
 * - Tower destruction
 * - Gold swing (>= 2000g)
 *
 * Item purchases do NOT trigger auto-refresh (per D-02).
 *
 * Cooldown: max 1 auto-refresh per 2 minutes (120s).
 * Events during cooldown are queued (latest replaces previous).
 * Manual Re-Evaluate bypasses cooldown and resets the timer.
 *
 * Lane result auto-detects at 10:00 game clock from GPM vs role benchmark.
 */
export function useAutoRefresh(): void {
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
  const prevGsiStatusRef = useRef<string>("idle");

  /**
   * Fire a recommendation refresh -- replicates useRecommendation.recommend()
   * but using direct store access (hooks can't be called inside effects).
   */
  async function fireRefresh(event: TriggerEvent, currentNetWorth: number) {
    const game = useGameStore.getState();
    const recStore = useRecommendationStore.getState();

    // Guard: need hero and role
    if (!game.selectedHero || game.role === null) return;
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
      playstyle: game.playstyle ?? "balanced",
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

  // Main gsiStore subscription for event detection
  useEffect(() => {
    const unsubscribe = useGsiStore.subscribe((state) => {
      // Track GSI status transitions for reconnect handling
      const prevStatus = prevGsiStatusRef.current;
      prevGsiStatusRef.current = state.gsiStatus;

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
        return;
      }

      // Only detect during active game
      if (live.game_state !== "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS") return;

      // Don't auto-refresh if no recommendations exist yet
      if (!useRecommendationStore.getState().data) return;

      // Don't auto-refresh while a recommendation is loading
      if (useRecommendationStore.getState().isLoading) return;

      // --- Lane auto-detection at 10:00 (D-12, D-13, D-14, GSI-05) ---
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

      // --- Event detection (D-01, D-06) ---
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

      // --- Cooldown check (D-07, D-08) ---
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

    // --- Cooldown expiry check (1Hz interval) (D-08, D-10) ---
    const interval = setInterval(() => {
      const now = Date.now();

      // Update countdown display (D-10)
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
    };
  }, []);

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
