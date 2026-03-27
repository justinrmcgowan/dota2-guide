import { useGameStore } from "../../stores/gameStore";
import { LANE_OPTIONS } from "../../utils/constants";

function LaneSelector() {
  const lane = useGameStore((s) => s.lane);
  const setLane = useGameStore((s) => s.setLane);

  return (
    <div role="radiogroup" aria-label="Lane" className="flex gap-1.5">
      {LANE_OPTIONS.map((opt) => {
        const isActive = lane === opt.value;
        return (
          <button
            key={opt.value}
            role="radio"
            aria-checked={isActive}
            onClick={() => setLane(opt.value)}
            className={`flex-1 py-1.5 text-xs font-medium border transition-colors ${
              isActive
                ? "bg-primary-container/20 text-primary border-primary/40"
                : "bg-surface-container-high text-on-surface-variant border-outline-variant/15 hover:text-on-surface"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

export default LaneSelector;
