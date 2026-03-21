import type { ItemRecommendation } from "../../types/recommendation";
import { itemImageUrl } from "../../utils/imageUrls";

interface ItemCardProps {
  item: ItemRecommendation;
  phaseKey: string;
  isSelected: boolean;
  onSelect: () => void;
}

const PRIORITY_BORDER: Record<ItemRecommendation["priority"], string> = {
  core: "border-l-cyan-accent",
  situational: "border-l-amber-400",
  luxury: "border-l-purple-400",
};

function formatItemName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ItemCard({ item, phaseKey, isSelected, onSelect }: ItemCardProps) {
  const borderClass = PRIORITY_BORDER[item.priority];
  const imgSrc = itemImageUrl(item.item_name);

  return (
    <button
      onClick={onSelect}
      title={formatItemName(item.item_name)}
      className={[
        "flex flex-col items-center gap-1 p-2 rounded-md border-l-2 cursor-pointer transition-all",
        borderClass,
        isSelected
          ? "ring-1 ring-cyan-accent bg-bg-elevated/50"
          : "bg-transparent hover:bg-bg-elevated/30",
      ].join(" ")}
    >
      <img
        src={imgSrc}
        alt={formatItemName(item.item_name)}
        className="w-12 h-12 object-contain rounded"
        loading="lazy"
      />
      <span className="text-amber-400 text-xs truncate max-w-[56px] text-center">
        {formatItemName(item.item_name)}
      </span>
    </button>
  );
}

export default ItemCard;
