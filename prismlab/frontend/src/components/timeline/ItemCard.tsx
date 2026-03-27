import type { ItemRecommendation } from "../../types/recommendation";
import { itemImageUrl } from "../../utils/imageUrls";

interface ItemCardProps {
  item: ItemRecommendation;
  phaseKey: string;
  isSelected: boolean;
  onSelect: () => void;
  isPurchased: boolean;
  onTogglePurchased: () => void;
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
  onTogglePurchased,
}: ItemCardProps) {
  const borderClass = PRIORITY_BORDER[item.priority];
  const imgSrc = itemImageUrl(item.item_name);

  const handleClick = () => {
    onTogglePurchased();
    onSelect();
  };

  return (
    <button
      onClick={handleClick}
      title={formatItemName(item.item_name)}
      className={[
        "flex flex-col items-center gap-1 p-2 border-l-2 cursor-pointer transition-all",
        borderClass,
        isSelected
          ? "ring-1 ring-secondary-fixed bg-surface-container-high/50"
          : "bg-transparent hover:bg-surface-container-high/30",
      ].join(" ")}
    >
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
    </button>
  );
}

export default ItemCard;
