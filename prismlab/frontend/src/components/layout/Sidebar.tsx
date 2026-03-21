import HeroPicker from "../draft/HeroPicker";
import { useGameStore } from "../../stores/gameStore";

function Sidebar() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const selectHero = useGameStore((s) => s.selectHero);
  const clearHero = useGameStore((s) => s.clearHero);

  return (
    <aside className="w-80 bg-bg-secondary border-r border-bg-elevated flex flex-col overflow-hidden shrink-0">
      <div className="p-4 flex-1 overflow-y-auto">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Your Hero
        </h2>
        <HeroPicker
          value={selectedHero}
          onSelect={selectHero}
          onClear={clearHero}
          excludedHeroIds={new Set()}
          placeholder="Search heroes..."
        />
        {/* Phase 2 Plan 02 components go here */}
      </div>
    </aside>
  );
}

export default Sidebar;
