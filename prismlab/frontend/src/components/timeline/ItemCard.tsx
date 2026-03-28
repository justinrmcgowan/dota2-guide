import type { ItemRecommendation, ItemTimingData } from "../../types/recommendation";
import { itemImageUrl } from "../../utils/imageUrls";
import TimingBar from "./TimingBar";

interface ItemCardProps {
  item: ItemRecommendation;
  phaseKey: string;
  isSelected: boolean;
  onSelect: () => void;
  isPurchased: boolean;
  isDismissed: boolean;
  onTogglePurchased: () => void;
  onDismiss: () => void;
  timingData?: ItemTimingData | null;
  currentGameClock?: number | null;
  currentGold?: number | null;
}

const PRIORITY_BORDER: Record<ItemRecommendation["priority"], string> = {
  core: "border-l-secondary-fixed",
  situational: "border-l-outline-variant",
  luxury: "border-l-secondary-fixed",
};

function formatItemName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ItemCard({
  item,
  phaseKey: _phaseKey,
  isSelected,
  onSelect,
  isPurchased,
  isDismissed,
  onTogglePurchased,
  onDismiss,
  timingData = null,
  currentGameClock = null,
  currentGold = null,
}: ItemCardProps) {
  const borderClass = PRIORITY_BORDER[item.priority];
  const imgSrc = itemImageUrl(item.item_name);

  if (isDismissed) return null;

  const handleClick = () => {
    onTogglePurchased();
    onSelect();
  };

  const handleDismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDismiss();
  };

  return (
    <button
      onClick={handleClick}
      title={formatItemName(item.item_name)}
      className={[
        "group relative flex flex-col items-center gap-1 p-2 border-l-2 cursor-pointer transition-all",
        borderClass,
        isSelected
          ? "ring-1 ring-secondary-fixed bg-surface-container-high/50"
          : "bg-transparent hover:bg-surface-container-high/30",
        timingData?.is_urgent && !isPurchased ? "timing-urgent" : "",
      ].join(" ")}
    >
      {/* Dismiss button — visible on hover */}
      <span
        onClick={handleDismiss}
        className="absolute -top-1 -left-1 w-4 h-4 bg-surface-container-high rounded-full items-center justify-center cursor-pointer hover:bg-dire/80 hidden group-hover:flex z-10"
        title="Dismiss this item"
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" className="text-on-surface-variant">
          <path d="M2 2L8 8M8 2L2 8" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
        </svg>
      </span>

      <div className="relative">
        <img
          src={imgSrc}
          alt={formatItemName(item.item_name)}
          className={[
            "w-12 h-12 object-contain rounded",
            isPurchased ? "opacity-60" : "",
          ].join(" ")}
          loading="lazy"
        />
        {isPurchased && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-radiant rounded-full flex items-center justify-center">
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              className="text-on-surface"
            >
              <path
                d="M3 6L5 8L9 4"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        )}
      </div>
      {item.gold_cost != null ? (
        <span className="text-secondary text-xs text-center">
          {item.gold_cost}
        </span>
      ) : (
        <span className="text-secondary text-xs truncate max-w-[56px] text-center">
          {formatItemName(item.item_name)}
        </span>
      )}
      {timingData && !isPurchased && (
        <TimingBar
          buckets={timingData.buckets}
          confidence={timingData.confidence}
          isUrgent={timingData.is_urgent}
          isPurchased={isPurchased}
          currentGameClock={currentGameClock ?? null}
          currentGold={currentGold ?? null}
          itemCost={item.gold_cost ?? null}
          goodRange={timingData.good_range}
          ontrackRange={timingData.ontrack_range}
          lateRange={timingData.late_range}
          goodWinRate={timingData.good_win_rate}
          ontrackWinRate={timingData.ontrack_win_rate}
          lateWinRate={timingData.late_win_rate}
          totalGames={timingData.total_games}
        />
      )}
    </button>
  );
}

export default ItemCard;
