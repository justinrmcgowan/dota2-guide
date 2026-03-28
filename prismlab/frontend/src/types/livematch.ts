export interface LiveMatchPlayer {
  account_id: number;
  hero_id: number;
  is_radiant: boolean;
  player_slot: number;
  position: number | null; // 1-5 from Stratz, null from OpenDota
}

export interface LiveMatchResponse {
  match_id: number;
  game_state: string;
  game_time: number;
  players: LiveMatchPlayer[];
  source: string; // "stratz" | "opendota"
  radiant_score: number;
  dire_score: number;
}
