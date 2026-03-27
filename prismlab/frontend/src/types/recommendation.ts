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

export interface NeutralItemPick {
  item_name: string;
  reasoning: string;
  rank: number;
}

export interface NeutralTierRecommendation {
  tier: number;
  items: NeutralItemPick[];
}

export interface RecommendResponse {
  phases: RecommendPhase[];
  overall_strategy: string | null;
  fallback: boolean;
  fallback_reason: "timeout" | "parse_error" | "api_error" | "rate_limited" | null;
  model: string | null;
  latency_ms: number | null;
  neutral_items: NeutralTierRecommendation[];
}

export interface EnemyContext {
  hero_id: number;
  kills?: number | null;
  deaths?: number | null;
  assists?: number | null;
  level?: number | null;
}

export interface RecommendRequest {
  hero_id: number;
  role: number;
  playstyle: string;
  side: "radiant" | "dire";
  lane: "safe" | "off" | "mid";
  lane_opponents: number[];
  allies: number[];

  // Mid-game adaptation fields (all optional for backward compatibility)
  lane_result?: "won" | "even" | "lost" | null;
  damage_profile?: { physical: number; magical: number; pure: number } | null;
  enemy_items_spotted?: string[];
  purchased_items?: number[];
  enemy_context?: EnemyContext[];
}
