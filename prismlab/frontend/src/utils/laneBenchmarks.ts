/**
 * Lane benchmark GPM thresholds and lane result detection.
 *
 * Compares a player's GPM against role-specific benchmarks to determine
 * whether the laning phase was won, even, or lost.
 */

export const GPM_BENCHMARKS: Record<number, number> = {};

export function detectLaneResult(
  _gpm: number,
  _role: number,
): "won" | "even" | "lost" {
  return "even"; // stub
}
