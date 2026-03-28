import { useGameStore } from "../../stores/gameStore";
import { useRecommendation } from "../../hooks/useRecommendation";
import { useRecommendationStore } from "../../stores/recommendationStore";
import { useRefreshStore } from "../../stores/refreshStore";

function GetBuildButton() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const role = useGameStore((s) => s.role);
  const { recommend, isLoading } = useRecommendation();
  const hasData = useRecommendationStore((s) => s.data !== null);
  const secondsRemaining = useRefreshStore((s) => s.secondsRemaining);
  const queuedEvent = useRefreshStore((s) => s.queuedEvent);

  const isReady = selectedHero !== null && role !== null;
  const isDisabled = !isReady || isLoading;

  const label = isLoading
    ? hasData ? "Re-Evaluating..." : "Analyzing..."
    : hasData ? "Re-Evaluate" : "Get Item Build";

  return (
    <div>
      <button
        disabled={isDisabled}
        onClick={() => {
          if (isReady && !isLoading) {
            recommend();
          }
        }}
        className={`w-full py-3 text-sm font-semibold transition-all ${
          isDisabled
            ? "bg-surface-container-high text-on-surface-variant/40 cursor-not-allowed"
            : "bg-primary-container text-on-surface font-display cursor-pointer hover:outline hover:outline-1 hover:outline-[#AA8986] shadow-glow-active"
        } ${isLoading ? "animate-pulse opacity-80" : ""}`}
      >
        {label}
      </button>
      {hasData && secondsRemaining > 0 && queuedEvent && (
        <p className="text-xs text-on-surface-variant/50 text-center mt-1">
          auto in {Math.floor(secondsRemaining / 60)}:
          {String(secondsRemaining % 60).padStart(2, "0")}
        </p>
      )}
    </div>
  );
}

export default GetBuildButton;
