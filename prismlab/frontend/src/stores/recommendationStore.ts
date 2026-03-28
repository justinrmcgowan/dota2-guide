import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { RecommendResponse } from "../types/recommendation";

interface RecommendationStore {
  data: RecommendResponse | null;
  isLoading: boolean;
  error: string | null;
  selectedItemId: string | null; // Composite key "phase-itemId" for expanded reasoning
  purchasedItems: Set<string>; // Set of composite keys "phase-itemId"
  dismissedItems: Set<string>; // Set of composite keys for denied/dismissed items

  setData: (data: RecommendResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  selectItem: (phaseItemKey: string | null) => void;
  togglePurchased: (phaseItemKey: string) => void;
  dismissItem: (phaseItemKey: string) => void;
  getPurchasedItemIds: () => number[];
  getDismissedItemIds: () => number[];
  clearResults: () => void; // Clears data/error/selection but KEEPS purchasedItems/dismissed
  clear: () => void; // Full reset including purchasedItems/dismissed
}

export const useRecommendationStore = create<RecommendationStore>()(
  persist(
    (set, get) => ({
    data: null,
    isLoading: false,
    error: null,
    selectedItemId: null,
    purchasedItems: new Set<string>(),
    dismissedItems: new Set<string>(),

    setData: (data) => {
      // Re-apply purchased state: match old purchased item_ids to new phase keys
      const oldPurchased = get().purchasedItems;
      const oldItemIds = new Set<number>();
      for (const key of oldPurchased) {
        const parts = key.split("-");
        const id = parseInt(parts[parts.length - 1], 10);
        if (!isNaN(id)) oldItemIds.add(id);
      }

      const newPurchased = new Set<string>();
      if (oldItemIds.size > 0) {
        for (const phase of data.phases) {
          for (const item of phase.items) {
            if (oldItemIds.has(item.item_id)) {
              newPurchased.add(`${phase.phase}-${item.item_id}`);
            }
          }
        }
      }

      set({
        data,
        error: null,
        isLoading: false,
        purchasedItems: newPurchased.size > 0 ? newPurchased : oldPurchased,
      });
    },

    setLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error, data: null, isLoading: false }),

    selectItem: (phaseItemKey) => {
      const current = get().selectedItemId;
      set({ selectedItemId: current === phaseItemKey ? null : phaseItemKey });
    },

    togglePurchased: (phaseItemKey) => {
      const next = new Set(get().purchasedItems);
      if (next.has(phaseItemKey)) {
        next.delete(phaseItemKey);
      } else {
        next.add(phaseItemKey);
      }
      set({ purchasedItems: next });
    },

    dismissItem: (phaseItemKey) => {
      const next = new Set(get().dismissedItems);
      next.add(phaseItemKey);
      set({ dismissedItems: next });
    },

    getPurchasedItemIds: () => {
      const keys = get().purchasedItems;
      const idSet = new Set<number>();
      for (const key of keys) {
        const parts = key.split("-");
        const idStr = parts[parts.length - 1];
        const id = parseInt(idStr, 10);
        if (!isNaN(id)) {
          idSet.add(id);
        }
      }
      return [...idSet];
    },

    getDismissedItemIds: () => {
      const keys = get().dismissedItems;
      const idSet = new Set<number>();
      for (const key of keys) {
        const parts = key.split("-");
        const idStr = parts[parts.length - 1];
        const id = parseInt(idStr, 10);
        if (!isNaN(id)) {
          idSet.add(id);
        }
      }
      return [...idSet];
    },

    clearResults: () =>
      set({ data: null, error: null, selectedItemId: null }),

    clear: () =>
      set({
        data: null,
        isLoading: false,
        error: null,
        selectedItemId: null,
        purchasedItems: new Set<string>(),
        dismissedItems: new Set<string>(),
      }),
    }),
    {
      name: "prismlab-recommendations",
      version: 1,
      storage: {
        getItem: (name: string) => {
          const raw = localStorage.getItem(name);
          if (!raw) return null;
          const parsed = JSON.parse(raw);
          if (parsed?.state?.purchasedItems) {
            parsed.state.purchasedItems = new Set(parsed.state.purchasedItems);
          }
          if (parsed?.state?.dismissedItems) {
            parsed.state.dismissedItems = new Set(parsed.state.dismissedItems);
          }
          return parsed;
        },
        setItem: (name: string, value: unknown) => {
          const serialized = JSON.stringify(value, (_key, val) =>
            val instanceof Set ? [...val] : val,
          );
          localStorage.setItem(name, serialized);
        },
        removeItem: (name: string) => localStorage.removeItem(name),
      },
    },
  ),
);
