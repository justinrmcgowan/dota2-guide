import { useState } from "react";
import { useGameStore } from "../../stores/gameStore";
import HeroSlot from "./HeroSlot";
import HeroPicker from "./HeroPicker";
import type { Hero } from "../../types/hero";

interface OpponentPickerProps {
  excludedHeroIds: Set<number>;
}

function OpponentPicker({ excludedHeroIds }: OpponentPickerProps) {
  const opponents = useGameStore((s) => s.opponents);
  const setOpponent = useGameStore((s) => s.setOpponent);
  const clearOpponent = useGameStore((s) => s.clearOpponent);

  const [activeSlot, setActiveSlot] = useState<number | null>(null);

  function handleSelect(hero: Hero) {
    if (activeSlot !== null) {
      setOpponent(activeSlot, hero);
      setActiveSlot(null);
    }
  }

  return (
    <div className="border-l-2 border-dire pl-3">
      <div className="flex items-center gap-1.5">
        {opponents.map((opponent, i) => (
          <HeroSlot
            key={i}
            hero={opponent}
            onClickEmpty={() => setActiveSlot(i)}
            onClear={() => clearOpponent(i)}
            borderColor="border-dire"
          />
        ))}
      </div>

      {activeSlot !== null && (
        <div className="mt-2">
          <HeroPicker
            value={null}
            onSelect={handleSelect}
            onClear={() => setActiveSlot(null)}
            excludedHeroIds={excludedHeroIds}
            compact
            placeholder="Add opponent..."
          />
        </div>
      )}
    </div>
  );
}

export default OpponentPicker;
