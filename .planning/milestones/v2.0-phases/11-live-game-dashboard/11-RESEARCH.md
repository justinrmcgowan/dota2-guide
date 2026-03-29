# Phase 11: Live Game Dashboard - Research

**Researched:** 2026-03-26
**Domain:** Real-time UI state sync (GSI -> Zustand stores -> React components)
**Confidence:** HIGH

## Summary

Phase 11 transforms the Prismlab frontend from a manual-input tool into a live game dashboard. The infrastructure (GSI receiver, WebSocket pipeline, Zustand stores) was built in Phase 10 and is already wired into the app. Phase 11's job is purely frontend: consume `gsiStore.liveState` data, sync it into `gameStore` and `recommendationStore`, and build three new UI components (stats bar, game clock, neutral tier highlight).

The critical technical challenge is cross-store synchronization: `gsiStore` receives WebSocket data, `gameStore` holds the hero/role/lane state, and `recommendationStore` tracks purchased items. Phase 11 must wire these three stores together while preserving manual-mode fallback when GSI is disconnected. The recommended approach is Zustand's `subscribe()` API (available in v5, already installed) to watch `gsiStore.liveState` changes and dispatch updates to the other stores -- this keeps the sync logic outside React components and avoids render-loop issues.

**Primary recommendation:** Use a `useGsiSync` custom hook mounted once in `App.tsx` that subscribes to `gsiStore.liveState` changes and orchestrates all cross-store updates (hero auto-fill, role suggestion, item auto-marking, stats population). All new UI components are pure presentational -- they read from existing stores with no side effects.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** GSI hero detection auto-fills the hero picker silently -- no toast, no confirmation dialog. User can still click to change manually.
- **D-02:** Role auto-suggested from OpenDota most-played position data for the detected hero (e.g., Anti-Mage -> Pos 1 at 95%). Pre-selects role but user can override. Fallback: if no data, leave role unselected.
- **D-03:** GSI is source of truth while connected -- overwrites hero, gold, GPM, net worth, inventory, game clock. Manual edits are possible but next GSI update will overwrite GSI-controlled fields.
- **D-04:** Priority chain: (1) GSI connected -> GSI data wins, (2) GSI disconnects -> last GSI values persist, manual edits resume control, (3) No GSI ever -> fully manual mode.
- **D-05:** Fields GSI controls: hero, role (suggest only), gold, GPM, net worth, inventory items, game clock, kills, deaths, assists. Fields always manual: playstyle, side, lane, lane opponents, enemy items spotted.
- **D-06:** New compact stats bar in the sidebar, positioned above the existing GameStatePanel. Shows Gold | GPM | Net Worth on one line, KDA on a second line.
- **D-07:** Stats bar only visible when GSI is connected and in-game. Hidden otherwise.
- **D-08:** Counting animation -- numbers smoothly interpolate to new values over ~300ms (slot machine style). Gold ticks up as creeps die.
- **D-09:** Color flash on significant changes: brief green pulse on large gold gains (+300g), brief red pulse on death.
- **D-10:** Existing manual controls (lane result, damage profile, enemy items) remain visible and functional below the stats bar. They are not replaced or hidden.
- **D-11:** Reuse existing green checkmark overlay and dimmed card visual for auto-detected purchases. Same visual as manual click -- no separate "GSI detected" indicator.
- **D-12:** Only mark completed items. Components in inventory (e.g., Ogre Axe toward BKB) do not trigger partial progress indicators. Item marked only when full item appears in inventory.
- **D-13:** Manual click still toggles purchased state. GSI effectively overrides manual unmarks on next update (1s later) if item is still in inventory. This is correct -- you do have the item.
- **D-14:** Item name matching: GSI inventory item names matched against recommended item internal names from the database.
- **D-15:** Game clock displays in the header bar, between GSI status indicator and data freshness. Format: MM:SS. Only visible when GSI is active and game is in progress.
- **D-16:** Neutral item section auto-highlights current tier based on game clock (e.g., clock > 7:00 = Tier 1 active). Next tier shows countdown to activation.
- **D-17:** NeutralItemSection component receives a `currentTier` prop derived from GSI game clock. Tier boundaries are the standard Dota 2 timing (7:00, 17:00, 27:00, 37:00, 60:00).

