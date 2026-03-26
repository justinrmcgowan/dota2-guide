/**
 * GSI inventory-to-recommendation item matching utility.
 *
 * Maps GSI inventory/backpack item names to recommendation composite keys
 * (e.g., "laning-36") matching the format used by recommendationStore.togglePurchased.
 */

import type { RecommendResponse } from "../types/recommendation";

/**
 * Given a GSI inventory and backpack (arrays of item internal_name strings),
 * find all matching recommendation composite keys.
 *
 * GSI item names and recommendation item_name both use Item.internal_name format
 * (e.g., "power_treads", "black_king_bar"). Backend _normalize_item_name() strips
 * the "item_" prefix from GSI data. Exact string match is sufficient.
 *
 * @param gsiInventory - Array of item internal_name strings from GSI inventory slots
 * @param gsiBackpack - Array of item internal_name strings from GSI backpack slots
 * @param recommendations - Current RecommendResponse with phases and items
 * @returns Set of composite keys in format "${phase}-${item_id}"
 */
export function findPurchasedKeys(
  gsiInventory: string[],
  gsiBackpack: string[],
  recommendations: RecommendResponse,
): Set<string> {
  const result = new Set<string>();

  // Combine inventory + backpack, filter empty strings (GSI sends "" for empty slots)
  const ownedItems = new Set(
    [...gsiInventory, ...gsiBackpack].filter((name) => name !== ""),
  );

  if (ownedItems.size === 0) return result;

  // Check each recommendation phase/item against owned items
  for (const phase of recommendations.phases) {
    for (const item of phase.items) {
      if (ownedItems.has(item.item_name)) {
        result.add(`${phase.phase}-${item.item_id}`);
      }
    }
  }

  return result;
}
