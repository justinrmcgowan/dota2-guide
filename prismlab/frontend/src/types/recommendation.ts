/** TypeScript interfaces matching backend Pydantic schemas in engine/schemas.py */

export interface ItemRecommendation {
  item_id: number;
  item_name: string;
  reasoning: string;
  priority: "core" | "situational" | "luxury";
  conditions: string | null;
  gold_cost: number | null;
}

export interface RecommendPhase {
  phase: "starting" | "laning" | "core" | "late_game" | "situational";
  items: ItemRecommendation[];
  timing: string | null;
  gold_budget: number | null;
}

export interface RecommendResponse {
  phases: RecommendPhase[];
  overall_strategy: string | null;
  fallback: boolean;
  model: string | null;
  latency_ms: number | null;
}

export interface RecommendRequest {
  hero_id: number;
  role: number;
  playstyle: string;
  side: "radiant" | "dire";
  lane: "safe" | "off" | "mid";
  lane_opponents: number[];
  allies: number[];
}
