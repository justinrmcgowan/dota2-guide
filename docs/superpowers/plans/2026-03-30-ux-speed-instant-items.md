# UX Speed + Instant Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zero manual clicks from hero pick (with GSI) to seeing starting items. Instant rules-based items in <2s, full Claude recommendation streams in behind.

**Architecture:** Two-pass recommendation: fast-mode fires immediately on hero+role detection, full auto/deep fires in parallel. Frontend merges partial → full results. Draft polling reduced from 10s → 3s. Enrichment pipeline parallelized with asyncio.gather().

**Tech Stack:** React 18 + Zustand (frontend), FastAPI + asyncio (backend), existing HybridRecommender infrastructure

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/hooks/useRecommendation.ts` | Modify | Add `recommendTwoPass()` two-pass method |
| `frontend/src/hooks/useLiveDraft.ts` | Modify | 3s polling, auto-trigger on hero+role detection |
| `frontend/src/hooks/useGameIntelligence.ts` | Modify | GSI hero_id change triggers immediate draft fetch |
| `frontend/src/stores/recommendationStore.ts` | Modify | Add `isPartial` flag, `mergeData()` action |
| `frontend/src/components/timeline/ItemTimeline.tsx` | Modify | Render partial state with loading indicators |
| `frontend/src/components/draft/GetBuildButton.tsx` | Modify | Show "Updating..." during two-pass merge |
| `frontend/src/components/layout/MainPanel.tsx` | Modify | Pass `isPartial` prop to ItemTimeline |
| `frontend/src/App.tsx` | Modify | Wire recommendTwoPass + fetchDraft to hooks |
| `backend/engine/recommender.py` | Modify | Parallelize `_enrich_all` with asyncio.gather() |

---

### Task 1: Parallelize Backend Enrichment

The simplest, safest change. `_enrich_all` currently runs 4 independent enrichment steps sequentially. Parallelize them.

**Files:**
- Modify: `prismlab/backend/engine/recommender.py:430-453`
- Test: Manual — hit `POST /api/recommend` and compare latency before/after

- [ ] **Step 1: Read the current `_enrich_all` method**

Confirm the 4 enrichment calls are independent (no shared state between them):
- `_enrich_timing_data` — reads from DataCache + optional DB fetch
- `_enrich_build_paths` — reads from DataCache only (sync, but wrapped in async)
- `_enrich_win_condition` — reads from DataCache only (sync)
- `_enrich_win_probability` — reads from DataCache only (sync)

All 4 read from `self.cache` (DataCache) which is thread-safe (frozen dicts). No writes. Safe to parallelize.

- [ ] **Step 2: Rewrite `_enrich_all` with asyncio.gather()**

Replace the sequential calls in `prismlab/backend/engine/recommender.py`:

```python
import asyncio

# ... inside class HybridRecommender ...

async def _enrich_all(
    self,
    request: RecommendRequest,
    phases: list[RecommendPhase],
    db: AsyncSession,
) -> tuple[list[ItemTimingResponse], list[BuildPathResponse], WinConditionResponse | None, float | None]:
    """Run all post-LLM enrichment steps in parallel."""
    if not self.cache:
        return [], [], None, None

    async def _timing() -> list[ItemTimingResponse]:
        return await self._enrich_timing_data(request.hero_id, phases, db)

    async def _build_paths() -> list[BuildPathResponse]:
        return self._enrich_build_paths(request, phases)

    async def _win_cond() -> WinConditionResponse | None:
        return self._enrich_win_condition(request)

    async def _win_prob() -> float | None:
        return self._enrich_win_probability(request)

    timing_data, build_paths, win_condition, win_probability = await asyncio.gather(
        _timing(), _build_paths(), _win_cond(), _win_prob()
    )
    return timing_data, build_paths, win_condition, win_probability
```

- [ ] **Step 3: Verify backend starts and responds**

Run:
```bash
cd prismlab/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then test with an existing recommend request. Verify response structure is identical to before.

- [ ] **Step 4: Commit**

```bash
git add prismlab/backend/engine/recommender.py
git commit -m "perf: parallelize enrichment pipeline with asyncio.gather()"
```

---

