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
      className={`w-full py-3 text-sm font-semibold transition-all ${
        isDisabled
          ? "bg-surface-container-high text-on-surface-variant/40 cursor-not-allowed"
          : "bg-primary-container text-on-surface font-display cursor-pointer hover:outline hover:outline-1 hover:outline-[#AA8986] shadow-glow-active"
      } ${isLoading ? "animate-pulse opacity-80" : ""}`}
    >
      {isLoading ? "Analyzing..." : "Get Item Build"}
    </button>
  );
}

export default GetBuildButton;
