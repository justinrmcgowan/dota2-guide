/**
 * Game event trigger detection for auto-refresh.
 *
 * Pure function that compares current and previous game state to detect
 * significant events that should trigger a recommendation refresh.
 */

export interface TriggerEvent {
  type: "death" | "gold_swing" | "tower_kill" | "roshan_kill" | "phase_transition";
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

export function detectTriggers(
  _current: CurrentState,
  _prev: PreviousState,
  _firedPhases: Set<number>,
): TriggerEvent | null {
  return null; // stub
}