### Task 2: Add Partial State + Merge to Recommendation Store

The store needs to support a two-pass recommendation flow: fast partial results, then full results merged over them.

**Files:**
- Modify: `prismlab/frontend/src/stores/recommendationStore.ts`

- [ ] **Step 1: Add `isPartial` flag and `mergeData` action to the store interface**

Add to the `RecommendationStore` interface in `prismlab/frontend/src/stores/recommendationStore.ts`:

```typescript
interface RecommendationStore {
  data: RecommendResponse | null;
  isLoading: boolean;
  isPartial: boolean; // true when showing fast-mode results, waiting for full
  error: string | null;
  selectedItemId: string | null;
  purchasedItems: Set<string>;
  dismissedItems: Set<string>;

  setData: (data: RecommendResponse) => void;
  setPartialData: (data: RecommendResponse) => void; // Sets data + isPartial=true
  mergeData: (data: RecommendResponse) => void; // Replaces data, isPartial=false
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
  selectItem: (phaseItemKey: string | null) => void;
  togglePurchased: (phaseItemKey: string) => void;
  dismissItem: (phaseItemKey: string) => void;
  getPurchasedItemIds: () => number[];
  getDismissedItemIds: () => number[];
  clearResults: () => void;
  clear: () => void;
}
```

- [ ] **Step 2: Implement the new state and actions**

Add to the store creation in `prismlab/frontend/src/stores/recommendationStore.ts`, after the existing `isLoading: false,` line:

```typescript
isPartial: false,
```

Add the `setPartialData` action after the existing `setData` action:

```typescript
setPartialData: (data) => {
  set({
    data,
    error: null,
    isLoading: false,
    isPartial: true,
  });
},
```

Add the `mergeData` action after `setPartialData`:

```typescript
mergeData: (data) => {
  // Re-apply purchased state (same logic as setData)
  const oldPurchased = get().purchasedItems;
  const oldItemIds = new Set<number>();
  for (const key of oldPurchased) {
    const parts = key.split("-");
    const id = parseInt(parts[parts.length - 1], 10);
    if (!isNaN(id)) oldItemIds.add(id);
  }

  const newPurchased = new Set<string>();
  if (oldItemIds.size > 0) {
    for (const phase of data.phases) {
      for (const item of phase.items) {
        if (oldItemIds.has(item.item_id)) {
          newPurchased.add(`${phase.phase}-${item.item_id}`);
        }
      }
    }
  }

  set({
    data,
    error: null,
    isLoading: false,
    isPartial: false,
    purchasedItems: newPurchased.size > 0 ? newPurchased : oldPurchased,
  });
},
```

Also update `clearResults` and `clear` to reset `isPartial`:

```typescript
clearResults: () =>
  set({ data: null, error: null, selectedItemId: null, isPartial: false }),

clear: () =>
  set({
    data: null,
    isLoading: false,
    isPartial: false,
    error: null,
    selectedItemId: null,
    purchasedItems: new Set<string>(),
    dismissedItems: new Set<string>(),
  }),
```

- [ ] **Step 3: Commit**

```bash
git add prismlab/frontend/src/stores/recommendationStore.ts
git commit -m "feat: add isPartial flag and mergeData to recommendation store"
```

---

### Task 3: Two-Pass Recommendation in useRecommendation

The core UX change. Fire fast-mode immediately, show results, then fire full auto/deep in parallel and merge.

**Files:**
- Modify: `prismlab/frontend/src/hooks/useRecommendation.ts`

- [ ] **Step 1: Add `recommendTwoPass` method**

Replace the entire contents of `prismlab/frontend/src/hooks/useRecommendation.ts`:

