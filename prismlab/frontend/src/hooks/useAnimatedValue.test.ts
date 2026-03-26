import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useAnimatedValue } from "./useAnimatedValue";

describe("useAnimatedValue", () => {
  let rafCallbacks: Array<(time: number) => void>;
  let rafId: number;
  let cancelledIds: Set<number>;

  beforeEach(() => {
    rafCallbacks = [];
    rafId = 0;
    cancelledIds = new Set();

    vi.stubGlobal("requestAnimationFrame", (cb: (time: number) => void) => {
      rafId += 1;
      rafCallbacks.push(cb);
      return rafId;
    });

    vi.stubGlobal("cancelAnimationFrame", (id: number) => {
      cancelledIds.add(id);
    });

    vi.stubGlobal("performance", {
      now: vi.fn(() => 0),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /** Flush all pending rAF callbacks at the given timestamp */
  function flushRAF(time: number) {
    const pending = [...rafCallbacks];
    rafCallbacks = [];
    for (const cb of pending) {
      cb(time);
    }
  }

  it("initially returns the target value", () => {
    const { result } = renderHook(() => useAnimatedValue(100));
    expect(result.current).toBe(100);
  });

  it("transitions toward new target when target changes", () => {
    const { result, rerender } = renderHook(
      ({ target }) => useAnimatedValue(target),
      { initialProps: { target: 100 } },
    );

    // Update performance.now for the animation start
    vi.mocked(performance.now).mockReturnValue(0);

    // Change target
    rerender({ target: 200 });

    // First frame at t=0 should schedule animation
    // Flush at 150ms (halfway through 300ms duration)
    act(() => {
      vi.mocked(performance.now).mockReturnValue(150);
      flushRAF(150);
    });

    // With ease-out curve at 50% progress: 1 - (1 - 0.5)^2 = 0.75
    // Value should be 100 + (200 - 100) * 0.75 = 175
    expect(result.current).toBe(175);
  });

  it("equals target exactly after duration completes", () => {
    const { result, rerender } = renderHook(
      ({ target }) => useAnimatedValue(target),
      { initialProps: { target: 100 } },
    );

    vi.mocked(performance.now).mockReturnValue(0);
    rerender({ target: 200 });

    // Flush at 300ms (full duration)
    act(() => {
      vi.mocked(performance.now).mockReturnValue(300);
      flushRAF(300);
    });

    expect(result.current).toBe(200);
  });

  it("respects custom duration parameter", () => {
    const { result, rerender } = renderHook(
      ({ target, duration }) => useAnimatedValue(target, duration),
      { initialProps: { target: 0, duration: 600 } },
    );

    vi.mocked(performance.now).mockReturnValue(0);
    rerender({ target: 100, duration: 600 });

    // Flush at 300ms (50% of 600ms duration)
    act(() => {
      vi.mocked(performance.now).mockReturnValue(300);
      flushRAF(300);
    });

    // Ease-out at 50%: 1 - (1 - 0.5)^2 = 0.75
    // Value should be 0 + 100 * 0.75 = 75
    expect(result.current).toBe(75);
  });

  it("returns rounded integer values", () => {
    const { result, rerender } = renderHook(
      ({ target }) => useAnimatedValue(target),
      { initialProps: { target: 0 } },
    );

    vi.mocked(performance.now).mockReturnValue(0);
    rerender({ target: 100 });

    // At 100ms: progress = 100/300 = 0.333
    // eased = 1 - (1 - 0.333)^2 = 1 - 0.667^2 = 1 - 0.4449 = 0.5551
    // value = 0 + 100 * 0.5551 = 55.51 -> rounds to 56
    act(() => {
      vi.mocked(performance.now).mockReturnValue(100);
      flushRAF(100);
    });

    expect(Number.isInteger(result.current)).toBe(true);
  });

  it("cancels requestAnimationFrame on unmount", () => {
    const { unmount, rerender } = renderHook(
      ({ target }) => useAnimatedValue(target),
      { initialProps: { target: 100 } },
    );

    vi.mocked(performance.now).mockReturnValue(0);
    rerender({ target: 200 });

    unmount();

    // Should have called cancelAnimationFrame
    expect(cancelledIds.size).toBeGreaterThan(0);
  });

  it("animation restarts from current display value when target changes mid-animation", () => {
    const { result, rerender } = renderHook(
      ({ target }) => useAnimatedValue(target),
      { initialProps: { target: 0 } },
    );

    // Start animating toward 100
    vi.mocked(performance.now).mockReturnValue(0);
    rerender({ target: 100 });

    // Advance to 150ms (halfway) - value should be ~75 (ease-out)
    act(() => {
      vi.mocked(performance.now).mockReturnValue(150);
      flushRAF(150);
    });

    const midValue = result.current;
    expect(midValue).toBeGreaterThan(0);
    expect(midValue).toBeLessThan(100);

    // Now change target to 200 mid-animation
    vi.mocked(performance.now).mockReturnValue(150);
    rerender({ target: 200 });

    // Complete the new animation
    act(() => {
      vi.mocked(performance.now).mockReturnValue(450);
      flushRAF(450);
    });

    // Should reach 200
    expect(result.current).toBe(200);
  });
});
