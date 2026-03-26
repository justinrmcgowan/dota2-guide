import { useRef, useEffect, useState } from "react";
import { useGsiStore } from "../../stores/gsiStore";
import { useAnimatedValue } from "../../hooks/useAnimatedValue";

const numberFmt = new Intl.NumberFormat("en-US");

function LiveStatsBar() {
  const gsiStatus = useGsiStore((s) => s.gsiStatus);
  const liveState = useGsiStore((s) => s.liveState);

  // Animated values (safe to call unconditionally -- hooks must not be conditional)
  const gold = liveState?.gold ?? 0;
  const gpm = liveState?.gpm ?? 0;
  const netWorth = liveState?.net_worth ?? 0;

  const animatedGold = useAnimatedValue(gold);
  const animatedGpm = useAnimatedValue(gpm);
  const animatedNw = useAnimatedValue(netWorth);

  // Pulse states
  const [goldPulse, setGoldPulse] = useState(false);
  const [deathPulse, setDeathPulse] = useState(false);

  const prevGoldRef = useRef(gold);
  const prevDeathsRef = useRef(liveState?.deaths ?? 0);

  useEffect(() => {
    if (!liveState) return;

    // Gold pulse: >= 300 increase
    if (liveState.gold - prevGoldRef.current >= 300) {
      setGoldPulse(true);
      const timer = setTimeout(() => setGoldPulse(false), 500);
      prevGoldRef.current = liveState.gold;
      return () => clearTimeout(timer);
    }
    prevGoldRef.current = liveState.gold;
  }, [liveState?.gold]);

  useEffect(() => {
    if (!liveState) return;

    // Death pulse: deaths increased
    if (liveState.deaths > prevDeathsRef.current) {
      setDeathPulse(true);
      const timer = setTimeout(() => setDeathPulse(false), 500);
      prevDeathsRef.current = liveState.deaths;
      return () => clearTimeout(timer);
    }
    prevDeathsRef.current = liveState.deaths;
  }, [liveState?.deaths]);

  // Visibility guard (D-07): only render when GSI connected + in-game
  if (
    gsiStatus !== "connected" ||
    !liveState ||
    liveState.game_state !== "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
  ) {
    return null;
  }

  return (
    <div
      data-testid="live-stats-bar"
      className={`rounded-lg p-3 border border-bg-elevated mb-4 transition-colors duration-500 ${
        goldPulse
          ? "bg-radiant/20"
          : deathPulse
            ? "bg-dire/20"
            : "bg-bg-elevated/50"
      }`}
    >
      {/* Line 1: Gold | GPM | Net Worth */}
      <div className="flex items-baseline gap-3">
        <span className="text-amber-400 font-bold text-lg">
          {numberFmt.format(animatedGold)}
          <span className="text-amber-400/60 text-xs ml-1">g</span>
        </span>
        <span className="text-text-muted text-sm border-l border-bg-elevated pl-3">
          {numberFmt.format(animatedGpm)}
          <span className="text-text-muted/60 text-xs ml-1">GPM</span>
        </span>
        <span className="text-text-muted text-sm border-l border-bg-elevated pl-3">
          {numberFmt.format(animatedNw)}
          <span className="text-text-muted/60 text-xs ml-1">NW</span>
        </span>
      </div>

      {/* Line 2: K / D / A */}
      <div className="flex items-center gap-1 mt-1 text-sm font-medium">
        <span className="text-radiant">{liveState.kills}</span>
        <span className="text-text-muted/40">/</span>
        <span className="text-dire">{liveState.deaths}</span>
        <span className="text-text-muted/40">/</span>
        <span className="text-text-muted">{liveState.assists}</span>
      </div>
    </div>
  );
}

export default LiveStatsBar;
