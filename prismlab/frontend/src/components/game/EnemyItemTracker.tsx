import { useGameStore } from "../../stores/gameStore";
import { ENEMY_COUNTER_ITEMS } from "../../utils/constants";
import { itemImageUrl } from "../../utils/imageUrls";

function EnemyItemTracker() {
  const enemyItemsSpotted = useGameStore((s) => s.enemyItemsSpotted);
  const toggleEnemyItem = useGameStore((s) => s.toggleEnemyItem);

  return (
    <div className="grid grid-cols-5 gap-2">
      {ENEMY_COUNTER_ITEMS.map((item) => {
        const isSpotted = enemyItemsSpotted.includes(item.name);
        return (
          <button
            key={item.name}
            title={item.label}
            onClick={() => toggleEnemyItem(item.name)}
            className={`flex flex-col items-center gap-0.5 p-1 transition-all ${
              isSpotted
                ? "ring-2 ring-dire opacity-100"
                : "opacity-50 grayscale hover:opacity-75 hover:grayscale-0"
            }`}
          >
            <img
              src={itemImageUrl(item.name)}
              alt={item.label}
              width={32}
              height={32}
              className=""
            />
            <span className="text-[8px] text-on-surface-variant leading-tight text-center truncate w-full">
              {item.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default EnemyItemTracker;
