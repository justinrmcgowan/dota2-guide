import { useGameStore } from "../../stores/gameStore";
import HeroPortrait from "../draft/HeroPortrait";

function MainPanel() {
  const selectedHero = useGameStore((state) => state.selectedHero);

  return (
    <main className="flex-1 bg-bg-primary overflow-y-auto p-6">
      {selectedHero ? (
        <div>
          <h2 className="text-lg font-semibold text-gray-200 mb-4">
            Selected: {selectedHero.localized_name}
          </h2>
          <HeroPortrait hero={selectedHero} size="lg" />
          <p className="text-gray-400 text-sm mt-4">
            Item recommendations will appear here once the recommendation engine
            is built in Phase 3.
          </p>
        </div>
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 text-sm">
            Select a hero from the sidebar to get started
          </p>
        </div>
      )}
    </main>
  );
}

export default MainPanel;
