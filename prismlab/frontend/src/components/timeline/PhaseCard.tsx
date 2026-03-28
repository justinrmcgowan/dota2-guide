import type { RecommendPhase, ItemTimingData, BuildPathResponse } from "../../types/recommendation";
import { useRecommendationStore } from "../../stores/recommendationStore";
import ItemCard from "./ItemCard";
import DecisionTreeCard from "./DecisionTreeCard";
import BuildPathSteps from "./BuildPathSteps";

interface PhaseCardProps {
  phase: RecommendPhase;
  selectedItemId: string | null;
  onSelectItem: (key: string | null) => void;
  timingDataMap?: Map<string, ItemTimingData>;
  currentGameClock?: number | null;
  currentGold?: number | null;
  buildPathMap?: Map<string, BuildPathResponse>;
}

const PHASE_COLORS: Record<string, string> = {
  starting: "text-on-surface-variant",
  laning: "text-primary",
  core: "text-secondary",
  late_game: "text-tertiary",
  situational: "text-secondary",
};

const PHASE_LABELS: Record<string, string> = {
  starting: "STARTING",
  laning: "LANING",
  core: "CORE",
  late_game: "LATE GAME",
  situational: "SITUATIONAL",
};

function PhaseCard({
  phase,
  selectedItemId,
  onSelectItem,
  timingDataMap,
  currentGameClock = null,
  currentGold = null,
  buildPathMap = new Map(),
}: PhaseCardProps) {
  const purchasedItems = useRecommendationStore((s) => s.purchasedItems);
  const togglePurchased = useRecommendationStore((s) => s.togglePurchased);
  const dismissedItems = useRecommendationStore((s) => s.dismissedItems);
  const dismissItem = useRecommendationStore((s) => s.dismissItem);

  const colorClass = PHASE_COLORS[phase.phase] ?? "text-gray-400";
  const label = PHASE_LABELS[phase.phase] ?? phase.phase.toUpperCase();

  const coreItems = phase.items.filter((i) => i.conditions === null);
  const situationalItems = phase.items.filter((i) => i.conditions !== null);

  // Find the selected item in this phase to show reasoning
  const selectedItem = phase.items.find((item) => {
    const key = `${phase.phase}-${item.item_id}`;
    return key === selectedItemId;
  });

  return (
    <div className="bg-surface-container-low p-[1.75rem]">
      {/* Phase header */}
      <div className="flex items-center gap-3 mb-3">
        <h3 className={`text-sm font-bold tracking-wider font-display ${colorClass}`}>
          {label}
        </h3>
        {phase.timing && (
          <span className="text-xs text-on-surface-variant">{phase.timing}</span>
        )}
        {phase.gold_budget !== null && (
          <span className="text-xs text-on-surface-variant">
            ~{phase.gold_budget.toLocaleString()}g
          </span>
        )}
      </div>

      {/* Core / luxury items row */}
      {coreItems.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {coreItems.map((item) => {
            const key = `${phase.phase}-${item.item_id}`;
            return (
              <ItemCard
                key={key}
                item={item}
                phaseKey={key}
                isSelected={selectedItemId === key}
                onSelect={() => onSelectItem(key)}
                isPurchased={purchasedItems.has(key)}
                isDismissed={dismissedItems.has(key)}
                onTogglePurchased={() => togglePurchased(key)}
                onDismiss={() => dismissItem(key)}
                timingData={timingDataMap?.get(item.item_name) ?? null}
                currentGameClock={currentGameClock}
                currentGold={currentGold}
              />
            );
          })}
        </div>
      )}

      {/* Situational decision tree */}
      {situationalItems.length > 0 && (
        <div className="mt-3">
          <DecisionTreeCard items={situationalItems} />
        </div>
      )}

      {/* Expandable reasoning panel */}
      {selectedItem && (
        <div className="bg-surface-container-high/50 p-[1.75rem] mt-[1.75rem] border-l-2 border-secondary-fixed">
          <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
            {selectedItem.item_name.replace(/_/g, " ")}
          </span>
          <p className="text-on-surface-variant text-sm leading-relaxed mt-1">
            {selectedItem.reasoning}
          </p>
          {/* Component build path (PATH-01, PATH-02, PATH-03) */}
          {(() => {
            const buildPath = buildPathMap.get(selectedItem.item_name);
            return buildPath && buildPath.steps.length > 0 ? (
              <BuildPathSteps buildPath={buildPath} currentGold={currentGold} />
            ) : null;
          })()}
        </div>
      )}
    </div>
  );
}

export default PhaseCard;
