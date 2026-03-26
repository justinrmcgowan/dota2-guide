/**
 * Neutral item tier boundary constants and utility functions.
 *
 * Boundaries match NeutralItemSection.tsx TIER_TIMING values:
 * Tier 1 = 5 min, Tier 2 = 15 min, Tier 3 = 25 min, Tier 4 = 35 min, Tier 5 = 60 min.
 */

export const NEUTRAL_TIER_BOUNDARIES = [
  { tier: 1, startSeconds: 5 * 60 },  // 5:00
  { tier: 2, startSeconds: 15 * 60 }, // 15:00
  { tier: 3, startSeconds: 25 * 60 }, // 25:00
  { tier: 4, startSeconds: 35 * 60 }, // 35:00
  { tier: 5, startSeconds: 60 * 60 }, // 60:00
] as const;

/**
 * Returns the highest active neutral item tier for the given game clock time.
 * Iterates boundaries in reverse to find the highest tier whose startSeconds <= gameClockSeconds.
 * Returns null if no tier is active yet (before 5:00 or negative time).
 */
export function getCurrentTier(gameClockSeconds: number): number | null {
  for (let i = NEUTRAL_TIER_BOUNDARIES.length - 1; i >= 0; i--) {
    if (gameClockSeconds >= NEUTRAL_TIER_BOUNDARIES[i].startSeconds) {
      return NEUTRAL_TIER_BOUNDARIES[i].tier;
    }
  }
  return null;
}

/**
 * Returns the next tier to unlock and seconds remaining until it does.
 * Finds the first boundary where gameClockSeconds < startSeconds.
 * Returns null if all tiers are already active (past 60:00).
 */
export function getNextTierCountdown(
  gameClockSeconds: number,
): { tier: number; secondsRemaining: number } | null {
  for (const boundary of NEUTRAL_TIER_BOUNDARIES) {
    if (gameClockSeconds < boundary.startSeconds) {
      return {
        tier: boundary.tier,
        secondsRemaining: boundary.startSeconds - gameClockSeconds,
      };
    }
  }
  return null;
}
