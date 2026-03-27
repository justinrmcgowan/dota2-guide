import { useMemo } from "react";
import HeroPicker from "../draft/HeroPicker";
import AllyPicker from "../draft/AllyPicker";
import OpponentPicker from "../draft/OpponentPicker";
import RoleSelector from "../draft/RoleSelector";
import PlaystyleSelector from "../draft/PlaystyleSelector";
import SideSelector from "../draft/SideSelector";
import LaneSelector from "../draft/LaneSelector";
import LaneOpponentPicker from "../draft/LaneOpponentPicker";
import GetBuildButton from "../draft/GetBuildButton";
import GameStatePanel from "../game/GameStatePanel";
import LiveStatsBar from "../game/LiveStatsBar";
import { useGameStore } from "../../stores/gameStore";
import { useRecommendationStore } from "../../stores/recommendationStore";

function Sidebar() {
  const selectedHero = useGameStore((s) => s.selectedHero);
  const selectHero = useGameStore((s) => s.selectHero);
  const clearHero = useGameStore((s) => s.clearHero);
  const allies = useGameStore((s) => s.allies);
  const opponents = useGameStore((s) => s.opponents);
  const role = useGameStore((s) => s.role);

  const hasData = useRecommendationStore((s) => s.data !== null);

  const excludedIds = useMemo(() => {
    const ids = new Set<number>();
    if (selectedHero) ids.add(selectedHero.id);
    allies.forEach((a) => {
      if (a) ids.add(a.id);
    });
    opponents.forEach((o) => {
      if (o) ids.add(o.id);
    });
    return ids;
  }, [selectedHero, allies, opponents]);

  return (
    <aside className="w-80 bg-surface-container-lowest flex flex-col overflow-hidden shrink-0 border-r border-r-transparent" style={{ borderImage: 'linear-gradient(to bottom, var(--color-secondary-fixed-dim), transparent 80%) 1' }}>
      <div className="p-4 flex-1 overflow-y-auto">
        {/* Your Hero */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
          Your Hero
        </h2>
        <HeroPicker
          value={selectedHero}
          onSelect={selectHero}
          onClear={clearHero}
          excludedHeroIds={excludedIds}
          placeholder="Search heroes..."
        />

        {/* Allies */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Allies
        </h2>
        <AllyPicker excludedHeroIds={excludedIds} />

        {/* Opponents */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Opponents
        </h2>
        <OpponentPicker excludedHeroIds={excludedIds} />

        {/* Role */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Role
        </h2>
        <RoleSelector />

        {/* Playstyle -- animated reveal */}
        <div
          className={`transition-all duration-300 ease-out overflow-hidden ${
            role !== null ? "max-h-40 opacity-100 mt-5" : "max-h-0 opacity-0"
          }`}
        >
          <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
            Playstyle
          </h2>
          {role !== null && <PlaystyleSelector role={role} />}
        </div>

        {/* Side */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Side
        </h2>
        <SideSelector />

        {/* Lane */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Lane
        </h2>
        <LaneSelector />

        {/* Lane Opponents */}
        <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-2 mt-5">
          Lane Opponents
        </h2>
        <LaneOpponentPicker />

        {/* Live Stats -- visible when GSI is connected and in-game */}
        <LiveStatsBar />

        {/* Game State -- appears after first recommendation */}
        {hasData && <GameStatePanel />}
      </div>

      {/* CTA Button -- pinned at bottom */}
      <div className="p-4 bg-surface-container-low">
        <GetBuildButton />
      </div>
    </aside>
  );
}

export default Sidebar;
