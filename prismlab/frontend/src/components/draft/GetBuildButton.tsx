import { useGameStore } from "../../stores/gameStore";
import { useRecommendation } from "../../hooks/useRecommendation";

function GetBuildButton() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const role = useGameStore((s) => s.role);
  const { recommend, isLoading } = useRecommendation();

  const isReady = selectedHero !== null && role !== null;
  const isDisabled = !isReady || isLoading;

  return (
    <button
      disabled={isDisabled}
      onClick={() => {
        if (isReady && !isLoading) {
          recommend();
        }
      }}
      className={`w-full py-3 rounded-lg text-sm font-semibold transition-all ${
        isDisabled
          ? "bg-bg-elevated text-gray-500 cursor-not-allowed"
          : "bg-cyan-accent text-bg-primary cursor-pointer hover:brightness-110 shadow-[0_0_15px_rgba(0,212,255,0.3)]"
      } ${isLoading ? "animate-pulse opacity-80" : ""}`}
    >
      {isLoading ? "Analyzing..." : "Get Item Build"}
    </button>
  );
}

export default GetBuildButton;
