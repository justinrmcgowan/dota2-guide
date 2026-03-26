import { useState, useEffect, useRef } from "react";

/**
 * requestAnimationFrame-based counting animation hook.
 * Smoothly interpolates from previous value to target over the given duration
 * using an ease-out curve for natural deceleration.
 *
 * Returns Math.round() of interpolated value (gold/GPM are integers).
 *
 * @param target - The target number to animate toward
 * @param duration - Animation duration in milliseconds (default 300ms)
 * @returns The current animated integer value
 */
export function useAnimatedValue(target: number, duration = 300): number {
  const [display, setDisplay] = useState(target);
  const displayRef = useRef(target); // tracks latest display value to avoid stale closure
  const startValRef = useRef(target);
  const startTimeRef = useRef(0);
  const rafRef = useRef(0);

  useEffect(() => {
    startValRef.current = displayRef.current; // capture current display as start
    startTimeRef.current = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out curve: 1 - (1 - progress)^2 for natural deceleration
      const eased = 1 - (1 - progress) ** 2;
      const current = Math.round(
        startValRef.current + (target - startValRef.current) * eased,
      );
      displayRef.current = current;
      setDisplay(current);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return display;
}
