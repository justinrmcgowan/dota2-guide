import type { Hero } from "../../types/hero";
import { heroIconUrl, heroSlugFromInternal } from "../../utils/imageUrls";
import { useState } from "react";

interface HeroSlotProps {
  hero: Hero | null;
  onClickEmpty: () => void;
  onClear: () => void;
  borderColor: string;
}

function HeroSlot({ hero, onClickEmpty, onClear, borderColor }: HeroSlotProps) {
  const [hovered, setHovered] = useState(false);

  if (!hero) {
    return (
      <button
        onClick={onClickEmpty}
        className="w-8 h-8 rounded-full border-2 border-dashed border-gray-500 flex items-center justify-center text-gray-500 hover:border-gray-300 hover:text-gray-300 transition-colors"
        aria-label="Add hero"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-3.5 h-3.5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    );
  }

  const slug = heroSlugFromInternal(hero.internal_name);
  const iconUrl = heroIconUrl(slug);

  return (
    <div
      className="relative w-8 h-8"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <img
        src={iconUrl}
        alt={hero.localized_name}
        title={hero.localized_name}
        className={`w-8 h-8 rounded-full object-cover border-2 ${borderColor}`}
      />
      {hovered && (
        <button
          onClick={onClear}
          className="absolute inset-0 w-8 h-8 rounded-full bg-black/70 flex items-center justify-center text-gray-200 hover:text-white transition-colors"
          aria-label={`Remove ${hero.localized_name}`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-3.5 h-3.5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

export default HeroSlot;
