import { useGameStore } from "../../stores/gameStore";
import { useRefreshStore } from "../../stores/refreshStore";
import { LANE_RESULT_OPTIONS } from "../../utils/constants";

function LaneResultSelector() {
  const laneResult = useGameStore((s) => s.laneResult);
  const setLaneResult = useGameStore((s) => s.setLaneResult);
  const laneAutoDetected = useRefreshStore((s) => s.laneAutoDetected);

  return (
    <div>
      <div role="radiogroup" aria-label="Lane result" className="flex gap-2">
        {LANE_RESULT_OPTIONS.map((opt) => {
          const isActive = laneResult === opt.value;
          return (
            <button
              key={opt.value}
              role="radio"
              aria-checked={isActive}
              onClick={() => setLaneResult(opt.value)}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                isActive
                  ? `${opt.bg} ${opt.color} ${opt.border}`
                  : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
      {laneAutoDetected && laneResult && (
        <p className="text-[10px] text-gray-500 mt-1 italic">
          auto-detected from GPM
        </p>
      )}
    </div>
  );
}

export default LaneResultSelector;
