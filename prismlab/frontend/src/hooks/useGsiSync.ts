import { useEffect, useRef } from "react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { useRecommendationStore } from "../stores/recommendationStore";
import { findPurchasedKeys } from "../utils/itemMatching";
import type { Hero } from "../types/hero";

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
 * Cross-store synchronization hook that bridges GSI live state
 * to gameStore (hero/role) and recommendationStore (purchased items).
 *
 * Subscribes to gsiStore outside the render cycle to avoid cascading
 * re-renders. Uses refs for mutable data to prevent stale closures.
 *
 * @param heroes - Array of all heroes from useHeroes()
 */
export function useGsiSync(heroes: Hero[]): void {
  const heroesRef = useRef<Hero[]>(heroes);
  const prevHeroIdRef = useRef<number>(0);

  // Keep heroesRef in sync when the heroes prop changes
  useEffect(() => {
    heroesRef.current = heroes;
  }, [heroes]);

  useEffect(() => {
    const unsubscribe = useGsiStore.subscribe((state) => {
      // Guard: only process when GSI is connected
      if (state.gsiStatus !== "connected") return;

      const live = state.liveState;
      if (!live) return;

      // --- Hero auto-detection (D-01, D-02, GSI-02) ---
      if (live.hero_id > 0 && live.hero_id !== prevHeroIdRef.current) {
        const hero = heroesRef.current.find((h) => h.id === live.hero_id);
        if (hero) {
          useGameStore.getState().selectHero(hero);
          prevHeroIdRef.current = live.hero_id;

          // Role suggestion (D-02)
          const role = inferRole(hero);
          if (role !== null) {
            useGameStore.getState().setRole(role);
          }
        } else {
          console.warn(
            `GSI hero_id ${live.hero_id} not found in heroes list`,
          );
        }
      }

      // --- Item auto-marking (D-11, D-12, D-13, D-14, GSI-04) ---
      const recStore = useRecommendationStore.getState();
      const recommendations = recStore.data;
      if (!recommendations) return;

      const matchedKeys = findPurchasedKeys(
        live.items_inventory,
        live.items_backpack,
        recommendations,
      );

      const currentPurchased = recStore.purchasedItems;
      for (const key of matchedKeys) {
        // Only ADD items, never remove -- prevents flickering
        if (!currentPurchased.has(key)) {
          useRecommendationStore.getState().togglePurchased(key);
        }
      }
    });

    return unsubscribe;
  }, []);
}
