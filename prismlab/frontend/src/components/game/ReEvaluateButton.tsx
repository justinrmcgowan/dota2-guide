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
        className={`w-full py-3 rounded-lg text-sm font-semibold transition-all ${
          isLoading
            ? "bg-bg-elevated text-gray-500 cursor-not-allowed animate-pulse opacity-80"
            : "bg-cyan-accent text-bg-primary cursor-pointer hover:brightness-110 shadow-[0_0_15px_rgba(0,212,255,0.3)]"
        }`}
      >
        {isLoading ? "Re-Evaluating..." : "Re-Evaluate"}
      </button>
      {secondsRemaining > 0 && queuedEvent && (
        <p className="text-xs text-gray-500 text-center mt-1">
          auto in {Math.floor(secondsRemaining / 60)}:
          {String(secondsRemaining % 60).padStart(2, "0")}
        </p>
      )}
    </div>
  );
}

export default ReEvaluateButton;
