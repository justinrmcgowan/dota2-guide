import { useState } from "react";
import type { TimingBucketUI } from "../../types/recommendation";

interface TimingBarProps {
  buckets: TimingBucketUI[];
  confidence: "strong" | "moderate" | "weak";
  isUrgent: boolean;
  isPurchased: boolean;
  currentGameClock: number | null;
  currentGold: number | null;
  itemCost: number | null;
  goodRange: string;
  ontrackRange: string;
  lateRange: string;
  goodWinRate: number;
  ontrackWinRate: number;
  lateWinRate: number;
  totalGames: number;
}

function TimingBar({
  buckets,
  confidence,
  isUrgent: _isUrgent,
  isPurchased,
  currentGameClock,
  currentGold,
  itemCost,
  goodRange,
  ontrackRange,
  lateRange,
  goodWinRate,
  ontrackWinRate,
  lateWinRate,
  totalGames,
}: TimingBarProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  // Return nothing if purchased (D-10)
  if (isPurchased) return null;

  // Compute zone bucket counts for proportional widths
  const goodBuckets = buckets.filter((b) => b.zone === "good");
  const ontrackBuckets = buckets.filter((b) => b.zone === "ontrack");
  const lateBuckets = buckets.filter((b) => b.zone === "late");

  const totalBuckets = buckets.length || 1;
  const goodPct = (goodBuckets.length / totalBuckets) * 100;
  const ontrackPct = (ontrackBuckets.length / totalBuckets) * 100;
  const latePct = (lateBuckets.length / totalBuckets) * 100;

  // Confidence opacity (D-04)
  const opacity = confidence === "strong" ? 1 : confidence === "moderate" ? 0.7 : 0.4;

  // LiveTimingMarker position
  const maxTime = buckets.length > 0 ? Math.max(...buckets.map((b) => b.time)) : 1;
  const markerPct =
    currentGameClock !== null
      ? Math.min(Math.max((currentGameClock / maxTime) * 100, 0), 100)
      : null;

  // WindowPassed detection (D-09)
  const lateBucketMax =
    lateBuckets.length > 0 ? Math.max(...lateBuckets.map((b) => b.time)) : 0;
  const isWindowPassed =
    currentGameClock !== null && lateBucketMax > 0 && currentGameClock > lateBucketMax;

  // Gold away text
  const showGoldText =
    currentGold !== null && itemCost !== null && !isWindowPassed;
  const isAffordable = currentGold !== null && itemCost !== null && currentGold >= itemCost;
  const goldDiff = currentGold !== null && itemCost !== null ? itemCost - currentGold : 0;

  // Aria label for accessibility
  const ariaLabel = `Timing: good ${goodRange}, on-track ${ontrackRange}, late ${lateRange}.${
    _isUrgent ? " Timing-critical item." : ""
  }`;

  return (
    <div className="w-full mt-1">
      {/* Bar container */}
      <div
        role="img"
        aria-label={ariaLabel}
        tabIndex={0}
        className="relative w-full h-[6px] bg-surface-container cursor-default"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
      >
        {/* Tooltip */}
        {showTooltip && (
          <div
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-[160px] p-2 bg-surface-container-highest shadow-[0_0_16px_rgb(255_180_172/0.05)]"
            style={{ fontFamily: "var(--font-body)" }}
          >
            {/* Good zone row */}
            {goodBuckets.length > 0 && (
              <div className="flex flex-col mb-1">
                <span className="text-xs text-radiant">Good</span>
                <span
                  className="text-xs font-semibold text-on-surface"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {goodRange}
                </span>
                <span
                  className="text-xs font-semibold text-secondary"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {Math.round(goodWinRate * 100)}% WR
                </span>
              </div>
            )}

            {/* On-track zone row */}
            {ontrackBuckets.length > 0 && (
              <div className="flex flex-col mb-1">
                <span className="text-xs text-secondary-fixed-dim">On-track</span>
                <span
                  className="text-xs font-semibold text-on-surface"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {ontrackRange}
                </span>
                <span
                  className="text-xs font-semibold text-on-surface"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {Math.round(ontrackWinRate * 100)}% WR
                </span>
              </div>
            )}

            {/* Late zone row */}
            {lateBuckets.length > 0 && (
              <div className="flex flex-col mb-1">
                <span className="text-xs text-primary">Late</span>
                <span
                  className="text-xs font-semibold text-on-surface"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {lateRange}
                </span>
                <span
                  className="text-xs font-semibold text-primary"
                  style={{ fontFeatureSettings: '"tnum"' }}
                >
                  {Math.round(lateWinRate * 100)}% WR
                </span>
              </div>
            )}

            {/* Divider */}
            <div className="h-px bg-outline-variant/15 my-1" />

            {/* Confidence / sample size */}
            <span
              className="text-[11px] text-on-surface-variant/60"
              style={{ fontFeatureSettings: '"tnum"' }}
            >
              Based on {totalGames.toLocaleString()} games (
              {confidence === "weak" ? "limited data" : confidence})
            </span>
          </div>
        )}

        {/* Zone segments or window-passed overlay */}
        {isWindowPassed ? (
          <div
            className="w-full h-full bg-surface-container-high transition-opacity duration-300 ease"
          />
        ) : (
          <div className="flex w-full h-full" style={{ opacity }}>
            {goodPct > 0 && (
              <div
                className="h-full bg-radiant"
                style={{ width: `${goodPct}%` }}
              />
            )}
            {ontrackPct > 0 && (
              <div
                className="h-full bg-secondary-fixed-dim"
                style={{ width: `${ontrackPct}%` }}
              />
            )}
            {latePct > 0 && (
              <div
                className="h-full bg-primary-container"
                style={{ width: `${latePct}%` }}
              />
            )}
          </div>
        )}

        {/* LiveTimingMarker (D-08) — hidden when window passed */}
        {markerPct !== null && !isWindowPassed && (
          <div
            className="absolute top-[-2px] w-[2px] h-[10px] bg-on-surface pointer-events-none"
            style={{ left: `${markerPct}%` }}
          />
        )}
      </div>

      {/* Window passed label */}
      {isWindowPassed && (
        <span className="text-[11px] font-semibold text-on-surface-variant/50">
          Window passed
        </span>
      )}

      {/* Gold away / affordable text (D-08) */}
      {showGoldText && (
        <span
          className={`text-xs ${isAffordable ? "text-radiant" : "text-on-surface-variant"}`}
        >
          {isAffordable ? "Affordable now" : `${goldDiff}g away`}
        </span>
      )}
    </div>
  );
}

export default TimingBar;
