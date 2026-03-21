import { create } from "zustand";
import type { RecommendResponse } from "../types/recommendation";

interface RecommendationStore {
  data: RecommendResponse | null;
  isLoading: boolean;
  error: string | null;
  selectedItemId: string | null; // Composite key "phase-itemId" for expanded reasoning

  setData: (data: RecommendResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  selectItem: (phaseItemKey: string | null) => void;
  clear: () => void;
}

export const useRecommendationStore = create<RecommendationStore>()(
  (set, get) => ({
    data: null,
    isLoading: false,
    error: null,
    selectedItemId: null,

    setData: (data) => set({ data, error: null, isLoading: false }),

    setLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error, data: null, isLoading: false }),

    selectItem: (phaseItemKey) => {
      const current = get().selectedItemId;
      set({ selectedItemId: current === phaseItemKey ? null : phaseItemKey });
    },

    clear: () =>
      set({ data: null, isLoading: false, error: null, selectedItemId: null }),
  }),
);
