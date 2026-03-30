import { useCallback, useEffect, useRef, useState } from "react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { useRecommendationStore } from "../stores/recommendationStore";
import { api } from "../api/client";
import { steamId64ToAccountId } from "../utils/steamId";
import type { Hero } from "../types/hero";
import type { LiveMatchResponse } from "../types/livematch";

/** Polling interval during active draft (3s for fast hero detection). */
const DRAFT_POLL_MS = 3_000;

/**
 * Live draft polling hook. Fetches draft data from the live match API
 * when GSI connects, polls every 3s during hero selection, and
 * auto-populates gameStore with allies, opponents, side, hero, and role.
 *
 * Auto-triggers a two-pass recommendation when hero+role are first detected.
 *
 * @param heroes - Array of all heroes from useHeroes()
 * @param recommendTwoPass - Two-pass recommend function from useRecommendation()
 * @returns fetchDraft for manual refresh and isPolling state
 */
export function useLiveDraft(
  heroes: Hero[],
  recommendTwoPass: () => Promise<void>,
): {
  fetchDraft: () => void;
  isPolling: boolean;
} {
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const draftCompleteRef = useRef(false);
  const autoTriggeredRef = useRef(false);
  const [isPolling, setIsPolling] = useState(false);
  const heroesRef = useRef(heroes);
  const recommendRef = useRef(recommendTwoPass);

  useEffect(() => {
    heroesRef.current = heroes;
  }, [heroes]);

  useEffect(() => {
    recommendRef.current = recommendTwoPass;
  }, [recommendTwoPass]);

  const processDraftData = useCallback(
    (match: LiveMatchResponse, accountId: number, heroList: Hero[]) => {
      const me = match.players.find((p) => p.account_id === accountId);
      if (!me) return;

      const myTeamIsRadiant = me.is_radiant;
      const gameStore = useGameStore.getState();

      gameStore.setSide(myTeamIsRadiant ? "radiant" : "dire");

      const allyHeroes = match.players
        .filter(
          (p) =>
            p.is_radiant === myTeamIsRadiant &&
            p.account_id !== accountId &&
            p.hero_id > 0,
        )
        .map((p) => heroList.find((h) => h.id === p.hero_id))
        .filter((h): h is Hero => h != null);

      const opponentHeroes = match.players
        .filter((p) => p.is_radiant !== myTeamIsRadiant && p.hero_id > 0)
        .map((p) => heroList.find((h) => h.id === p.hero_id))
        .filter((h): h is Hero => h != null);

      allyHeroes.forEach((hero, i) => {
        if (i < 4) gameStore.setAlly(i, hero);
      });

      opponentHeroes.forEach((hero, i) => {
        if (i < 5) gameStore.setOpponent(i, hero);
      });

      if (me.hero_id > 0) {
        const myHero = heroList.find((h) => h.id === me.hero_id);
        if (myHero) gameStore.selectHero(myHero);
      }

      if (
        me.position != null &&
        me.position >= 1 &&
        me.position <= 5
      ) {
        gameStore.setRole(me.position);
      }

      if (match.players.every((p) => p.hero_id > 0)) {
        draftCompleteRef.current = true;
      }

      // --- Auto-trigger: fire two-pass recommend when hero+role first detected ---
      const updatedGame = useGameStore.getState();
      const recStore = useRecommendationStore.getState();
      if (
        updatedGame.selectedHero &&
        updatedGame.role !== null &&
        !autoTriggeredRef.current &&
        !recStore.data &&
        !recStore.isLoading
      ) {
        autoTriggeredRef.current = true;
        recommendRef.current();
      }
    },
    [],
  );

  const fetchDraft = useCallback(async () => {
    const steamId = localStorage.getItem("prismlab_steam_id");
    if (!steamId) return;

    let accountId: number;
    try {
      accountId = steamId64ToAccountId(steamId);
    } catch {
      return;
    }

    try {
      const match = await api.getLiveMatch(accountId);
      if (!match) return;
      processDraftData(match, accountId, heroesRef.current);
    } catch (err) {
      console.warn("Live draft fetch failed:", err);
    }
  }, [processDraftData]);

  useEffect(() => {
    const unsub = useGsiStore.subscribe((state, prev) => {
      if (prev.gsiStatus !== "connected" && state.gsiStatus === "connected") {
        draftCompleteRef.current = false;
        autoTriggeredRef.current = false; // Reset on new connection
        fetchDraft();
        pollRef.current = setInterval(() => {
          if (!draftCompleteRef.current) fetchDraft();
        }, DRAFT_POLL_MS);
        setIsPolling(true);
      }

      if (state.gsiStatus !== "connected" && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        setIsPolling(false);
      }
    });

    return () => {
      unsub();
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [fetchDraft]);

  return { fetchDraft, isPolling };
}