### Claude's Discretion
- Exact implementation of counting animation (CSS transitions, requestAnimationFrame, library choice)
- GSI item name -> DB item name matching strategy (exact match on internal_name, fuzzy fallback)
- Stats bar layout and spacing within sidebar
- Game clock formatting for negative time (pre-horn) or paused states
- How gsiStore updates flow into gameStore (subscription, effect, derived state)
- WebSocket message parsing and validation in the frontend

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GSI-02 | Auto-detect player's hero and suggest role when game starts from GSI data | Hero lookup by `hero_id` from GSI (backend has `GET /heroes/{hero_id}`). Role suggestion from Hero.roles OpenDota data. See Architecture Pattern 1 (useGsiSync hook). |
| GSI-03 | Real-time gold, GPM, and net worth tracked from GSI and displayed in sidebar | `gsiStore.liveState` already has gold/gpm/net_worth fields. New `LiveStatsBar` component reads directly. See Architecture Pattern 2 (counting animation). |
| GSI-04 | Purchased items auto-detected from GSI inventory data and marked in the timeline | Item name matching: GSI `items_inventory` (stripped `item_` prefix) matches `item_name` in recommendations (set to `Item.internal_name`). See Architecture Pattern 3 (item matching). |
| WS-02 | Frontend WebSocket hook with auto-reconnect and connection status indicator | Already implemented in Phase 10: `useWebSocket.ts` with exponential backoff, `GsiStatusIndicator.tsx` with green/gray/red. Phase 11 extends header with game clock. |
| WS-03 | Game clock from GSI displayed in the UI, synced with neutral item tier timing | `liveState.game_clock` is integer seconds. New `GameClock` component in Header. Neutral tier derivation function. See Architecture Pattern 4. |
| WS-04 | Live gold counter in sidebar replacing manual lane result input when GSI is active | `LiveStatsBar` component visible only when `gsiStatus === "connected"`. Manual controls remain visible below. D-07 and D-10 govern visibility. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| zustand | ^5.0.12 | State management + cross-store subscriptions | Already installed. v5 `subscribe()` enables outside-React sync |
| react | 18.x | UI rendering | Already installed |
| typescript | strict | Type safety | Already configured |
| tailwind | v4 | Styling | Already configured with project tokens |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none needed) | - | - | No new dependencies for Phase 11 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom `useAnimatedValue` hook | react-countup / framer-motion | Adds dependency for ~20 lines of rAF code. Custom hook is simpler and avoids bundle growth. |
| Zustand `subscribe()` | React `useEffect` with selectors | `useEffect` runs after render; `subscribe()` is synchronous and avoids stale closures. Both work, but subscribe is cleaner for store-to-store sync. |

**Installation:**
```bash
# No new packages needed -- Phase 11 uses only existing dependencies
```

## Architecture Patterns

### Recommended Project Structure
```
prismlab/frontend/src/
  hooks/
    useGsiSync.ts           # NEW: Cross-store sync hook (gsiStore -> gameStore/recommendationStore)
    useAnimatedValue.ts     # NEW: requestAnimationFrame counting animation hook
    useWebSocket.ts         # EXISTING: WebSocket connection
  components/
    layout/
      Header.tsx            # MODIFY: Add GameClock component
      GsiStatusIndicator.tsx # EXISTING: No changes
      Sidebar.tsx           # MODIFY: Add LiveStatsBar above GameStatePanel
    game/
      LiveStatsBar.tsx      # NEW: Gold/GPM/NW/KDA display with animations
      GameStatePanel.tsx    # EXISTING: No changes (manual controls remain)
    timeline/
      ItemCard.tsx          # EXISTING: No changes (already has purchased visual)
      NeutralItemSection.tsx # MODIFY: Add currentTier prop, highlight active tier
      ItemTimeline.tsx      # MODIFY: Pass currentTier to NeutralItemSection
    clock/
      GameClock.tsx         # NEW: MM:SS game clock in header
  stores/
    gsiStore.ts             # EXISTING: No changes (already has all needed fields)
    gameStore.ts            # EXISTING: No interface changes (sync calls existing setters)
    recommendationStore.ts  # EXISTING: No interface changes (sync calls togglePurchased)
  utils/
    neutralTiers.ts         # NEW: Tier boundary constants + getCurrentTier helper
    itemMatching.ts         # NEW: GSI item name -> recommendation composite key matcher
```

