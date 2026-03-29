export interface Hero {
  id: number;
  name: string;
  localized_name: string;
  internal_name: string;
  primary_attr: "str" | "agi" | "int" | "all";
  attack_type: "Melee" | "Ranged";
  roles: string[];
  base_health: number;
  base_mana: number;
  base_armor: number;
  base_attack_min: number;
  base_attack_max: number;
  base_str: number;
  base_agi: number;
  base_int: number;
  str_gain: number;
  agi_gain: number;
  int_gain: number;
  attack_range: number;
  move_speed: number;
  img_url: string;
  icon_url: string;
}

export interface SuggestHeroRequest {
  role: number;
  ally_ids: number[];
  enemy_ids: number[];
  excluded_hero_ids: number[];
  top_n?: number;       // default 10 on backend
  bracket?: number;     // default 2 on backend
}

export interface HeroSuggestion {
  hero_id: number;
  hero_name: string;
  internal_name: string;
  icon_url: string | null;
  score: number;
  synergy_score: number;
  counter_score: number;
}

export interface SuggestHeroResponse {
  suggestions: HeroSuggestion[];
  matrices_available: boolean;
}
