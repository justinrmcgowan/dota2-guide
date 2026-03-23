import type { RecommendResponse } from "../../types/recommendation";
import PhaseCard from "./PhaseCard";
import NeutralItemSection from "./NeutralItemSection";

interface ItemTimelineProps {
  data: RecommendResponse;
  selectedItemId: string | null;
  onSelectItem: (key: string | null) => void;
}

function ItemTimeline({ data, selectedItemId, onSelectItem }: ItemTimelineProps) {
  return (
    <div className="flex flex-col gap-4">
      {/* Overall strategy summary */}
      {data.overall_strategy && (
        <div className="mb-2">
          <span className="text-cyan-accent text-xs font-semibold uppercase tracking-wide">
            Strategy
          </span>
          <p className="text-gray-400 text-sm italic mt-1">
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
        <NeutralItemSection neutralItems={data.neutral_items} />
      )}
    </div>
  );
}

export default ItemTimeline;