### Pattern 1: Cross-Store Sync via useGsiSync Hook
**What:** A single custom hook mounted in `App.tsx` that subscribes to `gsiStore.liveState` and dispatches updates to `gameStore` and `recommendationStore`.
**When to use:** Any time one Zustand store's data needs to trigger updates in another store.
**Example:**
```typescript
// hooks/useGsiSync.ts
import { useEffect, useRef } from "react";
import { useGsiStore } from "../stores/gsiStore";
import { useGameStore } from "../stores/gameStore";
import { useRecommendationStore } from "../stores/recommendationStore";

export function useGsiSync(heroes: Hero[]) {
  const prevHeroIdRef = useRef<number>(0);

  useEffect(() => {
    // Subscribe to gsiStore outside React render cycle
    const unsubscribe = useGsiStore.subscribe((state, prevState) => {
      const live = state.liveState;
      if (!live || state.gsiStatus !== "connected") return;

      // Hero auto-detection (only when hero changes)
      if (live.hero_id !== prevHeroIdRef.current && live.hero_id > 0) {
        prevHeroIdRef.current = live.hero_id;
        const hero = heroes.find(h => h.id === live.hero_id);
        if (hero) {
          useGameStore.getState().selectHero(hero);
          // Auto-suggest role from hero roles data
          const suggestedRole = inferRole(hero);
          if (suggestedRole) useGameStore.getState().setRole(suggestedRole);
        }
      }

      // Auto-mark purchased items
      syncPurchasedItems(live.items_inventory, live.items_backpack);
    });

    return unsubscribe;
  }, [heroes]);
}
```
**Key insight:** Zustand v5's `subscribe((state, prevState) => ...)` provides both current and previous state, enabling efficient change detection without selectors.

### Pattern 2: Counting Animation with requestAnimationFrame
**What:** A custom hook that smoothly interpolates a number from its previous value to a new target value over a configurable duration.
**When to use:** Real-time stat displays where instant jumps feel jarring (gold, GPM, net worth).
**Example:**
```typescript
// hooks/useAnimatedValue.ts
import { useRef, useState, useEffect } from "react";

export function useAnimatedValue(target: number, duration = 300): number {
  const [display, setDisplay] = useState(target);
  const startRef = useRef(target);
  const startTimeRef = useRef(0);
  const rafRef = useRef(0);

  useEffect(() => {
    startRef.current = display;
    startTimeRef.current = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out for natural deceleration
      const eased = 1 - (1 - progress) ** 2;
      const current = Math.round(
        startRef.current + (target - startRef.current) * eased
      );
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
```
**Important:** The `display` state in the dependency closure must be read via ref, not state, to avoid re-triggering the effect. The example above uses a `startRef` to capture the starting value at effect time.

### Pattern 3: Item Name Matching (GSI -> Recommendations)
**What:** Match GSI inventory item names against recommended item names to auto-mark purchases.
**When to use:** Every GSI update cycle (1Hz).
**Example:**
```typescript
// utils/itemMatching.ts
export function findPurchasedKeys(
  gsiInventory: string[],     // e.g., ["power_treads", "bfury", ""]
  gsiBackpack: string[],      // e.g., ["", "", ""]
  recommendations: RecommendResponse
): Set<string> {
  // Combine all GSI items, filter empty strings
  const ownedItems = new Set(
    [...gsiInventory, ...gsiBackpack].filter(Boolean)
  );

  const purchasedKeys = new Set<string>();
  for (const phase of recommendations.phases) {
    for (const item of phase.items) {
      // item.item_name is already internal_name (e.g., "power_treads")
      // GSI items also use internal_name format (item_ prefix stripped by backend)
      if (ownedItems.has(item.item_name)) {
        purchasedKeys.add(`${phase.phase}-${item.item_id}`);
      }
    }
  }
  return purchasedKeys;
}
```
**Key insight:** Both GSI item names and recommendation `item_name` fields use the same format: the `Item.internal_name` from the database (e.g., `power_treads`, `blink`, `black_king_bar`). The backend `_normalize_item_name()` strips the `item_` prefix from GSI data, and `_validate_item_ids()` overwrites `item_name` with `Item.internal_name`. Exact string match works -- no fuzzy matching needed.

