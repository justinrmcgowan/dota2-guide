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
            className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
              isActive
                ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
                : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
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
