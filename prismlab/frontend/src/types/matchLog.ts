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

/* ---------- Match History GET response types ---------- */

export interface MatchHistoryItem {
  id: number;
  match_id: string;
  hero_id: number;
  hero_name: string;
  role: number;
  playstyle: string | null;
  side: string | null;
  lane: string | null;
  win: boolean;
  duration_seconds: number | null;
  kills: number;
  deaths: number;
  assists: number;
  gpm: number;
  xpm: number;
  net_worth: number;
  engine_mode: string | null;
  was_fallback: boolean;
  overall_strategy: string | null;
  follow_rate: number | null;
  played_at: string;
  items: MatchItemPayload[];
  recommendations: MatchRecommendationPayload[];
}

export interface MatchHistoryResponse {
  matches: MatchHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface FlaggedItem {
  item_name: string;
  times_recommended: number;
  times_purchased: number;
  purchase_rate: number;
}

export interface MatchStatsResponse {
  total_games: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_follow_rate: number | null;
  avg_follow_rate_wins: number | null;
  avg_follow_rate_losses: number | null;
  // Accuracy metrics
  follow_win_rate: number | null;
  deviate_win_rate: number | null;
  follow_game_count: number;
  deviate_game_count: number;
  flagged_items: FlaggedItem[];
}
