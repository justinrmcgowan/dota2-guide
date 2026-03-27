import type { RecommendResponse } from "../../types/recommendation";
import PhaseCard from "./PhaseCard";
import NeutralItemSection from "./NeutralItemSection";
import { useGsiStore } from "../../stores/gsiStore";
import { getCurrentTier } from "../../utils/neutralTiers";

interface ItemTimelineProps {
  data: RecommendResponse;
  selectedItemId: string | null;
  onSelectItem: (key: string | null) => void;
}

function ItemTimeline({ data, selectedItemId, onSelectItem }: ItemTimelineProps) {
  const gsiStatus = useGsiStore((s) => s.gsiStatus);
  const gameClock = useGsiStore((s) => s.liveState?.game_clock ?? null);
  const currentTier = gsiStatus === "connected" && gameClock != null
    ? getCurrentTier(gameClock)
    : null;

  return (
    <div className="flex flex-col gap-4">
      {/* Overall strategy summary */}
      {data.overall_strategy && (
        <div className="mb-2">
          <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
            Strategy
          </span>
          <p className="text-on-surface-variant text-sm italic mt-1">
            {data.overall_strategy}
          </p>
        </div>
      )}

      {/* Phase cards */}
      {data.phases.map((phase) => (
        <PhaseCard
          key={phase.phase}
          phase={phase}
          selectedItemId={selectedItemId}
          onSelectItem={onSelectItem}
        />
      ))}

      {/* Neutral items section below purchasable timeline */}
      {data.neutral_items && data.neutral_items.length > 0 && (
        <NeutralItemSection
          neutralItems={data.neutral_items}
          currentTier={currentTier}
          gameClock={gsiStatus === "connected" ? gameClock : null}
        />
      )}
    </div>
  );
}

export default ItemTimeline;