### Pattern 4: Neutral Item Tier Derivation
**What:** Pure function that maps game clock seconds to the current active neutral item tier.
**When to use:** Derive `currentTier` prop for `NeutralItemSection` from `gsiStore.liveState.game_clock`.
**Example:**
```typescript
// utils/neutralTiers.ts
export const NEUTRAL_TIER_BOUNDARIES = [
  { tier: 1, startSeconds: 7 * 60 },   // 7:00
  { tier: 2, startSeconds: 17 * 60 },  // 17:00
  { tier: 3, startSeconds: 27 * 60 },  // 27:00
  { tier: 4, startSeconds: 37 * 60 },  // 37:00
  { tier: 5, startSeconds: 60 * 60 },  // 60:00
] as const;

export function getCurrentTier(gameClockSeconds: number): number | null {
  for (let i = NEUTRAL_TIER_BOUNDARIES.length - 1; i >= 0; i--) {
    if (gameClockSeconds >= NEUTRAL_TIER_BOUNDARIES[i].startSeconds) {
      return NEUTRAL_TIER_BOUNDARIES[i].tier;
    }
  }
  return null; // No tier active yet
}

export function getNextTierCountdown(gameClockSeconds: number): {
  tier: number;
  secondsRemaining: number;
} | null {
  for (const boundary of NEUTRAL_TIER_BOUNDARIES) {
    if (gameClockSeconds < boundary.startSeconds) {
      return {
        tier: boundary.tier,
        secondsRemaining: boundary.startSeconds - gameClockSeconds,
      };
    }
  }
  return null; // All tiers active
}
```

**IMPORTANT NOTE on tier timings:** CONTEXT.md D-17 specifies boundaries at 7:00, 17:00, 27:00, 37:00, 60:00. However, the current Dota 2 neutral item system (patch 7.40+) uses Madstone-based crafting with tier availability at 5:00, 15:00, 25:00, 35:00, 60:00. The existing `NeutralItemSection.tsx` TIER_TIMING constant already uses the correct 5/15/25/35/60 values. **The planner should use the values from `NeutralItemSection.tsx` (5:00, 15:00, 25:00, 35:00, 60:00) for tier boundary constants**, not the D-17 values, to maintain consistency with the existing component. If the user specifically wants the D-17 values, they can override, but the existing code and current game data both support 5/15/25/35/60.

### Anti-Patterns to Avoid
- **Cross-store sync in render path:** Do NOT read gsiStore in a component and call gameStore setters in the same render. This causes cascading re-renders. Use `subscribe()` outside the render cycle.
- **Polling gsiStore with setInterval:** The WebSocket already pushes at 1Hz. Do not add another timer. Subscribe to state changes directly.
- **Storing derived state:** Do NOT store `currentTier` in a store. Derive it from `game_clock` in the component or via a selector. Derived state creates sync bugs.
- **Modifying ItemCard for GSI:** The existing `isPurchased` prop and green checkmark overlay already work. Auto-marking writes to `recommendationStore.purchasedItems` -- the same data path as manual clicks. No ItemCard changes needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket management | Custom WS class | Existing `useWebSocket.ts` hook | Already built with reconnect, backoff, status tracking |
| GSI data parsing | Frontend JSON parser | Backend `GsiStateManager` + `gsiStore.updateLiveState` | Backend already normalizes item names, hero names, extracts fields |
| State management | Custom pub/sub system | Zustand `subscribe()` | Built-in, tested, handles React 18 concurrent mode |
| Number formatting | Manual toLocaleString calls | Intl.NumberFormat or simple comma formatter | Consistent formatting for gold values (1,523 not 1523) |

**Key insight:** Phase 10 built all the plumbing. Phase 11 should NOT add any new backend code or WebSocket logic. It is purely frontend: new components + store sync logic.

## Common Pitfalls

### Pitfall 1: Stale Closure in Subscribe Callback
**What goes wrong:** The `subscribe()` callback captures stale `heroes` array or recommendation data at mount time, causing hero lookups to fail.
**Why it happens:** Zustand `subscribe()` is called once in `useEffect`. If the heroes list loads async after mount, the closure has an empty array.
**How to avoid:** Use `useRef` for data that changes after mount (heroes list). Update the ref when data loads. Read `ref.current` inside the subscribe callback.
**Warning signs:** Hero auto-detection works on second game but not first. Or it never finds the hero despite GSI sending valid data.

