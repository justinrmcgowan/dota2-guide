import { useRecommendation } from "../../hooks/useRecommendation";
import { useRefreshStore } from "../../stores/refreshStore";

function ReEvaluateButton() {
  const { recommend, isLoading } = useRecommendation();
  const secondsRemaining = useRefreshStore((s) => s.secondsRemaining);
  const queuedEvent = useRefreshStore((s) => s.queuedEvent);

  return (
    <div>
      <button
        disabled={isLoading}
        onClick={() => {
          if (!isLoading) {
            recommend();
          }
        }}
        className={`w-full py-3 text-sm font-semibold transition-all ${
          isLoading
            ? "bg-surface-container-high text-on-surface-variant/40 cursor-not-allowed animate-pulse opacity-80"
            : "bg-primary-container text-on-surface font-display cursor-pointer hover:outline hover:outline-1 hover:outline-[#AA8986] shadow-glow-active"
        }`}
      >
        {isLoading ? "Re-Evaluating..." : "Re-Evaluate"}
      </button>
      {secondsRemaining > 0 && queuedEvent && (
        <p className="text-xs text-on-surface-variant/50 text-center mt-1">
          auto in {Math.floor(secondsRemaining / 60)}:
          {String(secondsRemaining % 60).padStart(2, "0")}
        </p>
      )}
    </div>
  );
}

export default ReEvaluateButton;
