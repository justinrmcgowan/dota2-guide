import { useCallback, useEffect, useRef, useState } from "react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { api } from "../api/client";
import { steamId64ToAccountId } from "../utils/steamId";
import type { Hero } from "../types/hero";
import type { LiveMatchResponse } from "../types/livematch";

/**
 * Live draft polling hook. Fetches draft data from the live match API
 * when GSI connects, polls every 10s during hero selection, and
 * auto-populates gameStore with allies, opponents, side, hero, and role.
 *
 * @param heroes - Array of all heroes from useHeroes()
 * @returns fetchDraft for manual refresh (D-05) and isPolling state
 */
export function useLiveDraft(heroes: Hero[]): {
  fetchDraft: () => void;
  isPolling: boolean;
} {
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const draftCompleteRef = useRef(false);
  const [isPolling, setIsPolling] = useState(false);
  const heroesRef = useRef(heroes);

  // Keep heroesRef in sync
  useEffect(() => {
    heroesRef.current = heroes;
  }, [heroes]);

  /**
   * Process draft data from the live match API and populate gameStore.
   */
  const processDraftData = useCallback(
    (match: LiveMatchResponse, accountId: number, heroList: Hero[]) => {
      // Find user in players by account_id
      const me = match.players.find((p) => p.account_id === accountId);
      if (!me) return; // User not found in this game (Pitfall 4)

      const myTeamIsRadiant = me.is_radiant;
      const gameStore = useGameStore.getState();

      // Set side (D-06)
      gameStore.setSide(myTeamIsRadiant ? "radiant" : "dire");

      // Filter allies (same team, exclude self, hero_id > 0 -- Pitfall 2)
      const allyHeroes = match.players
        .filter(
          (p) =>
            p.is_radiant === myTeamIsRadiant &&
            p.account_id !== accountId &&
            p.hero_id > 0,
        )
        .map((p) => heroList.find((h) => h.id === p.hero_id))
        .filter((h): h is Hero => h != null);

      // Filter opponents (other team, hero_id > 0)
      const opponentHeroes = match.players
        .filter((p) => p.is_radiant !== myTeamIsRadiant && p.hero_id > 0)
        .map((p) => heroList.find((h) => h.id === p.hero_id))
        .filter((h): h is Hero => h != null);

      // Auto-fill allies (up to 4 slots) -- D-06, D-08: overwrite existing
      allyHeroes.forEach((hero, i) => {
        if (i < 4) gameStore.setAlly(i, hero);
      });

      // Auto-fill opponents (up to 5 slots)
      opponentHeroes.forEach((hero, i) => {
        if (i < 5) gameStore.setOpponent(i, hero);
      });

      // Auto-set user's own hero if picked
      if (me.hero_id > 0) {
        const myHero = heroList.find((h) => h.id === me.hero_id);
        if (myHero) gameStore.selectHero(myHero);
      }

      // Auto-suggest role from Stratz position data (Pitfall 5)
      if (
        me.position != null &&
        me.position >= 1 &&
        me.position <= 5
      ) {
        gameStore.setRole(me.position);
      }

      // Check if draft is complete: all 10 heroes picked
      if (match.players.every((p) => p.hero_id > 0)) {
        draftCompleteRef.current = true;
      }
    },
    [],
  );

  /**
   * Fetch live draft data for the configured Steam ID.
   */
  const fetchDraft = useCallback(async () => {
    const steamId = localStorage.getItem("prismlab_steam_id");
    if (!steamId) return;

    let accountId: number;
    try {
      accountId = steamId64ToAccountId(steamId);
    } catch {
      return; // Invalid Steam ID
    }

    try {
      const match = await api.getLiveMatch(accountId);
      if (!match) return; // No live match found
      processDraftData(match, accountId, heroesRef.current);
    } catch (err) {
      console.warn("Live draft fetch failed:", err);
    }
  }, [processDraftData]);

  // GSI subscription: start/stop polling on connect/disconnect
  useEffect(() => {
    const unsub = useGsiStore.subscribe((state, prev) => {
      // On GSI connect: fetch immediately + start polling (D-03, D-04)
      if (prev.gsiStatus !== "connected" && state.gsiStatus === "connected") {
        draftCompleteRef.current = false;
        fetchDraft(); // Immediate fetch
        // Start polling every 10s during pick phase
        pollRef.current = setInterval(() => {
          if (!draftCompleteRef.current) fetchDraft();
        }, 10_000);
        setIsPolling(true);
      }

      // On GSI disconnect: stop polling
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