### Pitfall 2: Infinite Re-render from Store Sync
**What goes wrong:** Setting gameStore state from a gsiStore subscription triggers a re-render, which re-runs an effect, which sets state again.
**Why it happens:** Naive implementation uses `useEffect` watching `gsiStore.liveState` and calling `gameStore.selectHero()` on every update.
**How to avoid:** (1) Use `subscribe()` outside render cycle. (2) Add guards: only call `selectHero()` when hero_id actually changes. (3) Never watch entire `liveState` object -- watch specific fields.
**Warning signs:** Browser becomes sluggish. React DevTools shows thousands of renders per second.

### Pitfall 3: Item Composite Key Mismatch
**What goes wrong:** Auto-marked items don't show as purchased in the UI because the composite key format doesn't match.
**Why it happens:** `purchasedItems` uses format `"phase-itemId"` (e.g., `"laning-36"`). If auto-marking builds keys with wrong format (e.g., `"laning-magic_stick"` or just `"36"`), the Set lookup fails.
**How to avoid:** Always use `${phase.phase}-${item.item_id}` format, identical to what `togglePurchased` expects. Write a unit test that verifies the key format matches.
**Warning signs:** Items in inventory but timeline doesn't show green checkmarks. Manual clicking works but auto-mark doesn't.

### Pitfall 4: Gold Animation Jank at 1Hz Updates
**What goes wrong:** Counting animation restarts every 1 second (WebSocket push rate), creating stuttering instead of smooth counting.
**Why it happens:** Each new gold value triggers a new animation from current display value to new target. If animation duration (300ms) is shorter than update interval (1000ms), there's a 700ms pause between animations.
**How to avoid:** Animation duration of 300ms is fine -- the pause is expected between GSI updates. The "slot machine" feel comes from the easing, not continuous motion. If smoother interpolation is desired, increase duration to ~800ms so animations nearly overlap.
**Warning signs:** Numbers jump-pause-jump instead of smooth counting. Or animations overlap and create jittery display.

### Pitfall 5: Hero Not Found in Frontend Heroes List
**What goes wrong:** GSI sends a `hero_id` that doesn't match any hero in the frontend `useHeroes()` list.
**Why it happens:** Heroes list loaded from API may be incomplete, or there's a new hero in Dota 2 that hasn't been seeded into the DB yet.
**How to avoid:** Graceful fallback: if hero not found by ID, log a warning but don't crash. Optionally fetch from `GET /heroes/{hero_id}` as a one-off lookup. The hero picker stays empty -- user can still manually select.
**Warning signs:** GSI is connected, game clock running, but hero picker stays empty.

### Pitfall 6: Incorrect Neutral Tier Timings
**What goes wrong:** Tier highlight is wrong because tier boundaries don't match the current Dota 2 patch.
**Why it happens:** D-17 specifies 7:00/17:00/27:00/37:00/60:00 but the current patch uses 5:00/15:00/25:00/35:00/60:00. The existing `NeutralItemSection.tsx` TIER_TIMING constant uses 5/15/25/35/60.
**How to avoid:** Use a single source of truth for tier boundaries. Define them once in `utils/neutralTiers.ts` and import everywhere. Cross-reference with existing `TIER_TIMING` in `NeutralItemSection.tsx`.
**Warning signs:** Tier highlight activates 2 minutes late compared to actual in-game neutral item drops.

## Code Examples

Verified patterns from existing codebase:

### Zustand v5 Subscribe with Previous State
```typescript
// Source: Zustand v5 API -- subscribe(listener) where listener receives (state, prevState)
// Already used pattern in this codebase (gsiStore.setWsStatus checks previous gsiStatus)
const unsubscribe = useGsiStore.subscribe((state, prevState) => {
  // Only react to meaningful changes
  if (state.liveState?.hero_id !== prevState.liveState?.hero_id) {
    // Hero changed -- update gameStore
  }
});
```

