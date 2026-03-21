import { useRecommendation } from "../../hooks/useRecommendation";

function ReEvaluateButton() {
  const { recommend, isLoading } = useRecommendation();

  return (
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
  );
}

export default ReEvaluateButton;
