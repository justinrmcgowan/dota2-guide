import { describe, it, expect } from "vitest";
import { GPM_BENCHMARKS, detectLaneResult } from "./laneBenchmarks";

describe("GPM_BENCHMARKS", () => {
  it("maps all 5 roles to correct GPM values", () => {
    expect(GPM_BENCHMARKS[1]).toBe(500); // Pos 1 Carry
    expect(GPM_BENCHMARKS[2]).toBe(480); // Pos 2 Mid
    expect(GPM_BENCHMARKS[3]).toBe(400); // Pos 3 Off
    expect(GPM_BENCHMARKS[4]).toBe(280); // Pos 4 Soft Sup
    expect(GPM_BENCHMARKS[5]).toBe(230); // Pos 5 Hard Sup
  });
});

describe("detectLaneResult", () => {
  it("returns 'won' when GPM exceeds +10% of benchmark (pos 1: 551 > 550)", () => {
    expect(detectLaneResult(551, 1)).toBe("won");
  });

  it("returns 'even' when GPM is exactly at benchmark (pos 1: 500)", () => {
    expect(detectLaneResult(500, 1)).toBe("even");
  });

  it("returns 'even' when GPM is at +10% boundary (pos 1: 550 is NOT > 550)", () => {
    // 500 * 1.10 = 550, and 550 is NOT > 550, so it's "even"
    expect(detectLaneResult(550, 1)).toBe("even");
  });

  it("returns 'lost' when GPM is below -10% of benchmark (pos 1: 449 < 450)", () => {
    expect(detectLaneResult(449, 1)).toBe("lost");
  });

  it("returns 'even' at -10% boundary (pos 1: 450 is NOT < 450)", () => {
    // 500 * 0.90 = 450, and 450 is NOT < 450, so it's "even"
    expect(detectLaneResult(450, 1)).toBe("even");
  });

  it("returns 'even' when GPM exactly matches pos 4 benchmark (280)", () => {
    expect(detectLaneResult(280, 4)).toBe("even");
  });

  it("returns 'won' for pos 4 when GPM exceeds +10% (350 > 308)", () => {
    // 280 * 1.10 = 308, 350 > 308 => "won"
    expect(detectLaneResult(350, 4)).toBe("won");
  });

  it("returns 'lost' for pos 5 when GPM below -10% (200 < 207)", () => {
    // 230 * 0.90 = 207, 200 < 207 => "lost"
    expect(detectLaneResult(200, 5)).toBe("lost");
  });

  it("returns 'even' for unknown role", () => {
    expect(detectLaneResult(999, 99)).toBe("even");
  });
});
