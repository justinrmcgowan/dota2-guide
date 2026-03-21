import { useGameStore } from "../../stores/gameStore";

function GetBuildButton() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const role = useGameStore((s) => s.role);

  const isReady = selectedHero !== null && role !== null;

  return (
    <button
      disabled={!isReady}
      onClick={() => {
        if (isReady) {
          // Phase 4 will wire this to the recommendation API
          console.log("Get Item Build clicked");
        }
      }}
      className={`w-full py-3 rounded-lg text-sm font-semibold transition-all ${
        isReady
          ? "bg-cyan-accent text-bg-primary cursor-pointer hover:brightness-110 shadow-[0_0_15px_rgba(0,212,255,0.3)]"
          : "bg-bg-elevated text-gray-500 cursor-not-allowed"
      }`}
    >
      Get Item Build
    </button>
  );
}

export default GetBuildButton;
