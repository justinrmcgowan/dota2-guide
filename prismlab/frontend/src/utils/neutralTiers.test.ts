import { describe, it, expect } from "vitest";
import {
  NEUTRAL_TIER_BOUNDARIES,
  getCurrentTier,
  getNextTierCountdown,
} from "./neutralTiers";

describe("NEUTRAL_TIER_BOUNDARIES", () => {
  it("has 5 tiers with correct boundaries (5/15/25/35/60 minutes)", () => {
    expect(NEUTRAL_TIER_BOUNDARIES).toHaveLength(5);
    expect(NEUTRAL_TIER_BOUNDARIES[0]).toEqual({ tier: 1, startSeconds: 300 });
    expect(NEUTRAL_TIER_BOUNDARIES[1]).toEqual({ tier: 2, startSeconds: 900 });
    expect(NEUTRAL_TIER_BOUNDARIES[2]).toEqual({
      tier: 3,
      startSeconds: 1500,
    });
    expect(NEUTRAL_TIER_BOUNDARIES[3]).toEqual({
      tier: 4,
      startSeconds: 2100,
    });
    expect(NEUTRAL_TIER_BOUNDARIES[4]).toEqual({
      tier: 5,
      startSeconds: 3600,
    });
  });
});

describe("getCurrentTier", () => {
  it("returns null at game start (0s)", () => {
    expect(getCurrentTier(0)).toBeNull();
  });

  it("returns null just before tier 1 at 4:59 (299s)", () => {
    expect(getCurrentTier(299)).toBeNull();
  });

  it("returns 1 at exactly 5:00 (300s)", () => {
    expect(getCurrentTier(300)).toBe(1);
  });

  it("returns 1 at 7:00 (420s), still tier 1", () => {
    expect(getCurrentTier(420)).toBe(1);
  });

  it("returns 2 at 15:00 (900s)", () => {
    expect(getCurrentTier(900)).toBe(2);
  });

  it("returns 3 at 25:00 (1500s)", () => {
    expect(getCurrentTier(1500)).toBe(3);
  });

  it("returns 4 at 35:00 (2100s)", () => {
    expect(getCurrentTier(2100)).toBe(4);
  });

  it("returns 5 at 60:00 (3600s)", () => {
    expect(getCurrentTier(3600)).toBe(5);
  });

  it("returns 5 past all tiers (5000s)", () => {
    expect(getCurrentTier(5000)).toBe(5);
  });

  it("returns null for negative time (pre-horn)", () => {
    expect(getCurrentTier(-60)).toBeNull();
  });
});

describe("getNextTierCountdown", () => {
  it("returns tier 1 with 300s remaining at game start", () => {
    expect(getNextTierCountdown(0)).toEqual({
      tier: 1,
      secondsRemaining: 300,
    });
  });

  it("returns tier 2 with 600s remaining at exactly 5:00 (300s)", () => {
    expect(getNextTierCountdown(300)).toEqual({
      tier: 2,
      secondsRemaining: 600,
    });
  });

  it("returns tier 2 with correct countdown at 10:00 (600s)", () => {
    expect(getNextTierCountdown(600)).toEqual({
      tier: 2,
      secondsRemaining: 300,
    });
  });

  it("returns null when all tiers are active (3600s)", () => {
    expect(getNextTierCountdown(3600)).toBeNull();
  });

  it("returns null past all tiers (5000s)", () => {
    expect(getNextTierCountdown(5000)).toBeNull();
  });

  it("returns tier 1 countdown for negative time", () => {
    expect(getNextTierCountdown(-60)).toEqual({
      tier: 1,
      secondsRemaining: 360,
    });
  });
});
