/**
 * Game event trigger detection for auto-refresh.
 *
 * Pure function that compares current and previous game state to detect
 * significant events that should trigger a recommendation refresh.
 *
 * Priority order (highest first):
 * 1. Phase transitions (35 min > 20 min > 10 min)
 * 2. Death
 * 3. Roshan kill
 * 4. Tower destruction
 * 5. Gold swing (>= 2000g delta)
 *
 * Item purchase is NOT a trigger (per design decision D-02).
 */

export interface TriggerEvent {
  type:
    | "death"
    | "gold_swing"
    | "tower_kill"
    | "roshan_kill"
    | "phase_transition";
  message: string;
}

export interface PreviousState {
  deaths: number;
  netWorthAtLastRefresh: number;
  roshanState: string;
  radiantTowers: number;
  direTowers: number;
}

export interface CurrentState {
  deaths: number;
  net_worth: number;
  roshan_state: string;
  radiant_tower_count: number;
  dire_tower_count: number;
  game_clock: number;
}

/** Phase transition thresholds in seconds, checked highest-first. */
const PHASE_THRESHOLDS = [
  { seconds: 2100, message: "Late game reached (35:00)" },
  { seconds: 1200, message: "Mid-game reached (20:00)" },
  { seconds: 600, message: "Lane phase ended (10:00)" },
] as const;

/** Minimum net worth delta to trigger a gold swing event. */
const GOLD_SWING_THRESHOLD = 2000;

/**
 * Detect the highest-priority game event trigger.
 *
 * Mutates `firedPhases` to track which phase transitions have already fired
 * (ensuring each fires at most once per game).
 *
 * Returns the single highest-priority event, or null if nothing detected.
 */
export function detectTriggers(
  current: CurrentState,
  prev: PreviousState,
  firedPhases: Set<number>,
): TriggerEvent | null {
  // 1. Phase transitions (highest threshold first)
  for (const { seconds, message } of PHASE_THRESHOLDS) {
    if (current.game_clock >= seconds && !firedPhases.has(seconds)) {
      firedPhases.add(seconds);
      return { type: "phase_transition", message };
    }
  }

  // 2. Death
  if (current.deaths > prev.deaths) {
    return { type: "death", message: "Death -- reassessing priorities" };
  }

  // 3. Roshan kill
  if (
    current.roshan_state !== prev.roshanState &&
    current.roshan_state === "respawn_base"
  ) {
    return { type: "roshan_kill", message: "Roshan killed -- updating" };
  }

  // 4. Tower destruction (total tower count decreased)
  const currentTotalTowers =
    current.radiant_tower_count + current.dire_tower_count;
  const prevTotalTowers = prev.radiantTowers + prev.direTowers;
  if (currentTotalTowers < prevTotalTowers) {
    return { type: "tower_kill", message: "Tower destroyed -- map changed" };
  }

  // 5. Gold swing (>= 2000g absolute delta from last refresh)
  const goldDelta = current.net_worth - prev.netWorthAtLastRefresh;
  if (Math.abs(goldDelta) >= GOLD_SWING_THRESHOLD) {
    const sign = goldDelta > 0 ? "+" : "";
    return {
      type: "gold_swing",
      message: `Gold swing: ${sign}${Math.abs(goldDelta).toLocaleString()}g`,
    };
  }

  return null;
}