```typescript
import { useRecommendationStore } from "../stores/recommendationStore";
import { useGameStore } from "../stores/gameStore";
import { api } from "../api/client";
import type { RecommendRequest } from "../types/recommendation";
import { PLAYSTYLE_OPTIONS } from "../utils/constants";

function buildRequest(): RecommendRequest | null {
  const game = useGameStore.getState();
  if (!game.selectedHero || game.role === null) return null;

  const store = useRecommendationStore.getState();
  const purchasedItemIds = store.getPurchasedItemIds();
  const dismissedItemIds = store.getDismissedItemIds();
  const excludedItemIds = [...new Set([...purchasedItemIds, ...dismissedItemIds])];

  const playstyle =
    game.playstyle ?? PLAYSTYLE_OPTIONS[game.role]?.[0] ?? "Farm-first";

  return {
    hero_id: game.selectedHero.id,
    role: game.role,
    playstyle,
    side: game.side ?? "radiant",
    lane: game.lane ?? "safe",
    lane_opponents: game.laneOpponents.length > 0
      ? game.laneOpponents.map((h) => h.id)
      : game.opponents.filter(Boolean).map((h) => h!.id).slice(0, 2),
    allies: game.allies.filter(Boolean).map((h) => h!.id),
    all_opponents: game.opponents.filter(Boolean).map((h) => h!.id),
    lane_result: game.laneResult,
    damage_profile: game.damageProfile,
    enemy_items_spotted:
      game.enemyItemsSpotted.length > 0
        ? game.enemyItemsSpotted
        : undefined,
    purchased_items:
      excludedItemIds.length > 0 ? excludedItemIds : undefined,
    enemy_context:
      game.enemyContext.length > 0 ? game.enemyContext : undefined,
  };
}

export function useRecommendation() {
  const data = useRecommendationStore((s) => s.data);
  const isLoading = useRecommendationStore((s) => s.isLoading);
  const isPartial = useRecommendationStore((s) => s.isPartial);
  const error = useRecommendationStore((s) => s.error);
  const selectedItemId = useRecommendationStore((s) => s.selectedItemId);
  const selectItem = useRecommendationStore((s) => s.selectItem);
  const clear = useRecommendationStore((s) => s.clear);

  /** Standard single-pass recommendation (manual button click). */
  const recommend = async () => {
    const request = buildRequest();
    if (!request) return;

    const store = useRecommendationStore.getState();
    store.clearResults();
    store.setLoading(true);

    try {
      const response = await api.recommend(request);
      store.setData(response);
    } catch (err) {
      store.setError(
        err instanceof Error ? err.message : "Failed to get recommendations",
      );
    }
  };

  /**
   * Two-pass recommendation for auto-trigger scenarios.
   * 1. Fire fast-mode request -> show partial results immediately
   * 2. Fire full auto/deep request -> merge over partial results
   */
  const recommendTwoPass = async () => {
    const request = buildRequest();
    if (!request) return;

    const store = useRecommendationStore.getState();
    // Don't interrupt an in-progress recommendation
    if (store.isLoading) return;

    store.clearResults();
    store.setLoading(true);

    // Pass 1: Fast mode (rules-only, <1s)
    const fastRequest = { ...request, mode: "fast" as const };
    try {
      const fastResponse = await api.recommend(fastRequest);
      // Show partial results immediately
      useRecommendationStore.getState().setPartialData(fastResponse);
    } catch {
      // Fast mode failed -- continue to full request anyway
    }

    // Pass 2: Full recommendation (auto mode, 2-15s)
    try {
      const fullResponse = await api.recommend(request);
      useRecommendationStore.getState().mergeData(fullResponse);
    } catch (err) {
      // If we already have partial data, keep it and clear loading
      const current = useRecommendationStore.getState();
      if (current.data && current.isPartial) {
        // Keep partial data but clear the partial flag
        useRecommendationStore.getState().mergeData(current.data);
      } else {
        useRecommendationStore.getState().setError(
          err instanceof Error ? err.message : "Failed to get recommendations",
        );
      }
    }
  };

  return {
    recommend,
    recommendTwoPass,
    data,
    isLoading,
    isPartial,
    error,
    selectedItemId,
    selectItem,
    clear,
  };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd prismlab/frontend && npx tsc --noEmit
```
Expected: No errors related to useRecommendation.

- [ ] **Step 3: Commit**

```bash
git add prismlab/frontend/src/hooks/useRecommendation.ts
git commit -m "feat: add two-pass recommendation (fast then full) for auto-trigger"
```

---

### Task 4: Auto-Trigger Recommendation on Hero+Role Detection

