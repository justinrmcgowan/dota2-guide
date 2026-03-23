import type { NeutralTierRecommendation } from "../../types/recommendation";

interface NeutralItemSectionProps {
  neutralItems: NeutralTierRecommendation[];
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
  1: "bg-cyan-accent text-bg-primary",
  2: "bg-gray-600 text-gray-200",
  3: "bg-gray-700 text-gray-300",
};

function NeutralItemSection({ neutralItems }: NeutralItemSectionProps) {
  if (!neutralItems || neutralItems.length === 0) return null;

  const sorted = [...neutralItems].sort((a, b) => a.tier - b.tier);

  return (
    <div className="bg-bg-secondary rounded-lg p-4 border border-bg-elevated">
      {/* Section header */}
      <h3 className="text-cyan-accent text-sm font-bold tracking-wider mb-4">
        BEST NEUTRAL ITEMS
      </h3>

      {/* Tier rows */}
      <div className="flex flex-col gap-3">
        {sorted.map((tierRec) => {
          const timing = TIER_TIMING[tierRec.tier] ?? "";
          const sortedItems = [...tierRec.items].sort(
            (a, b) => a.rank - b.rank,
          );

          return (
            <div
              key={tierRec.tier}
              className="bg-bg-elevated/50 rounded-lg p-3"
            >
              {/* Tier sub-header */}
              <div className="text-gray-400 text-xs font-semibold mb-2">
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
                        <span className="text-gray-300 text-xs font-medium">
                          {formatDisplayName(pick.item_name)}
                        </span>
                        {pick.reasoning && (
                          <p className="text-gray-400 text-xs mt-0.5 leading-relaxed">
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
    </div>
  );
}

export default NeutralItemSection;
