import { useRecommendationStore } from "../stores/recommendationStore";
import { useGameStore } from "../stores/gameStore";
import { api } from "../api/client";
import type { RecommendRequest } from "../types/recommendation";
import { PLAYSTYLE_OPTIONS } from "../utils/constants";

export function useRecommendation() {
  const data = useRecommendationStore((s) => s.data);
  const isLoading = useRecommendationStore((s) => s.isLoading);
  const error = useRecommendationStore((s) => s.error);
  const selectedItemId = useRecommendationStore((s) => s.selectedItemId);
  const selectItem = useRecommendationStore((s) => s.selectItem);
  const clear = useRecommendationStore((s) => s.clear);

  const recommend = async () => {
    const store = useRecommendationStore.getState();
    const game = useGameStore.getState();

    if (!game.selectedHero || game.role === null) return;

    // Preserve purchasedItems across re-evaluations
    store.clearResults();
    store.setLoading(true);

    // Get purchased item IDs for filtering
    const purchasedItemIds = store.getPurchasedItemIds();

    // Use selected playstyle, or first valid option for the role
    const playstyle =
      game.playstyle ?? PLAYSTYLE_OPTIONS[game.role]?.[0] ?? "Farm-first";

    const request: RecommendRequest = {
      hero_id: game.selectedHero.id,
      role: game.role,
      playstyle,
      side: game.side ?? "radiant",
      lane: game.lane ?? "safe",
      lane_opponents: game.laneOpponents.map((h) => h.id),
      allies: game.allies.filter(Boolean).map((h) => h!.id),

      // Mid-game adaptation fields (only include when present)
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
      store.setData(response);
    } catch (err) {
      store.setError(
        err instanceof Error ? err.message : "Failed to get recommendations",
      );
    }
  };

  return { recommend, data, isLoading, error, selectedItemId, selectItem, clear };
}