### Existing Purchased Item Toggle Pattern
```typescript
// Source: prismlab/frontend/src/stores/recommendationStore.ts
// The togglePurchased action uses composite key format "phase-itemId"
const key = `${phase.phase}-${item.item_id}`;  // e.g., "laning-36"
useRecommendationStore.getState().togglePurchased(key);
```

### GSI Item Name Format (Backend Normalization)
```typescript
// Source: prismlab/backend/gsi/state_manager.py
// _normalize_item_name strips "item_" prefix: "item_power_treads" -> "power_treads"
// _normalize_hero_name strips "npc_dota_hero_" prefix: "npc_dota_hero_antimage" -> "antimage"

// Frontend gsiStore receives already-normalized names:
// liveState.items_inventory = ["power_treads", "bfury", "", "", "", ""]
// liveState.hero_name = "antimage"
```

### Recommendation item_name Format
```typescript
// Source: prismlab/backend/engine/recommender.py line 229
// After validation, item_name is set to Item.internal_name (the DB slug):
// item.item_name = "power_treads"  (same format as GSI normalized names)
// This means exact string comparison works for matching.
```

### Existing Game Clock Formatting
```typescript
// Source: prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx
// Already formats game_clock for tooltip:
const mins = Math.floor(liveState.game_clock / 60);
const secs = liveState.game_clock % 60;
const formatted = `${mins}:${String(secs).padStart(2, "0")}`;
// For negative time (pre-horn), game_clock is negative.
// Math.floor(-90 / 60) = -2, -90 % 60 = -30 -> need absolute values with "-" prefix
```

