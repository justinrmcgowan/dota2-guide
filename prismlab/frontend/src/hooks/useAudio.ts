import { useEffect, useRef } from "react";
import { useRefreshStore } from "../stores/refreshStore";
import { useRecommendationStore } from "../stores/recommendationStore";
import { useAudioStore } from "../stores/audioStore";
import { speak, sanitizeForSpeech, humanizeItemName } from "../utils/audioUtils";
import type { RecommendResponse } from "../types/recommendation";

/**
 * useAudio — App-level hook that wires audio coaching callouts to GSI and
 * recommendation events.
 *
 * Three responsibilities:
 *   1. Unlock AudioContext on first user click (autoplay policy compliance)
 *   2. Speak GSI toast messages when refreshStore.lastToast fires
 *   3. Announce the top priority item when new recommendations arrive
 *
 * Must be called once at the top of the App component (alongside
 * useGameIntelligence and useLiveDraft). Returns void.
 */
export function useAudio(): void {
  const audioCtxRef = useRef<AudioContext | null>(null);

  // Block 1: AudioContext unlock for autoplay policy.
  // Chrome and other browsers suspend AudioContext until a user gesture.
  // Listening for "click" at the document level catches the first interaction.
  useEffect(() => {
    const unlock = () => {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioContext();
      } else if (audioCtxRef.current.state === "suspended") {
        audioCtxRef.current.resume().catch(() => {});
      }
    };
    document.addEventListener("click", unlock);
    return () => document.removeEventListener("click", unlock);
  }, []);

  // Block 2: Toast subscription — speaks sanitized GSI trigger toast messages.
  // Uses Zustand subscribe (not a React hook call) so it runs outside the
  // render cycle. useAudioStore.getState() avoids stale closure captures.
  useEffect(() => {
    return useRefreshStore.subscribe((state) => {
      const { enabled, volume } = useAudioStore.getState();
      if (!enabled || !state.lastToast) return;
      speak(sanitizeForSpeech(state.lastToast.message), volume);
    });
  }, []);

  // Block 3: Recommendation subscription — announces top priority item when
  // new recommendation data arrives (not on reload/persist hydration).
  // prevDataRef guards against double-fire for the same data reference.
  useEffect(() => {
    const prevDataRef = { current: null as RecommendResponse | null };
    return useRecommendationStore.subscribe((state) => {
      const { enabled, volume } = useAudioStore.getState();
      if (!enabled) return;
      if (state.data && state.data !== prevDataRef.current && !state.isLoading) {
        prevDataRef.current = state.data;
        const topItem = state.data.phases[0]?.items[0];
        if (topItem) {
          speak(`Consider buying ${humanizeItemName(topItem.item_name)}`, volume);
        }
      }
    });
  }, []);
}
