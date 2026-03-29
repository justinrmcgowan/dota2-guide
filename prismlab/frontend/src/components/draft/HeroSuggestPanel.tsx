import { useState, useEffect, useMemo } from "react";
import { api } from "../../api/client";
import { useHeroes } from "../../hooks/useHeroes";
import HeroPortrait from "./HeroPortrait";
import type { Hero, SuggestHeroResponse } from "../../types/hero";

interface HeroSuggestPanelProps {
  role: number;
  allyIds: number[];
  enemyIds: number[];
  excludedHeroIds: Set<number>;
  onSelect: (hero: Hero) => void;
}

function HeroSuggestPanel({
  role,
  allyIds,
  enemyIds,
  excludedHeroIds,
  onSelect,
}: HeroSuggestPanelProps) {
  const [result, setResult] = useState<SuggestHeroResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { heroes } = useHeroes();
  const heroMap = useMemo(() => new Map(heroes.map((h) => [h.id, h])), [heroes]);

  // Stable serialized deps to avoid ref-equality churn on arrays/sets
  const allyKey = allyIds.join(",");
  const enemyKey = enemyIds.join(",");
  const excludedKey = [...excludedHeroIds].sort().join(",");

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .suggestHero({
        role,
        ally_ids: allyIds,
        enemy_ids: enemyIds,
        excluded_hero_ids: [...excludedHeroIds],
        top_n: 10,
        bracket: 2,
      })
      .then(setResult)
      .catch((e: Error) => setError(e.message ?? "Failed to load suggestions"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, allyKey, enemyKey, excludedKey]);

  if (loading) {
    return (
      <div className="py-3 px-3 text-xs text-on-surface-variant">
        Loading suggestions...
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-3 px-3 text-xs text-dire">
        Error: {error}
      </div>
    );
  }

  if (!result) return null;

  const { suggestions, matrices_available } = result;

  if (suggestions.length === 0) {
    return (
      <div className="py-3 px-3 text-xs text-on-surface-variant">
        No heroes found for this role.
      </div>
    );
  }

  return (
    <div className="bg-surface-container-low border border-outline-variant/15">
      {!matrices_available && (
        <div className="px-3 pt-2 pb-1 text-xs text-on-surface-variant">
          Training data pending — showing all viable picks
        </div>
      )}
      <div className="max-h-80 overflow-y-auto">
        {suggestions.map((suggestion) => {
          const hero = heroMap.get(suggestion.hero_id);

          // Score bar width: (score + 0.5) * 100, clamped to [5, 100]
          const barWidth = matrices_available
            ? Math.min(100, Math.max(5, (suggestion.score + 0.5) * 100)).toFixed(0)
            : null;

          return (
            <div
              key={suggestion.hero_id}
              className="group"
            >
              {hero ? (
                <div className="relative">
                  <HeroPortrait
                    hero={hero}
                    size="sm"
                    onClick={() => onSelect(hero)}
                  />
                  {barWidth !== null && (
                    <div
                      className="h-0.5 bg-primary/40 transition-all"
                      style={{ width: `${barWidth}%` }}
                    />
                  )}
                </div>
              ) : (
                // Fallback when hero not yet in cache: render text row
                <button
                  className="w-full text-left px-3 py-1.5 text-sm text-on-surface hover:bg-surface-container-high transition-colors"
                  onClick={() => {
                    // Build a minimal Hero-compatible object from suggestion
                    // This path is rarely hit — heroes cache loads before panel opens
                    const fallbackHero = {
                      id: suggestion.hero_id,
                      name: suggestion.internal_name,
                      localized_name: suggestion.hero_name,
                      internal_name: suggestion.internal_name,
                      primary_attr: "str" as const,
                      attack_type: "Melee" as const,
                      roles: [],
                      base_health: 0,
                      base_mana: 0,
                      base_armor: 0,
                      base_attack_min: 0,
                      base_attack_max: 0,
                      base_str: 0,
                      base_agi: 0,
                      base_int: 0,
                      str_gain: 0,
                      agi_gain: 0,
                      int_gain: 0,
                      attack_range: 0,
                      move_speed: 0,
                      img_url: suggestion.icon_url ?? "",
                      icon_url: suggestion.icon_url ?? "",
                    };
                    onSelect(fallbackHero);
                  }}
                >
                  {suggestion.hero_name}
                  {barWidth !== null && (
                    <div
                      className="h-0.5 bg-primary/40 mt-0.5 transition-all"
                      style={{ width: `${barWidth}%` }}
                    />
                  )}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default HeroSuggestPanel;
