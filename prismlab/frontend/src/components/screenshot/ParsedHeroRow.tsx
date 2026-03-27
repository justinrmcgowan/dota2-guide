import { useState } from "react";
import type { ParsedHero } from "../../types/screenshot";
import { useScreenshotStore } from "../../stores/screenshotStore";
import {
  heroImageUrl,
  heroSlugFromInternal,
  itemImageUrl,
} from "../../utils/imageUrls";

interface ParsedHeroRowProps {
  hero: ParsedHero;
  heroIdx: number;
  onAddItem: (heroIdx: number) => void;
}

function ParsedHeroRow({ hero, heroIdx, onAddItem }: ParsedHeroRowProps) {
  const [hoveredItem, setHoveredItem] = useState<number | null>(null);

  const heroPortrait = hero.internal_name
    ? heroImageUrl(heroSlugFromInternal(hero.internal_name))
    : null;

  const kda =
    hero.kills !== null || hero.deaths !== null || hero.assists !== null
      ? `${hero.kills ?? "?"}/${hero.deaths ?? "?"}/${hero.assists ?? "?"}`
      : null;

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-surface-container-high">
      {/* Hero portrait — keep rounded per D-05 (functional: portrait) */}
      {heroPortrait ? (
        <img
          src={heroPortrait}
          alt={hero.hero_name}
          className="w-10 h-10 rounded object-cover shrink-0"
        />
      ) : (
        <div className="w-10 h-10 rounded bg-surface-container shrink-0" />
      )}

      {/* Hero info column */}
      <div className="min-w-0 shrink-0">
        <div className="text-sm font-medium text-on-surface truncate max-w-[100px]">
          {hero.hero_name}
        </div>
        {kda && <div className="text-xs text-on-surface-variant">{kda}</div>}
        {hero.level !== null && (
          <div className="text-xs text-on-surface-variant/70">Lv {hero.level}</div>
        )}
      </div>

      {/* Items row */}
      <div className="flex flex-wrap items-center gap-1.5 flex-1 min-w-0">
        {hero.items.map((item, itemIdx) => {
          const isLow = item.confidence === "low";
          const isMedium = item.confidence === "medium";

          return (
            <div
              key={`${item.internal_name}-${itemIdx}`}
              className="relative"
              onMouseEnter={() => setHoveredItem(itemIdx)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <img
                src={itemImageUrl(item.internal_name)}
                alt={item.display_name}
                title={`${item.display_name} (${item.confidence})`}
                className={`w-8 h-8 rounded object-cover ${
                  isLow
                    ? "ring-2 ring-orange-400"
                    : isMedium
                      ? "ring-1 ring-yellow-500/50"
                      : ""
                }`}
              />
              {/* Low confidence badge — keep rounded-full per D-05 (badge dot) */}
              {isLow && (
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-orange-400 text-black text-[8px] font-bold rounded-full flex items-center justify-center">
                  ?
                </span>
              )}
              {/* Remove button on hover */}
              {hoveredItem === itemIdx && (
                <button
                  onClick={() =>
                    useScreenshotStore
                      .getState()
                      .removeItem(heroIdx, itemIdx)
                  }
                  className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-dire text-on-surface text-[9px] font-bold rounded-full flex items-center justify-center hover:bg-dire/80 z-10"
                  title="Remove item"
                >
                  X
                </button>
              )}
            </div>
          );
        })}

        {/* Add item button */}
        {hero.items.length < 6 && (
          <button
            onClick={() => onAddItem(heroIdx)}
            className="w-8 h-8 border border-dashed border-outline-variant text-on-surface-variant hover:border-primary hover:text-primary flex items-center justify-center text-lg transition-colors"
            title="Add item"
          >
            +
          </button>
        )}
      </div>

      {/* Remove hero button */}
      <button
        onClick={() => useScreenshotStore.getState().removeHero(heroIdx)}
        className="shrink-0 p-1 text-on-surface-variant/50 hover:text-dire transition-colors"
        title="Remove hero"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 6h18" />
          <path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" />
          <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
        </svg>
      </button>
    </div>
  );
}

export default ParsedHeroRow;
