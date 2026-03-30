import { useRecommendationStore } from "../stores/recommendationStore";
import { useGameStore } from "../stores/gameStore";
import { useGsiStore } from "../stores/gsiStore";
import { api } from "../api/client";
import type { RecommendRequest } from "../types/recommendation";
import { PLAYSTYLE_OPTIONS } from "../utils/constants";

function buildRequest(): RecommendRequest | null {
  const game = useGameStore.getState();
  if (!game.selectedHero || game.role === null) return null;

  const store = useRecommendationStore.getState();
  const purchasedItemIds = store.getPurchasedItemIds();
  const dismissedItemIds = store.getDismissedItemIds();
  const excludedItemIds = [...new Set([...purchasedItemIds, ...dismissedItemIds])];

  const playstyle =
    game.playstyle ?? PLAYSTYLE_OPTIONS[game.role]?.[0] ?? "Farm-first";

  // Read GSI game clock if available (Phase 36: PROM-02)
  const gsi = useGsiStore.getState();
  const gameTimeSec = gsi.liveState?.game_clock ?? null;

  return {
    hero_id: game.selectedHero.id,
    role: game.role,
    playstyle,
    side: game.side ?? "radiant",
    lane: game.lane ?? "safe",
    lane_opponents: game.laneOpponents.length > 0
      ? game.laneOpponents.map((h) => h.id)
      : game.opponents.filter(Boolean).map((h) => h!.id).slice(0, 2),
    allies: game.allies.filter(Boolean).map((h) => h!.id),
    all_opponents: game.opponents.filter(Boolean).map((h) => h!.id),
    lane_result: game.laneResult,
    damage_profile: game.damageProfile,
    enemy_items_spotted:
      game.enemyItemsSpotted.length > 0
        ? game.enemyItemsSpotted
        : undefined,
    purchased_items:
      excludedItemIds.length > 0 ? excludedItemIds : undefined,
    enemy_context:
      game.enemyContext.length > 0 ? game.enemyContext : undefined,

    // Phase 36: Time-aware fields (PROM-02, PROM-05)
    game_time_seconds: gameTimeSec != null && gameTimeSec > 0 ? Math.round(gameTimeSec) : undefined,
    turbo: game.turbo || undefined,  // omit if false (default)
  };
}

export function useRecommendation() {
  const data = useRecommendationStore((s) => s.data);
  const isLoading = useRecommendationStore((s) => s.isLoading);
  const isPartial = useRecommendationStore((s) => s.isPartial);
  const error = useRecommendationStore((s) => s.error);
  const selectedItemId = useRecommendationStore((s) => s.selectedItemId);
  const selectItem = useRecommendationStore((s) => s.selectItem);
  const clear = useRecommendationStore((s) => s.clear);

  /** Standard single-pass recommendation (manual button click). */
  const recommend = async () => {
    const request = buildRequest();
    if (!request) return;

    const store = useRecommendationStore.getState();
    store.clearResults();
    store.setLoading(true);

    try {
      const response = await api.recommend(request);
      store.setData(response);
    } catch (err) {
      store.setError(
        err instanceof Error ? err.message : "Failed to get recommendations",
      );
    }
  };

  /**
   * Two-pass recommendation for auto-trigger scenarios.
   * 1. Fire fast-mode request -> show partial results immediately
   * 2. Fire full auto/deep request -> merge over partial results
   */
  const recommendTwoPass = async () => {
    const request = buildRequest();
    if (!request) return;

    const store = useRecommendationStore.getState();
    // Don't interrupt an in-progress recommendation
    if (store.isLoading) return;

    store.clearResults();
    store.setLoading(true);

    // Pass 1: Fast mode (rules-only, <1s)
    const fastRequest = { ...request, mode: "fast" as const };
    try {
      const fastResponse = await api.recommend(fastRequest);
      // Show partial results immediately
      useRecommendationStore.getState().setPartialData(fastResponse);
    } catch {
      // Fast mode failed -- continue to full request anyway
    }

    // Pass 2: Full recommendation (auto mode, 2-15s)
    try {
      const fullResponse = await api.recommend(request);
      useRecommendationStore.getState().mergeData(fullResponse);
    } catch (err) {
      // If we already have partial data, keep it and clear the partial flag
      const current = useRecommendationStore.getState();
      if (current.data && current.isPartial) {
        // Keep partial data but clear the partial flag
        useRecommendationStore.getState().mergeData(current.data);
      } else {
        useRecommendationStore.getState().setError(
          err instanceof Error ? err.message : "Failed to get recommendations",
        );
      }
    }
  };

  return {
    recommend,
    recommendTwoPass,
    data,
    isLoading,
    isPartial,
    error,
    selectedItemId,
    selectItem,
    clear,
  };
}
