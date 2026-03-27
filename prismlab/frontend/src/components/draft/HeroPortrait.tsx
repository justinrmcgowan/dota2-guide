import type { Hero } from "../../types/hero";
import { heroImageUrl, heroSlugFromInternal } from "../../utils/imageUrls";
import { ATTR_BG_COLORS } from "../../utils/constants";

interface HeroPortraitProps {
  hero: Hero;
  size?: "sm" | "lg";
  onClick?: () => void;
  selected?: boolean;
  disabled?: boolean;
}

function HeroPortrait({
  hero,
  size = "sm",
  onClick,
  selected = false,
  disabled = false,
}: HeroPortraitProps) {
  const slug = heroSlugFromInternal(hero.internal_name);
  const imgUrl = heroImageUrl(slug);
  const attrDotClass = ATTR_BG_COLORS[hero.primary_attr] ?? "bg-gray-400";

  const imgSize = size === "lg" ? "w-16 h-10" : "w-10 h-6";
  const textSize = size === "lg" ? "text-base font-semibold" : "text-sm";
  const dotSize = size === "lg" ? "w-2.5 h-2.5" : "w-2 h-2";

  const containerClasses = [
    "flex items-center gap-2 px-2 py-1.5 transition-colors",
    disabled
      ? "opacity-40 cursor-not-allowed"
      : onClick
        ? "cursor-pointer hover:bg-surface-container-high"
        : "",
    selected ? "ring-1 ring-secondary-fixed" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={containerClasses}
      onClick={disabled ? undefined : onClick}
      role={onClick && !disabled ? "button" : undefined}
      tabIndex={onClick && !disabled ? 0 : undefined}
      onKeyDown={
        onClick && !disabled
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      <img
        src={imgUrl}
        alt={hero.localized_name}
        className={`${imgSize} object-cover rounded`}
        loading="lazy"
      />
      <span className={`${textSize} text-on-surface`}>{hero.localized_name}</span>
      <span
        className={`${dotSize} rounded-full ${attrDotClass} shrink-0`}
        title={hero.primary_attr}
      />
    </div>
  );
}

export default HeroPortrait;
