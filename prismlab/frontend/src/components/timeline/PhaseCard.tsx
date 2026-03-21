import type { RecommendPhase } from "../../types/recommendation";
import { useRecommendationStore } from "../../stores/recommendationStore";
import ItemCard from "./ItemCard";
import DecisionTreeCard from "./DecisionTreeCard";

interface PhaseCardProps {
  phase: RecommendPhase;
  selectedItemId: string | null;
  onSelectItem: (key: string | null) => void;
}

const PHASE_COLORS: Record<string, string> = {
  starting: "text-gray-400",
  laning: "text-cyan-accent",
  core: "text-amber-400",
  late_game: "text-purple-400",
  situational: "text-amber-400",
};

const PHASE_LABELS: Record<string, string> = {
  starting: "STARTING",
  laning: "LANING",
  core: "CORE",
  late_game: "LATE GAME",
  situational: "SITUATIONAL",
};

function PhaseCard({ phase, selectedItemId, onSelectItem }: PhaseCardProps) {
  const purchasedItems = useRecommendationStore((s) => s.purchasedItems);
  const togglePurchased = useRecommendationStore((s) => s.togglePurchased);

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
    <div className="bg-bg-secondary rounded-lg p-4 border border-bg-elevated">
      {/* Phase header */}
      <div className="flex items-center gap-3 mb-3">
        <h3 className={`text-sm font-bold tracking-wider ${colorClass}`}>
          {label}
        </h3>
        {phase.timing && (
          <span className="text-xs text-gray-500">{phase.timing}</span>
        )}
        {phase.gold_budget !== null && (
          <span className="text-xs text-gray-500">
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
                onTogglePurchased={() => togglePurchased(key)}
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
        <div className="bg-bg-elevated/50 rounded-lg p-4 mt-3 border-l-2 border-cyan-accent">
          <span className="text-cyan-accent text-xs font-semibold uppercase tracking-wide">
            {selectedItem.item_name.replace(/_/g, " ")}
          </span>
          <p className="text-gray-300 text-sm leading-relaxed mt-1">
            {selectedItem.reasoning}
          </p>
        </div>
      )}
    </div>
  );
}

export default PhaseCard;
