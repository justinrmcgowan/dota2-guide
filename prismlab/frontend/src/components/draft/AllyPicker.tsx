import { useState } from "react";
import { useGameStore } from "../../stores/gameStore";
import HeroSlot from "./HeroSlot";
import HeroPicker from "./HeroPicker";
import type { Hero } from "../../types/hero";

interface AllyPickerProps {
  excludedHeroIds: Set<number>;
}

function AllyPicker({ excludedHeroIds }: AllyPickerProps) {
  const allies = useGameStore((s) => s.allies);
  const setAlly = useGameStore((s) => s.setAlly);
  const clearAlly = useGameStore((s) => s.clearAlly);

  const [activeSlot, setActiveSlot] = useState<number | null>(null);

  function handleSelect(hero: Hero) {
    if (activeSlot !== null) {
      setAlly(activeSlot, hero);
      setActiveSlot(null);
    }
  }

  return (
    <div className="border-l-2 border-radiant pl-3">
      <div className="flex items-center gap-1.5">
        {allies.map((ally, i) => (
          <HeroSlot
            key={i}
            hero={ally}
            onClickEmpty={() => setActiveSlot(i)}
            onClear={() => clearAlly(i)}
            borderColor="border-radiant"
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
            placeholder="Add ally..."
          />
        </div>
      )}
    </div>
  );
}

export default AllyPicker;
