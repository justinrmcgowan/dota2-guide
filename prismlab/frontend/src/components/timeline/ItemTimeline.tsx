import { useMemo } from "react";
import type { RecommendResponse, ItemTimingData, BuildPathResponse } from "../../types/recommendation";
import PhaseCard from "./PhaseCard";
import NeutralItemSection from "./NeutralItemSection";
import WinConditionBadge from "./WinConditionBadge";
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
  const gold = useGsiStore((s) => s.liveState?.gold ?? null);
  const isGsiConnected = gsiStatus === "connected";
  const currentTier = isGsiConnected && gameClock != null
    ? getCurrentTier(gameClock)
    : null;

  const timingDataMap = useMemo(() => {
    const map = new Map<string, ItemTimingData>();
    if (data.timing_data) {
      for (const td of data.timing_data) {
        map.set(td.item_name, td);
      }
    }
    return map;
  }, [data.timing_data]);

  const buildPathMap = useMemo(() => {
    const map = new Map<string, BuildPathResponse>();
    if (data.build_paths) {
      for (const bp of data.build_paths) {
        map.set(bp.item_name, bp);
      }
    }
    return map;
  }, [data.build_paths]);

  return (
    <div className="flex flex-col gap-4">
      {/* Overall strategy summary */}
      {data.overall_strategy && (
        <div className="mb-2">
          <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
            Strategy
          </span>
          {data.win_condition && (
            <WinConditionBadge winCondition={data.win_condition} winProbability={data.win_probability} />
          )}
          <p className="text-on-surface-variant text-sm italic mt-1">
            {data.overall_strategy}
          </p>
        </div>
      )}

      {/* Win condition badge when overall_strategy is absent but win_condition is present (fallback mode) */}
      {!data.overall_strategy && data.win_condition && (
        <div className="mb-2">
          <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
            Strategy
          </span>
          <WinConditionBadge winCondition={data.win_condition} winProbability={data.win_probability} />
        </div>
      )}

      {/* Phase cards */}
      {data.phases.map((phase) => (
        <PhaseCard
          key={phase.phase}
          phase={phase}
          selectedItemId={selectedItemId}
          onSelectItem={onSelectItem}
          timingDataMap={timingDataMap}
          currentGameClock={isGsiConnected ? gameClock : null}
          currentGold={isGsiConnected ? gold : null}
          buildPathMap={buildPathMap}
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
