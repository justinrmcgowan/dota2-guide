import { useGameStore } from "../../stores/gameStore";
import { heroIconUrl, heroSlugFromInternal } from "../../utils/imageUrls";
import type { Hero } from "../../types/hero";

function LaneOpponentPicker() {
  const opponents = useGameStore((s) => s.opponents);
  const laneOpponents = useGameStore((s) => s.laneOpponents);
  const toggleLaneOpponent = useGameStore((s) => s.toggleLaneOpponent);

  const pickedOpponents = opponents.filter(
    (o): o is Hero => o !== null
  );

  if (pickedOpponents.length === 0) {
    return (
      <p className="text-xs text-on-surface-variant italic">Pick opponents first</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {pickedOpponents.map((hero) => {
        const isSelected = laneOpponents.some((h) => h.id === hero.id);
        const slug = heroSlugFromInternal(hero.internal_name);
        const iconUrl = heroIconUrl(slug);

        return (
          <button
            key={hero.id}
            onClick={() => toggleLaneOpponent(hero)}
            className={`flex items-center gap-1 px-2 py-1 border text-xs transition-colors ${
              isSelected
                ? "bg-primary-container/20 text-primary border-primary/40"
                : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
            }`}
          >
            <img
              src={iconUrl}
              alt={hero.localized_name}
              className="w-5 h-5 rounded-full object-cover"
            />
            <span>{hero.localized_name}</span>
          </button>
        );
      })}
    </div>
  );
}

export default LaneOpponentPicker;
