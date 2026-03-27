import type { ItemRecommendation } from "../../types/recommendation";
import { itemImageUrl } from "../../utils/imageUrls";

interface DecisionTreeCardProps {
  items: ItemRecommendation[];
}

function formatItemName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function DecisionTreeCard({ items }: DecisionTreeCardProps) {
  return (
    <div className="bg-surface-container-high/30 p-[1.75rem]">
      <h4 className="text-secondary text-xs font-semibold uppercase tracking-wide font-display mb-2">
        Situational Options
      </h4>

      <div className="flex flex-col gap-[1.75rem]">
        {items.map((item) => (
          <div
            key={item.item_id}
            className="flex items-center gap-2"
          >
            {/* Condition text */}
            <span className="text-on-surface-variant text-xs flex-1 min-w-0">
              {item.conditions}
            </span>

            {/* Arrow */}
            <svg
              className="w-4 h-4 text-outline-variant shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>

            {/* Item icon + name */}
            <div className="flex items-center gap-1.5 shrink-0">
              <img
                src={itemImageUrl(item.item_name)}
                alt={formatItemName(item.item_name)}
                className="w-8 h-8 object-contain rounded"
                loading="lazy"
              />
              <span className="text-on-surface text-xs">
                {formatItemName(item.item_name)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DecisionTreeCard;