Wire up `useLiveDraft` to automatically fire `recommendTwoPass()` when hero and role are both set from live match data.

**Files:**
- Modify: `prismlab/frontend/src/hooks/useLiveDraft.ts`

- [ ] **Step 1: Add auto-trigger and faster polling**

Replace the entire contents of `prismlab/frontend/src/hooks/useLiveDraft.ts`:

```typescript
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
```

- [ ] **Step 2: Update useLiveDraft call site in App.tsx**

Both hooks are called in `prismlab/frontend/src/App.tsx` (not Sidebar.tsx). Update the call:

```typescript
import { useRecommendation } from "./hooks/useRecommendation";

function App() {
  const { heroes } = useHeroes();
  const { recommendTwoPass } = useRecommendation();
  useGameIntelligence(heroes);
  useLiveDraft(heroes, recommendTwoPass);
  // ... rest unchanged
```

Add the `useRecommendation` import at the top of App.tsx.

- [ ] **Step 3: Verify TypeScript compiles**

Run:
```bash
cd prismlab/frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add prismlab/frontend/src/hooks/useLiveDraft.ts prismlab/frontend/src/App.tsx
git commit -m "feat: 3s draft polling + auto-trigger two-pass recommend on hero+role detection"
```

---

### Task 5: GSI Hero Change Triggers Immediate Draft Fetch

When GSI detects a hero_id change (user just picked their hero in-game), immediately trigger a draft fetch instead of waiting for the next 3s poll.

**Files:**
- Modify: `prismlab/frontend/src/hooks/useGameIntelligence.ts`

- [ ] **Step 1: Add fetchDraft callback parameter to useGameIntelligence**

Update the function signature in `prismlab/frontend/src/hooks/useGameIntelligence.ts`:

```typescript
export function useGameIntelligence(
  heroes: Hero[],
  fetchDraft?: () => void,
): void {
```

- [ ] **Step 2: Store fetchDraft in a ref and call it on hero_id change**

Add a ref at the top of the function body (after existing refs):

```typescript
const fetchDraftRef = useRef(fetchDraft);
```

Add a useEffect to keep the ref in sync (after the existing heroesRef sync):

```typescript
useEffect(() => {
  fetchDraftRef.current = fetchDraft;
}, [fetchDraft]);
```

Then in the hero auto-detection section (line ~375, inside `if (live.hero_id > 0 && live.hero_id !== prevHeroIdRef.current)`), add after `prevHeroIdRef.current = live.hero_id;`:

```typescript
// Immediately refresh draft data to pick up allies/opponents faster
if (fetchDraftRef.current) {
  fetchDraftRef.current();
}
```

- [ ] **Step 3: Update call site in App.tsx**

Where `useGameIntelligence` is called in `prismlab/frontend/src/App.tsx`, pass `fetchDraft`:

```typescript
const { fetchDraft } = useLiveDraft(heroes, recommendTwoPass);
useGameIntelligence(heroes, fetchDraft);
```

