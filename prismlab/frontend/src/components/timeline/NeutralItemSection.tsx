import type { NeutralTierRecommendation } from "../../types/recommendation";
import { getNextTierCountdown } from "../../utils/neutralTiers";

interface NeutralItemSectionProps {
  neutralItems: NeutralTierRecommendation[];
  currentTier?: number | null;
  gameClock?: number | null;
}

const TIER_TIMING: Record<number, string> = {
  1: "5 min",
  2: "15 min",
  3: "25 min",
  4: "35 min",
  5: "60 min",
};

const STEAM_CDN_ITEMS =
  "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items";

/** Convert display name to Steam CDN internal name (lowercase, spaces to underscores, apostrophes removed) */
function toInternalName(itemName: string): string {
  return itemName.toLowerCase().replace(/ /g, "_").replace(/'/g, "");
}

function formatDisplayName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

const RANK_COLORS: Record<number, string> = {
  1: "bg-secondary text-surface",
  2: "bg-surface-container-high text-on-surface",
  3: "bg-surface-container text-on-surface-variant",
};

function formatCountdown(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

function NeutralItemSection({ neutralItems, currentTier, gameClock }: NeutralItemSectionProps) {
  if (!neutralItems || neutralItems.length === 0) return null;

  const sorted = [...neutralItems].sort((a, b) => a.tier - b.tier);

  return (
    <div className="bg-surface-container-low p-[1.75rem]">
      {/* Section header */}
      <h3 className="text-secondary text-sm font-bold tracking-wider font-display mb-4">
        BEST NEUTRAL ITEMS
      </h3>

      {/* Tier rows */}
      <div className="flex flex-col gap-3">
        {sorted.map((tierRec) => {
          const timing = TIER_TIMING[tierRec.tier] ?? "";
          const sortedItems = [...tierRec.items].sort(
            (a, b) => a.rank - b.rank,
          );

          const isActive = currentTier != null && tierRec.tier === currentTier;
          const isPast = currentTier != null && tierRec.tier < currentTier;

          return (
            <div
              key={tierRec.tier}
              className={`bg-surface-container-high/50 p-3${isActive ? " ring-1 ring-secondary-fixed" : ""}${isPast ? " opacity-50" : ""}`}
            >
              {/* Tier sub-header */}
              <div className="text-on-surface-variant text-xs font-semibold mb-2">
                T{tierRec.tier}{timing && ` (${timing})`}
              </div>

              {/* Item picks */}
              <div className="flex flex-col gap-2">
                {sortedItems.map((pick) => {
                  const internalName = toInternalName(pick.item_name);
                  const imgSrc = `${STEAM_CDN_ITEMS}/${internalName}.png`;
                  const rankColor =
                    RANK_COLORS[pick.rank] ?? "bg-gray-700 text-gray-300";

                  return (
                    <div key={pick.item_name} className="flex items-start gap-2">
                      {/* Rank badge */}
                      <span
                        className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${rankColor}`}
                      >
                        {pick.rank}
                      </span>

                      {/* Item image */}
                      <img
                        src={imgSrc}
                        alt={formatDisplayName(pick.item_name)}
                        className="w-6 h-6 object-contain rounded shrink-0"
                        loading="lazy"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />

                      {/* Name and reasoning */}
                      <div className="min-w-0">
                        <span className="text-on-surface text-xs font-medium">
                          {formatDisplayName(pick.item_name)}
                        </span>
                        {pick.reasoning && (
                          <p className="text-on-surface-variant text-xs mt-0.5 leading-relaxed">
                            {pick.reasoning}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Next tier countdown */}
      {gameClock != null && (() => {
        const nextTier = getNextTierCountdown(gameClock);
        if (!nextTier) return null;
        return (
          <p className="text-on-surface-variant text-xs mt-2 text-center">
            Next: Tier {nextTier.tier} in {formatCountdown(nextTier.secondsRemaining)}
          </p>
        );
      })()}
    </div>
  );
}

export default NeutralItemSection;
