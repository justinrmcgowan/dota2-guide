/**
 * Lane benchmark GPM thresholds and lane result detection.
 *
 * Compares a player's GPM against role-specific benchmarks to determine
 * whether the laning phase was won, even, or lost. Thresholds use +/-10%
 * of the role benchmark.
 */

export const GPM_BENCHMARKS: Record<number, number> = {
  1: 500, // Pos 1 Carry
  2: 480, // Pos 2 Mid
  3: 400, // Pos 3 Off
  4: 280, // Pos 4 Soft Sup
  5: 230, // Pos 5 Hard Sup
};

/**
 * Classify lane result based on GPM vs role benchmark.
 *
 * - "won" if GPM > benchmark * 1.10 (strictly greater)
 * - "lost" if GPM < benchmark * 0.90 (strictly less)
 * - "even" otherwise (within +/-10% inclusive of boundaries)
 *
 * Returns "even" for unknown roles as a safe default.
 */
export function detectLaneResult(
  gpm: number,
  role: number,
): "won" | "even" | "lost" {
  const benchmark = GPM_BENCHMARKS[role];
  if (!benchmark) return "even"; // Unknown role, safe default

  if (gpm > benchmark * 1.1) return "won";
  if (gpm < benchmark * 0.9) return "lost";
  return "even";
}