Note: `useLiveDraft` must be called before `useGameIntelligence` so `fetchDraft` is available.

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
cd prismlab/frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add prismlab/frontend/src/hooks/useGameIntelligence.ts prismlab/frontend/src/App.tsx
git commit -m "feat: GSI hero_id change triggers immediate draft fetch"
```

---

### Task 6: Partial Loading State in ItemTimeline

Show fast-mode results immediately with a loading indicator for the remaining phases that are still being fetched.

**Files:**
- Modify: `prismlab/frontend/src/components/timeline/ItemTimeline.tsx`
- Modify: `prismlab/frontend/src/components/draft/GetBuildButton.tsx`

- [ ] **Step 1: Add partial state indicator to ItemTimeline**

In `prismlab/frontend/src/components/timeline/ItemTimeline.tsx`, add an `isPartial` prop:

```typescript
interface ItemTimelineProps {
  data: RecommendResponse;
  selectedItemId: string | null;
  onSelectItem: (key: string | null) => void;
  isPartial?: boolean;
}
```

Update the function signature:

```typescript
function ItemTimeline({ data, selectedItemId, onSelectItem, isPartial = false }: ItemTimelineProps) {
```

Add a loading banner at the bottom of the timeline (before the closing `</div>`), after the existing phase cards and neutral items:

```typescript
{isPartial && (
  <div className="flex items-center gap-2 px-4 py-3 text-sm text-on-surface-variant/60 italic">
    <span className="inline-block w-3 h-3 border-2 border-secondary/50 border-t-secondary rounded-full animate-spin" />
    Analyzing full matchup for detailed recommendations...
  </div>
)}
```

- [ ] **Step 2: Pass isPartial from MainPanel**

In `prismlab/frontend/src/components/layout/MainPanel.tsx`, where `ItemTimeline` is rendered, add the `isPartial` prop:

```typescript
const isPartial = useRecommendationStore((s) => s.isPartial);
// ... in the JSX:
<ItemTimeline
  data={data}
  selectedItemId={selectedItemId}
  onSelectItem={selectItem}
  isPartial={isPartial}
/>
```

Add the import if not already present:

```typescript
import { useRecommendationStore } from "../../stores/recommendationStore";
```

- [ ] **Step 3: Update GetBuildButton label for partial state**

In `prismlab/frontend/src/components/draft/GetBuildButton.tsx`, add partial awareness:

```typescript
const isPartial = useRecommendationStore((s) => s.isPartial);
```

Update the label logic:

```typescript
const label = isLoading
  ? hasData ? "Re-Evaluating..." : "Analyzing..."
  : isPartial
    ? "Updating..."
    : hasData ? "Re-Evaluate" : "Get Item Build";
```

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
cd prismlab/frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add prismlab/frontend/src/components/timeline/ItemTimeline.tsx prismlab/frontend/src/components/layout/MainPanel.tsx prismlab/frontend/src/components/draft/GetBuildButton.tsx
git commit -m "feat: partial loading state in ItemTimeline + GetBuildButton"
```

---

### Task 7: Integration Verification

End-to-end test of the complete two-pass flow.

**Files:**
- No new files

- [ ] **Step 1: Build frontend**

```bash
cd prismlab/frontend && npm run build
```
Expected: Build succeeds with no TypeScript or bundle errors.

- [ ] **Step 2: Start backend**

```bash
cd prismlab/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Expected: Server starts, DataCache loads.

- [ ] **Step 3: Test fast-mode endpoint**

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"hero_id": 1, "role": 1, "playstyle": "Farm-first", "side": "radiant", "lane": "safe", "lane_opponents": [], "allies": [], "all_opponents": [], "mode": "fast"}'
```
Expected: Response in <1s with rules-based items and `engine_mode: "fast"`.

- [ ] **Step 4: Test two-pass flow manually (without GSI)**

1. Open frontend in browser
2. Select a hero (e.g., Anti-Mage)
3. Select role (Pos 1)
4. Click "Get Item Build"
5. Verify: Recommendations appear as before (single-pass, no regression)

- [ ] **Step 5: Verify parallel enrichment latency improvement**

Compare `latency_ms` in the response before and after the asyncio.gather() change. The enrichment phase should be faster (exact improvement depends on whether timing data requires a DB fetch).

- [ ] **Step 6: Commit any final fixes**

```bash
git add -A
git commit -m "fix: integration fixes for two-pass recommendation flow"
```

Only commit this step if fixes were needed. Skip if everything worked.

---

## Summary

| Task | What | Impact |
|------|------|--------|
| 1 | Parallel enrichment | ~2x faster enrichment on every request |
| 2 | Store: isPartial + mergeData | Foundation for two-pass UX |
| 3 | useRecommendation: recommendTwoPass | Core two-pass logic |
| 4 | useLiveDraft: 3s poll + auto-trigger | Zero-click hero detection + auto-recommend |
| 5 | useGameIntelligence: immediate draft fetch | Faster ally/opponent detection on hero pick |
| 6 | ItemTimeline: partial loading state | Progressive UX feedback |
| 7 | Integration verification | End-to-end confidence |

**Total estimated tasks:** 7 tasks, ~25 steps
**Expected outcome:** Hero pick in Dota → starting items visible in Prismlab within 3 seconds (no clicks). Full recommendation streams in 5-10s later.
