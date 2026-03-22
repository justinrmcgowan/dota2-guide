import { describe, it, expect, beforeEach } from "vitest";
import { useRecommendationStore } from "./recommendationStore";
import type { RecommendResponse } from "../types/recommendation";

const mockResponse: RecommendResponse = {
  phases: [
    {
      phase: "laning",
      items: [
        {
          item_id: 48,
          item_name: "Power Treads",
          reasoning: "Attribute switching for lane sustain",
          priority: "core",
          conditions: null,
          gold_cost: 1400,
        },
      ],
      timing: null,
      gold_budget: null,
    },
  ],
  overall_strategy: "Test strategy",
  fallback: false,
  model: "test-model",
  latency_ms: 100,
};

beforeEach(() => {
  useRecommendationStore.setState({
    data: null,
    isLoading: false,
    error: null,
    selectedItemId: null,
    purchasedItems: new Set(),
  });
});

describe("setData", () => {
  it("stores the response", () => {
    useRecommendationStore.getState().setData(mockResponse);
    expect(useRecommendationStore.getState().data).toEqual(mockResponse);
  });

  it("clears error when data is set", () => {
    useRecommendationStore.setState({ error: "previous error" });
    useRecommendationStore.getState().setData(mockResponse);
    expect(useRecommendationStore.getState().error).toBeNull();
  });

  it("clears isLoading when data is set", () => {
    useRecommendationStore.setState({ isLoading: true });
    useRecommendationStore.getState().setData(mockResponse);
    expect(useRecommendationStore.getState().isLoading).toBe(false);
  });
});

describe("setError", () => {
  it("stores error message", () => {
    useRecommendationStore.getState().setError("Something went wrong");
    expect(useRecommendationStore.getState().error).toBe("Something went wrong");
  });

  it("clears data when error is set", () => {
    useRecommendationStore.setState({ data: mockResponse });
    useRecommendationStore.getState().setError("fail");
    expect(useRecommendationStore.getState().data).toBeNull();
  });

  it("clears isLoading when error is set", () => {
    useRecommendationStore.setState({ isLoading: true });
    useRecommendationStore.getState().setError("fail");
    expect(useRecommendationStore.getState().isLoading).toBe(false);
  });
});

describe("setLoading", () => {
  it("sets isLoading to true", () => {
    useRecommendationStore.getState().setLoading(true);
    expect(useRecommendationStore.getState().isLoading).toBe(true);
  });

  it("sets isLoading to false", () => {
    useRecommendationStore.setState({ isLoading: true });
    useRecommendationStore.getState().setLoading(false);
    expect(useRecommendationStore.getState().isLoading).toBe(false);
  });
});

describe("selectItem", () => {
  it("sets selectedItemId when currently null", () => {
    useRecommendationStore.getState().selectItem("laning-48");
    expect(useRecommendationStore.getState().selectedItemId).toBe("laning-48");
  });

  it("toggles to null when same key is selected (deselect)", () => {
    useRecommendationStore.getState().selectItem("laning-48");
    useRecommendationStore.getState().selectItem("laning-48");
    expect(useRecommendationStore.getState().selectedItemId).toBeNull();
  });

  it("switches selection when different key is selected", () => {
    useRecommendationStore.getState().selectItem("laning-48");
    useRecommendationStore.getState().selectItem("core-1");
    expect(useRecommendationStore.getState().selectedItemId).toBe("core-1");
  });
});

describe("togglePurchased", () => {
  it("adds key to purchasedItems set", () => {
    useRecommendationStore.getState().togglePurchased("laning-48");
    expect(useRecommendationStore.getState().purchasedItems.has("laning-48")).toBe(true);
  });

  it("removes key from purchasedItems when toggled again", () => {
    useRecommendationStore.getState().togglePurchased("laning-48");
    useRecommendationStore.getState().togglePurchased("laning-48");
    expect(useRecommendationStore.getState().purchasedItems.has("laning-48")).toBe(false);
    expect(useRecommendationStore.getState().purchasedItems.size).toBe(0);
  });
});

describe("getPurchasedItemIds", () => {
  it("extracts numeric IDs from composite keys like 'laning-48'", () => {
    useRecommendationStore.getState().togglePurchased("laning-48");
    const ids = useRecommendationStore.getState().getPurchasedItemIds();
    expect(ids).toEqual([48]);
  });

  it("deduplicates same item in different phases", () => {
    useRecommendationStore.getState().togglePurchased("laning-48");
    useRecommendationStore.getState().togglePurchased("core-48");
    const ids = useRecommendationStore.getState().getPurchasedItemIds();
    expect(ids).toEqual([48]);
  });

  it("returns empty array when no purchases", () => {
    const ids = useRecommendationStore.getState().getPurchasedItemIds();
    expect(ids).toEqual([]);
  });

  it("handles multiple distinct items", () => {
    useRecommendationStore.getState().togglePurchased("laning-48");
    useRecommendationStore.getState().togglePurchased("core-1");
    useRecommendationStore.getState().togglePurchased("starting-36");
    const ids = useRecommendationStore.getState().getPurchasedItemIds();
    expect(ids).toHaveLength(3);
    expect(ids).toContain(48);
    expect(ids).toContain(1);
    expect(ids).toContain(36);
  });
});

describe("clearResults vs clear", () => {
  it("clearResults clears data, error, and selectedItemId but keeps purchasedItems", () => {
    useRecommendationStore.setState({
      data: mockResponse,
      error: "some error",
      selectedItemId: "laning-48",
    });
    useRecommendationStore.getState().togglePurchased("laning-48");
    useRecommendationStore.getState().clearResults();

    const state = useRecommendationStore.getState();
    expect(state.data).toBeNull();
    expect(state.error).toBeNull();
    expect(state.selectedItemId).toBeNull();
    expect(state.purchasedItems.has("laning-48")).toBe(true);
  });

  it("clear resets everything including purchasedItems", () => {
    useRecommendationStore.setState({
      data: mockResponse,
      isLoading: true,
      error: "some error",
      selectedItemId: "laning-48",
    });
    useRecommendationStore.getState().togglePurchased("laning-48");
    useRecommendationStore.getState().clear();

    const state = useRecommendationStore.getState();
    expect(state.data).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.selectedItemId).toBeNull();
    expect(state.purchasedItems.size).toBe(0);
  });
});
