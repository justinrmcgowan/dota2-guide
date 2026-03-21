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
      <p className="text-xs text-gray-500 italic">Pick opponents first</p>
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
            className={`flex items-center gap-1 px-2 py-1 rounded-md border text-xs transition-colors ${
              isSelected
                ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
                : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
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