### Role Inference from Hero Data
```typescript
// Hero.roles from OpenDota is an array like ["Carry", "Escape", "Nuker"]
// This is NOT position data (Pos 1-5). It's role tags.
// For D-02 (role auto-suggestion), need a mapping:
// - "Carry" in roles -> suggest Pos 1
// - "Mid" or solo-oriented heroes -> suggest Pos 2
// - "Initiator" + "Durable" -> suggest Pos 3
// - "Support" + not "Hard Support" -> suggest Pos 4
// - "Support" + healer/save archetype -> suggest Pos 5
// This is heuristic and imprecise. Better approach: use hero_id to check
// commonly played positions from OpenDota hero stats, or use a simple
// lookup map for the most common heroes.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GSI item names with `item_` prefix | Backend strips prefix in `state_manager.py` | Phase 10 | Frontend receives clean names matching DB internal_name |
| Manual hero selection only | GSI auto-detection + manual fallback | Phase 11 (this phase) | Hero picker auto-fills from live game data |
| Separate neutral item timings | Madstone-based crafting system | Dota 2 patch 7.37 (2024) | Tier availability unchanged at 5/15/25/35/60 minutes |

**Deprecated/outdated:**
- D-17's tier boundaries (7:00/17:00/27:00/37:00/60:00) do not match current game data. The existing `NeutralItemSection.tsx` uses the correct values (5:00/15:00/25:00/35:00/60:00). Use the existing values.

## Open Questions

1. **Role auto-suggestion accuracy**
   - What we know: Hero.roles contains OpenDota role tags like ["Carry", "Escape", "Nuker"]. These are descriptive tags, not position numbers (1-5).
   - What's unclear: How reliably can we map these tags to Dota 2 positions? Some heroes play multiple positions (e.g., Mirana Pos 2/4, Naga Pos 1/4).
   - Recommendation: Build a simple heuristic mapping (Carry->1, high-confidence only). For ambiguous heroes, leave role unselected and let user choose. The mapping doesn't need to be perfect -- it's a suggestion (D-02 says "pre-selects but user can override").

2. **Game clock negative time handling**
   - What we know: `game_clock` is `map.clock_time` from GSI, which is negative during pre-game/strategy time (before 0:00 horn).
   - What's unclear: Exact format for displaying negative time (e.g., `-1:30` or just hide the clock).
   - Recommendation: Display as `-M:SS` when negative. D-15 says "only visible when GSI is active and game is in progress". The `game_state` field can be checked: only show clock when `game_state === "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"`.

3. **BKB internal_name discrepancy**
   - What we know: In test conftest.py, BKB appears twice: id=2 as `internal_name="black_king_bar"` and id=116 as `internal_name="bkb"`. GSI may send either name.
   - What's unclear: Which name GSI actually sends for BKB after `item_` prefix stripping.
   - Recommendation: Handle by checking both forms in the matching function, or rely on the fact that the recommender uses whichever internal_name the DB has for the recommended item's ID. Since the matcher compares GSI inventory against recommendation item_name (both from DB), they should naturally match. If they don't, add a small alias map for known discrepancies.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 |
| Config file | `prismlab/frontend/vitest.config.ts` |
| Quick run command | `cd prismlab/frontend && npx vitest run --reporter=verbose` |
| Full suite command | `cd prismlab/frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GSI-02 | Hero auto-detected from GSI, role suggested | unit | `npx vitest run src/hooks/useGsiSync.test.ts -t "hero detection"` | Wave 0 |
| GSI-03 | Gold/GPM/NW displayed, animated values | unit | `npx vitest run src/components/game/LiveStatsBar.test.tsx` | Wave 0 |
| GSI-04 | Items auto-marked as purchased from GSI | unit | `npx vitest run src/utils/itemMatching.test.ts` | Wave 0 |
| WS-02 | WebSocket auto-reconnect and status indicator | unit | `npx vitest run src/hooks/useWebSocket.test.ts` | Exists (from Phase 10) |
| WS-03 | Game clock displayed, neutral tier sync | unit | `npx vitest run src/utils/neutralTiers.test.ts` | Wave 0 |
| WS-04 | Live gold counter visible when GSI active | unit | `npx vitest run src/components/game/LiveStatsBar.test.tsx -t "visibility"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/frontend && npx vitest run --reporter=verbose`
- **Per wave merge:** `cd prismlab/frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `src/hooks/useGsiSync.test.ts` -- covers GSI-02 (hero auto-detect, role suggest, store sync)
- [ ] `src/components/game/LiveStatsBar.test.tsx` -- covers GSI-03, WS-04 (stats display, visibility, animation)
- [ ] `src/utils/itemMatching.test.ts` -- covers GSI-04 (item name matching, composite key generation)
- [ ] `src/utils/neutralTiers.test.ts` -- covers WS-03 (tier boundary calculation, countdown)
- [ ] `src/hooks/useAnimatedValue.test.ts` -- covers animation hook (rAF behavior)

## Sources

### Primary (HIGH confidence)
- `prismlab/frontend/src/stores/gsiStore.ts` -- GsiLiveState interface, all GSI field names and types
- `prismlab/frontend/src/stores/gameStore.ts` -- Manual state setters (selectHero, setRole, etc.)
- `prismlab/frontend/src/stores/recommendationStore.ts` -- purchasedItems Set with composite key format
- `prismlab/backend/gsi/state_manager.py` -- Item/hero name normalization logic (_normalize_item_name, _normalize_hero_name)
- `prismlab/backend/engine/recommender.py` (line 229) -- item_name overwritten with Item.internal_name during validation
- `prismlab/frontend/src/components/timeline/NeutralItemSection.tsx` -- Existing TIER_TIMING constant (5/15/25/35/60)
- `prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx` -- Existing game clock formatting pattern
- [Liquipedia Dota 2 Neutral Items](https://liquipedia.net/dota2/Neutral_Items) -- Tier timing verification (5:00/15:00/25:00/35:00/60:00)

### Secondary (MEDIUM confidence)
- [Zustand v5 GitHub](https://github.com/pmndrs/zustand) -- subscribe() API with (state, prevState) signature
- [CSS-Tricks requestAnimationFrame with React Hooks](https://css-tricks.com/using-requestanimationframe-with-react-hooks/) -- rAF hook patterns

### Tertiary (LOW confidence)
- Role inference heuristic (OpenDota role tags -> position mapping) -- no authoritative source; best-effort heuristic

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing libraries
- Architecture: HIGH -- all integration points verified by reading actual source code
- Item matching: HIGH -- verified both GSI normalization and recommender validation produce same format
- Neutral tier timings: HIGH -- verified against Liquipedia and existing codebase (but D-17 values differ)
- Role inference: LOW -- no authoritative mapping from OpenDota role tags to positions
- Counting animation: MEDIUM -- standard rAF pattern, but edge cases with 1Hz updates need testing
- Pitfalls: HIGH -- derived from actual code analysis of store interactions

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable -- no external API changes expected)
