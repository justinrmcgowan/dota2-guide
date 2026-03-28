/** TypeScript interfaces matching backend Pydantic models for match logging. */

export interface MatchItemPayload {
  slot_type: "inventory" | "backpack" | "neutral";
  item_name: string;
}

export interface MatchRecommendationPayload {
  phase: string;
  item_id: number;
  item_name: string;
  priority: string;
  was_purchased: boolean;
}

export interface MatchLogPayload {
  match_id: string;
  hero_id: number;
  hero_name: string;
  role: number;
  playstyle: string | null;
  side: string | null;
  lane: string | null;
  allies: number[];
  opponents: number[];
  lane_opponents: number[];
  win: boolean;
  duration_seconds: number | null;
  kills: number;
  deaths: number;
  assists: number;
  gpm: number;
  xpm: number;
  net_worth: number;
  last_hits: number;
  denies: number;
  engine_mode: string | null;
  was_fallback: boolean;
  overall_strategy: string | null;
  items: MatchItemPayload[];
  recommendations: MatchRecommendationPayload[];
}
