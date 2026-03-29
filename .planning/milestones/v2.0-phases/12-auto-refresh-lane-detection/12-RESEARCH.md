# Phase 12: Auto-Refresh & Lane Detection - Research

**Researched:** 2026-03-26
**Domain:** Frontend event detection, GSI data extension, rate-limited auto-refresh, toast notifications
**Confidence:** MEDIUM-HIGH

## Summary

Phase 12 adds automatic recommendation refreshing and lane result auto-detection. The core challenge is detecting game events (deaths, gold swings, tower kills, Roshan kills, game phase transitions) from GSI data arriving at 1Hz via WebSocket, rate-limiting auto-refresh calls to max once per 2 minutes, and providing toast notifications explaining each trigger. Lane result auto-detection compares GPM vs role benchmarks at the 10-minute mark.

The implementation is entirely frontend-driven. The existing `useGsiSync` hook establishes the pattern: subscribe to `gsiStore` outside the render cycle, compare current state to previous state via refs, and call into other stores when events are detected. A new `useAutoRefresh` hook follows this same pattern. The backend `/api/recommend` endpoint requires no changes -- auto-refresh simply calls the same `recommend()` function that the manual Re-Evaluate button uses.

**Primary recommendation:** Create a new `useAutoRefresh` hook that subscribes to gsiStore, maintains previous-state refs for diff detection, manages a cooldown timer, and calls the existing `recommend()` function. Extend the GSI pipeline to forward `roshan_state` from the existing map data. For tower detection, add `"buildings" "1"` to the GSI config and parse building health, with a fallback approach if buildings data is unavailable in player mode. Build a custom toast component (no library) since the requirement is narrow and specific.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Five trigger types: player death, major gold swing (>2000g net worth delta), tower kill (any team), Roshan kill, and game phase transitions (10 min, 20 min, 35 min).
- **D-02:** Item purchases do NOT trigger auto-refresh -- buying an item doesn't change what you should buy next (the recommendation already knew what was coming).
- **D-03:** Tower kills detected for either team (enemy or allied) -- both have itemization implications (defensive urgency vs aggressive opportunity).
- **D-04:** Gold swing threshold fixed at 2000g (not configurable). Computed as |current_net_worth - net_worth_at_last_refresh|. Baseline resets after each refresh.
- **D-05:** Game phase transition thresholds: 10:00 (laning ends, lane result determined), 20:00 (mid-game shift), 35:00 (late-game priorities). Each fires once per game.
- **D-06:** Event detection runs on each GSI update (1Hz from WebSocket). Compares current state to previous state to detect diffs (deaths++, new tower count, net_worth delta, clock crossing thresholds).
- **D-07:** Max one auto-refresh per 2 minutes (120 seconds). Cooldown starts when a refresh fires (auto or manual).
- **D-08:** Events during cooldown: queue the most recent trigger only. When cooldown expires, auto-fire with that event's context. Multiple events during cooldown -- last one replaces previous (most recent context is most relevant).
- **D-09:** Manual Re-Evaluate button always bypasses cooldown and fires immediately. Manual click also resets the 2-minute cooldown timer (prevents auto-refresh immediately after manual).
- **D-10:** Subtle cooldown timer displayed below the Re-Evaluate button: dim text showing "auto in 1:23" countdown. Only visible when auto-refresh is cooling down and an event is queued.
- **D-11:** Role-based static GPM benchmarks at 10:00 game time. Pos 1: ~500, Pos 2: ~480, Pos 3: ~400, Pos 4: ~280, Pos 5: ~230. Won = GPM > benchmark x 1.10, Even = within +/-10%, Lost = GPM < benchmark x 0.90.
- **D-12:** At 10:00 game clock, lane result auto-sets in `gameStore.laneResult` based on current GPM vs role benchmark. The LaneResultSelector visually updates with a subtle "auto-detected" indicator.
- **D-13:** User can click any lane result button to override the auto-detected value at any time. Override persists (GSI does not re-detect after override).
- **D-14:** Lane result auto-detection triggers a re-evaluation as part of the 10:00 game phase transition event.
- **D-15:** Bottom-right toast with lightning bolt icon, "Recommendations updated" header, and trigger reason text. Auto-dismiss after 4 seconds.
- **D-16:** Trigger-specific messages: "Death -- reassessing priorities", "Gold swing: +2,340g", "Tower destroyed -- map changed", "Roshan killed -- updating", "Lane phase ended (10:00)", "Mid-game reached (20:00)", "Late game reached (35:00)".
- **D-17:** When cooldown-queued event fires, toast shows only the final trigger reason (not accumulated events). Matches queue-latest-only behavior.

### Claude's Discretion
- Toast component implementation (custom or library like react-hot-toast)
- Exact animation/transition for toast appearance and dismissal
- GSI state diff detection implementation (how to compare previous vs current state)
- Tower/Roshan detection from GSI map data fields
- Cooldown timer implementation (setInterval, requestAnimationFrame, etc.)
- Edge cases: GSI disconnects during cooldown, game ends during cooldown, reconnect after pause

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GSI-05 | Lane result (won/even/lost) auto-determined from GPM vs role benchmarks at 10 minutes | GPM available from `gsiStore.liveState.gpm`, role from `gameStore.role`, benchmarks from D-11. Compare at game_clock >= 600. |
| REFRESH-01 | Recommendations auto-refresh on key game events (death, tower, Roshan, gold swing >2000g) | Item purchases EXCLUDED per D-02. Events detected via gsiStore subscription comparing prev/current state. Tower/Roshan detection requires GSI pipeline extension. |
| REFRESH-02 | Rate limiter enforces max 1 auto-refresh per 2 minutes to control API costs | Cooldown timer in useAutoRefresh hook. Manual Re-Evaluate bypasses cooldown per D-09. Queue-latest-only per D-08. |
| REFRESH-03 | Auto-refresh notification toast shows reason for update | Custom toast component with trigger-specific messages per D-16. Bottom-right positioning, 4s auto-dismiss per D-15. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Frontend: React 19 + Vite + TypeScript strict + Tailwind v4 + Zustand 5
- Backend: Python 3.12 + FastAPI + Pydantic v2
- Dark theme: spectral cyan (#00d4ff) primary, Radiant teal (#6aff97), Dire red (#ff5555)
- Desktop-first layout: left sidebar inputs, right main panel timeline
- Functional components with hooks, type hints throughout
- Hybrid engine: rules first, Claude API for reasoning. Always have fallback.
- Structured JSON output from Claude API, validated before frontend return

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.4 | UI framework | Already in project |
| Zustand | 5.0.12 | State management | Already in project, subscription API used for event detection |
| Tailwind CSS | 4.2.2 | Styling | Already in project |
| Vitest | 4.1.0 | Testing | Already in project |

### No New Dependencies Needed

Phase 12 requires **zero new npm packages**. All functionality is built with:
- Custom `useAutoRefresh` hook using Zustand `subscribe()` + `useRef` + `setInterval`
- Custom toast component using Tailwind CSS transitions
- GPM benchmark logic as pure utility function

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom toast | react-hot-toast (2.6.0) or sonner (2.0.7) | Libraries add dependency for a single toast type. Custom is ~40 lines, fully styled to match Prismlab's dark theme. No configuration overhead. |
| Custom cooldown timer | useReducer + setTimeout | setInterval with 1s tick is simpler, matches existing patterns (similar to useAnimatedValue). |

**Installation:** None required.

## Architecture Patterns

### Recommended New Files
```
prismlab/frontend/src/
  hooks/
    useAutoRefresh.ts          # Core event detection + rate limiting + auto-refresh trigger
  stores/
    refreshStore.ts            # Cooldown state, queued event, toast message queue
  components/
    toast/
      AutoRefreshToast.tsx     # Toast notification component
  utils/
    laneBenchmarks.ts          # GPM benchmarks by role, lane result calculation
    triggerDetection.ts        # Pure functions: detectDeath, detectGoldSwing, detectTower, etc.
prismlab/backend/
  gsi/
    models.py                  # Extend GsiMap with roshan_state; add GsiBuildings model
    state_manager.py           # Extend ParsedGsiState with roshan_state, tower_count fields
  api/routes/
    settings.py                # Add "buildings" "1" to GSI config template
```

### Modified Files
```
prismlab/frontend/src/
  App.tsx                      # Add useAutoRefresh() hook call, render AutoRefreshToast
  stores/gsiStore.ts           # Extend GsiLiveState with roshan_state, tower counts
  components/game/
    ReEvaluateButton.tsx       # Add cooldown timer text below button
    LaneResultSelector.tsx     # Add auto-detected indicator, override behavior
    GameStatePanel.tsx         # Pass cooldown state to ReEvaluateButton
  hooks/useRecommendation.ts   # Export recommend as standalone (not just from hook)
```

### Pattern 1: Zustand Subscription for Event Detection (ESTABLISHED)

**What:** Subscribe to gsiStore outside React render cycle, compare prev/current state via refs, trigger side effects.

**When to use:** Any time GSI data changes need to trigger actions without re-rendering.

**Example:** (from existing `useGsiSync.ts`)
```typescript
// Source: prismlab/frontend/src/hooks/useGsiSync.ts (existing pattern)
useEffect(() => {
  const unsubscribe = useGsiStore.subscribe((state) => {
    if (state.gsiStatus !== "connected") return;
    const live = state.liveState;
    if (!live) return;
    // Compare to refs, trigger actions
  });
  return unsubscribe;
}, []);
```

### Pattern 2: Event Detection via Diff (NEW)

**What:** On each GSI update, compare current state fields to stored-previous-state refs. If a threshold is crossed, fire an event.

**When to use:** Detecting deaths (deaths incremented), gold swings (net_worth delta > threshold), clock crossing phase boundaries.

**Example:**
```typescript
// Trigger detection pattern
interface TriggerEvent {
  type: "death" | "gold_swing" | "tower_kill" | "roshan_kill" | "phase_transition";
  message: string;
}

function detectTriggers(
  current: GsiLiveState,
  prev: PreviousState,
  firedPhases: Set<number>,
): TriggerEvent | null {
  // Priority order: phase transition > death > roshan > tower > gold swing

  // Phase transitions (fire once per game)
  const clock = current.game_clock;
  if (clock >= 2100 && !firedPhases.has(2100)) {
    firedPhases.add(2100);
    return { type: "phase_transition", message: "Late game reached (35:00)" };
  }
  if (clock >= 1200 && !firedPhases.has(1200)) {
    firedPhases.add(1200);
    return { type: "phase_transition", message: "Mid-game reached (20:00)" };
  }
  if (clock >= 600 && !firedPhases.has(600)) {
    firedPhases.add(600);
    return { type: "phase_transition", message: "Lane phase ended (10:00)" };
  }

  // Death
  if (current.deaths > prev.deaths) {
    return { type: "death", message: "Death -- reassessing priorities" };
  }

  // Gold swing
  const delta = current.net_worth - prev.netWorthAtLastRefresh;
  if (Math.abs(delta) >= 2000) {
    const sign = delta > 0 ? "+" : "";
    return { type: "gold_swing", message: `Gold swing: ${sign}${delta.toLocaleString()}g` };
  }

  return null;
}
```

### Pattern 3: Cooldown with Queue-Latest (NEW)

**What:** After a refresh fires, start a 120s cooldown. Events during cooldown are queued (latest replaces previous). When cooldown expires, auto-fire the queued event. Manual Re-Evaluate bypasses and resets.

**When to use:** Rate-limiting API calls while preserving reactivity.

**Example:**
```typescript
// refreshStore state shape
interface RefreshState {
  cooldownEnd: number | null;       // timestamp when cooldown expires (null = no cooldown)
  queuedEvent: TriggerEvent | null; // most recent event during cooldown
  lastToast: { message: string; timestamp: number } | null;

  startCooldown: () => void;
  queueEvent: (event: TriggerEvent) => void;
  clearQueue: () => void;
  showToast: (message: string) => void;
  dismissToast: () => void;
}
```

### Pattern 4: Custom Toast Component (NEW)

**What:** Minimal toast component rendered at app root, driven by refreshStore state. Uses Tailwind transitions for enter/exit animation.

**When to use:** Showing auto-refresh trigger notifications.

**Example:**
```typescript
// AutoRefreshToast.tsx sketch
function AutoRefreshToast() {
  const toast = useRefreshStore((s) => s.lastToast);
  const dismiss = useRefreshStore((s) => s.dismissToast);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!toast) { setVisible(false); return; }
    setVisible(true);
    const timer = setTimeout(() => { setVisible(false); dismiss(); }, 4000);
    return () => clearTimeout(timer);
  }, [toast?.timestamp]);

  if (!toast) return null;

  return (
    <div className={`fixed bottom-4 right-4 ... transition-all duration-300
      ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}>
      {/* lightning bolt icon */}
      <p className="text-sm font-semibold text-cyan-accent">Recommendations updated</p>
      <p className="text-xs text-gray-400">{toast.message}</p>
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Re-rendering on every GSI tick:** Do NOT use `useGsiStore((s) => s.liveState)` in the auto-refresh hook. Use `subscribe()` outside React's render cycle (established in useGsiSync.ts).
- **Multiple useEffect chains for event detection:** Consolidate all trigger detection into a single subscription callback. Multiple effects create race conditions and ordering issues.
- **setInterval for cooldown + separate setInterval for countdown display:** Use a single 1s interval that both checks cooldown expiry AND updates the countdown display.
- **Calling recommend() directly from the subscription:** The `recommend()` function is async and accesses gameStore. Call it via a ref or from a React context to avoid stale closures.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Custom token bucket / leaky bucket | Simple timestamp comparison (`Date.now() > cooldownEnd`) | The rate limit is a fixed 120s window, not a throughput limiter. Timestamp comparison is trivial. |
| Toast animations | Custom CSS @keyframes | Tailwind `transition-all duration-300` + conditional classes | Project already uses Tailwind transitions throughout (collapsible panels, pulse effects). |
| GPM benchmark comparison | Dynamic benchmark API | Static constants object | Benchmarks are fixed per D-11. A map of role to GPM threshold is 5 lines. |

## GSI Pipeline Extension

### Current State
The GSI config (`settings.py`) enables: `provider`, `map`, `player`, `hero`, `abilities`, `items`. It does NOT enable `buildings`.

The `GsiMap` Pydantic model parses: `name`, `matchid`, `game_time`, `clock_time`, `daytime`, `game_state`, `paused`. It does NOT parse `roshan_state` or `roshan_state_end_seconds`.

The `ParsedGsiState` dataclass forwards: `game_clock`, `game_state`, `is_alive`, and player stats. It does NOT forward Roshan state or building data.

### Required Changes

**1. Roshan state from map data (HIGH confidence)**
The `map` section already includes `roshan_state` and `roshan_state_end_seconds` fields. These are sent alongside `clock_time` and `game_state` when `"map" "1"` is configured. No GSI config change needed.

Known `roshan_state` values (from antonpup/Dota2GSI C# library):
- `"alive"` -- Roshan is up
- `"respawn_base"` -- Dead, base respawn timer running (8 min)
- `"respawn_variable"` -- Base timer expired, variable window (3 min)

Detection: When `roshan_state` transitions from `"alive"` to `"respawn_base"`, Roshan was just killed.

**2. Buildings data for tower detection (MEDIUM confidence)**
Tower health data requires adding `"buildings" "1"` to the GSI config. The availability of buildings data in player mode (not spectating) is not definitively documented. Multiple community sources suggest player mode receives limited data, but buildings may still be sent since tower health is visible to the player in-game.

Recommended approach:
- Add `"buildings" "1"` to the GSI config template
- Parse building count on the backend (count buildings with health > 0)
- Forward `radiant_tower_count` and `dire_tower_count` (integer counts)
- If buildings data is empty/missing in player mode at runtime, tower kill detection gracefully degrades -- tower kills would only be caught by the gold swing threshold

Buildings JSON structure (from community docs):
```json
{
  "buildings": {
    "radiant": {
      "dota_goodguys_tower1_top": { "health": 1800, "max_health": 1800 },
      "dota_goodguys_tower2_top": { "health": 1800, "max_health": 1800 },
      "dota_goodguys_tower3_top": { "health": 1800, "max_health": 1800 },
      "dota_goodguys_tower1_mid": { "health": 1800, "max_health": 1800 },
      ...
    },
    "dire": {
      "dota_badguys_tower1_top": { "health": 1800, "max_health": 1800 },
      ...
    }
  }
}
```

Tower names follow the pattern: `dota_{goodguys|badguys}_tower{1-4}_{top|mid|bot}`
Plus: `dota_{goodguys|badguys}_fort` (ancient)
Plus: `good_rax_{melee|range}_{top|mid|bot}` / `bad_rax_{melee|range}_{top|mid|bot}`

For tower detection, count towers with `health > 0` each tick. If count decreases, a tower was destroyed.

### GsiLiveState Extension
```typescript
// New fields to add to GsiLiveState interface
export interface GsiLiveState {
  // ... existing fields ...
  roshan_state: string;           // "alive" | "respawn_base" | "respawn_variable"
  radiant_tower_count: number;    // count of alive towers (0-11)
  dire_tower_count: number;       // count of alive towers (0-11)
}
```

### Backend ParsedGsiState Extension
```python
@dataclass
class ParsedGsiState:
    # ... existing fields ...
    roshan_state: str = "alive"
    radiant_tower_count: int = 11
    dire_tower_count: int = 11
```

## Common Pitfalls

### Pitfall 1: Stale Closure in Async recommend()
**What goes wrong:** The `recommend()` function from `useRecommendation` hook reads gameStore at call time. If called from inside a stale subscription closure, it reads old state.
**Why it happens:** Zustand `subscribe()` runs outside React's render cycle, so hook-returned functions may be stale.
**How to avoid:** Use `useRecommendationStore.getState()` and `useGameStore.getState()` directly (synchronous, always current) rather than hook-returned functions. The existing `recommend()` function already does this correctly.
**Warning signs:** Recommendations don't include the updated lane result after auto-detection.

### Pitfall 2: Double-Fire on Game Phase Transitions
**What goes wrong:** The 10:00 phase transition fires both lane auto-detection AND the phase transition trigger, causing two refreshes in quick succession.
**Why it happens:** Lane detection and phase transition are conceptually separate but triggered by the same clock crossing.
**How to avoid:** Lane detection at 10:00 should be part of the 10:00 phase transition handler, not a separate trigger. Per D-14: "Lane result auto-detection triggers a re-evaluation as part of the 10:00 game phase transition event." They are ONE event.
**Warning signs:** Two toasts appearing at 10:00, or two API calls firing.

### Pitfall 3: Gold Swing Baseline Never Resets
**What goes wrong:** Gold swing threshold computes delta from net worth at last refresh. If the baseline never resets on manual Re-Evaluate, the delta grows unbounded and triggers spuriously.
**Why it happens:** Manual Re-Evaluate bypasses the auto-refresh system but still needs to reset the gold baseline per D-04.
**How to avoid:** Reset `netWorthAtLastRefresh` whenever ANY refresh fires (auto or manual). Both paths must update the baseline.
**Warning signs:** Gold swing triggers immediately after a manual re-evaluate.

### Pitfall 4: Cooldown Timer Memory Leak
**What goes wrong:** setInterval for cooldown countdown is not cleaned up when component unmounts or game ends.
**Why it happens:** Missing cleanup in useEffect return function.
**How to avoid:** Always return a cleanup function from useEffect that clears the interval. Also clear interval when game_state changes away from "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS".
**Warning signs:** Console warnings about state updates on unmounted components.

### Pitfall 5: Tower Count Detection False Positives from GSI Reconnect
**What goes wrong:** If GSI disconnects and reconnects mid-game, the "previous" tower count is stale (e.g., 11), and the current count may be lower, triggering false tower kill events.
**Why it happens:** The previous-state ref retains pre-disconnect values.
**How to avoid:** When gsiStatus transitions from non-connected to connected, reset all previous-state refs to current values without triggering events. Treat reconnection as a "sync" not a "diff".
**Warning signs:** Toast saying "Tower destroyed" when reconnecting to an ongoing game.

### Pitfall 6: Roshan State Not Available in Player Mode
**What goes wrong:** If `map.roshan_state` is not sent in player mode (only spectator), the field is undefined/empty on every tick, and Roshan kills are never detected.
**Why it happens:** Dota 2 GSI limits some data to spectator mode to prevent cheating. Whether `roshan_state` on the map object (vs the separate Roshan spectator object) is available in player mode is not definitively documented.
**How to avoid:** Parse `roshan_state` from map data (which IS the player-mode map object, not the spectator-only Roshan object). If the field is consistently empty/missing at runtime, log a warning and disable Roshan trigger detection. The gold swing threshold will still catch Roshan kills indirectly (Aegis pickup gives gold and the fight causes gold swings).
**Warning signs:** `roshan_state` is always `""` or undefined in production.

## Code Examples

### Lane Result Auto-Detection
```typescript
// Source: D-11 benchmarks
const GPM_BENCHMARKS: Record<number, number> = {
  1: 500,  // Pos 1 Carry
  2: 480,  // Pos 2 Mid
  3: 400,  // Pos 3 Off
  4: 280,  // Pos 4 Soft Sup
  5: 230,  // Pos 5 Hard Sup
};

function detectLaneResult(
  gpm: number,
  role: number,
): "won" | "even" | "lost" {
  const benchmark = GPM_BENCHMARKS[role];
  if (!benchmark) return "even";

  if (gpm > benchmark * 1.10) return "won";
  if (gpm < benchmark * 0.90) return "lost";
  return "even";
}
```

### useAutoRefresh Hook Skeleton
```typescript
// Source: Follows useGsiSync.ts established pattern
export function useAutoRefresh(): void {
  const prevStateRef = useRef<PreviousState>({
    deaths: 0,
    netWorthAtLastRefresh: 0,
    roshanState: "alive",
    radiantTowers: 11,
    direTowers: 11,
  });
  const firedPhasesRef = useRef<Set<number>>(new Set());
  const cooldownEndRef = useRef<number>(0);
  const queuedEventRef = useRef<TriggerEvent | null>(null);

  useEffect(() => {
    const unsubscribe = useGsiStore.subscribe((state) => {
      if (state.gsiStatus !== "connected") return;
      const live = state.liveState;
      if (!live) return;
      if (live.game_state !== "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS") return;

      // Don't auto-refresh if no recommendations exist yet
      if (!useRecommendationStore.getState().data) return;
      if (useRecommendationStore.getState().isLoading) return;

      const prev = prevStateRef.current;
      const event = detectTriggers(live, prev, firedPhasesRef.current);
      if (!event) return;

      const now = Date.now();
      if (now < cooldownEndRef.current) {
        // Queue the event (latest replaces previous)
        queuedEventRef.current = event;
        useRefreshStore.getState().queueEvent(event);
        return;
      }

      // Fire immediately
      fireRefresh(event, prevStateRef, cooldownEndRef);
    });

    // Cooldown expiry check (1Hz)
    const interval = setInterval(() => {
      const now = Date.now();
      const queued = queuedEventRef.current;
      if (queued && now >= cooldownEndRef.current) {
        queuedEventRef.current = null;
        fireRefresh(queued, prevStateRef, cooldownEndRef);
      }
      // Update countdown display
      useRefreshStore.getState().tick(now);
    }, 1000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);
}
```

### Backend roshan_state Parsing
```python
# Source: Extend gsi/models.py GsiMap
class GsiMap(BaseModel):
    name: str = ""
    matchid: str = ""
    game_time: float = 0
    clock_time: float = 0
    daytime: bool = True
    game_state: str = ""
    paused: bool = False
    roshan_state: str = ""                   # NEW
    roshan_state_end_seconds: float = 0      # NEW
    model_config = ConfigDict(extra="allow")
```

### Backend Buildings Parsing
```python
# Source: New gsi/models.py classes
class GsiBuilding(BaseModel):
    health: int = 0
    max_health: int = 0

class GsiTeamBuildings(BaseModel):
    model_config = ConfigDict(extra="allow")
    # All fields are dynamic (dota_goodguys_tower1_top, etc.)
    # Use extra="allow" and count non-zero health entries

class GsiBuildings(BaseModel):
    radiant: dict[str, GsiBuilding] = {}
    dire: dict[str, GsiBuilding] = {}
    model_config = ConfigDict(extra="allow")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Polling API on timer | Event-driven from GSI state diffs | This phase | Only refreshes when game state actually changes |
| Manual lane result input only | Auto-detect from GPM + allow override | This phase | Hands-free during laning phase |
| No rate limiting | 2-minute cooldown with queue | This phase | Controls API costs while staying responsive |

## Open Questions

1. **Buildings data in player mode**
   - What we know: GSI `"buildings"` config section exists, buildings data is well-documented for spectator mode, player mode has limited data access.
   - What's unclear: Whether Dota 2 sends buildings data when `"buildings" "1"` is configured and the user is actively playing (not spectating). Community documentation is inconsistent.
   - Recommendation: Add `"buildings" "1"` to the GSI config and attempt to parse it. The backend should gracefully handle missing buildings data. Tower detection has a natural fallback: the gold swing threshold (>2000g) will catch most tower kills since tower bounty creates a team gold event. Flag for validation in Phase 12 implementation -- test with a real game.

2. **Roshan state in player mode**
   - What we know: `map.roshan_state` is part of the Map data (not the spectator-only Roshan object). Map data IS sent in player mode. The C# library defines RoshanState enum: `Alive`, `Respawn_Base`, `Respawn_Variable`.
   - What's unclear: Whether `roshan_state` is populated in the map section when playing (not spectating). The separate `Roshan` top-level object is confirmed spectator-only, but `map.roshan_state` may be different.
   - Recommendation: Parse it from map data. If consistently empty at runtime, Roshan detection is disabled and gold swing catches the fight. MEDIUM confidence it works.

3. **GPM benchmarks accuracy**
   - What we know: D-11 specifies static benchmarks (Pos 1: ~500, Pos 2: ~480, etc.).
   - What's unclear: These are approximate and may not reflect current patch meta. STATE.md notes: "Lane result GPM thresholds need verification against current patch data before Phase 12."
   - Recommendation: Use D-11 values as-is (they are locked decisions). The auto-detect includes user override (D-13), so slightly inaccurate benchmarks are correctable. Can be tuned post-release.

4. **GSI config regeneration UX**
   - What we know: Adding `"buildings" "1"` to the GSI config requires users to re-download and replace their config file.
   - What's unclear: Whether users will notice they need a new config.
   - Recommendation: When buildings data is expected but not received for 30+ seconds of connected GSI, show a subtle warning in the UI suggesting config regeneration. Low priority -- tower detection has gold swing fallback.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified). Phase 12 is purely code/config changes to existing frontend and backend.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | `prismlab/frontend/vitest.config.ts` |
| Quick run command | `cd prismlab/frontend && npx vitest run` |
| Full suite command | `cd prismlab/frontend && npx vitest run` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GSI-05 | Lane result auto-detected from GPM vs role benchmark at 10 min | unit | `cd prismlab/frontend && npx vitest run src/utils/laneBenchmarks.test.ts -x` | No -- Wave 0 |
| REFRESH-01 | Events detected from GSI state diffs (death, gold swing, tower, roshan, phase) | unit | `cd prismlab/frontend && npx vitest run src/utils/triggerDetection.test.ts -x` | No -- Wave 0 |
| REFRESH-01 | useAutoRefresh fires recommend() on detected events | unit | `cd prismlab/frontend && npx vitest run src/hooks/useAutoRefresh.test.ts -x` | No -- Wave 0 |
| REFRESH-02 | Cooldown prevents auto-refresh within 2 minutes; queue-latest behavior | unit | `cd prismlab/frontend && npx vitest run src/hooks/useAutoRefresh.test.ts -x` | No -- Wave 0 |
| REFRESH-02 | Manual Re-Evaluate bypasses cooldown and resets timer | unit | `cd prismlab/frontend && npx vitest run src/hooks/useAutoRefresh.test.ts -x` | No -- Wave 0 |
| REFRESH-03 | Toast appears with correct trigger message after refresh | unit | `cd prismlab/frontend && npx vitest run src/stores/refreshStore.test.ts -x` | No -- Wave 0 |
| GSI-05 | Lane result override persists after auto-detection | unit | `cd prismlab/frontend && npx vitest run src/hooks/useAutoRefresh.test.ts -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/frontend && npx vitest run`
- **Per wave merge:** `cd prismlab/frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `src/utils/laneBenchmarks.test.ts` -- covers GSI-05 (GPM benchmark logic)
- [ ] `src/utils/triggerDetection.test.ts` -- covers REFRESH-01 (event detection pure functions)
- [ ] `src/hooks/useAutoRefresh.test.ts` -- covers REFRESH-01, REFRESH-02 (hook integration)
- [ ] `src/stores/refreshStore.test.ts` -- covers REFRESH-02, REFRESH-03 (cooldown + toast state)
- [ ] Backend: `tests/test_gsi.py` extended for roshan_state and building parsing

## Sources

### Primary (HIGH confidence)
- `prismlab/frontend/src/hooks/useGsiSync.ts` -- Established Zustand subscription pattern for GSI event detection
- `prismlab/frontend/src/stores/gsiStore.ts` -- GsiLiveState interface with available fields
- `prismlab/backend/gsi/models.py` -- GsiMap model with `extra="allow"` (already accepts unknown fields)
- `prismlab/backend/gsi/state_manager.py` -- ParsedGsiState dataclass, state normalization pattern
- `prismlab/backend/api/routes/settings.py` -- GSI config template (currently missing `"buildings"`)
- [antonpup/Dota2GSI Map.cs](https://github.com/antonpup/Dota2GSI/blob/master/Dota2GSI/Nodes/Map.cs) -- RoshanState enum values: Undefined, Alive, Respawn_Base, Respawn_Variable

### Secondary (MEDIUM confidence)
- [antonpup/Dota2GSI](https://github.com/antonpup/Dota2GSI) -- C# GSI library, comprehensive data model
- [xzion/dota2-gsi](https://github.com/xzion/dota2-gsi) -- Node.js GSI library, data field documentation
- [MrBean355/dota2-gsi](https://github.com/MrBean355/dota2-gsi) -- JVM library, player vs spectator mode distinction
- [LogRocket toast comparison](https://blog.logrocket.com/react-toast-libraries-compared-2025/) -- React toast library comparison (informed custom vs library decision)

### Tertiary (LOW confidence)
- Buildings data availability in player mode -- Multiple community sources suggest limited data, but no definitive confirmation either way. Needs runtime validation.
- `map.roshan_state` in player mode -- Likely available since it's on the Map object (not the spectator-only Roshan object), but not definitively confirmed. Needs runtime validation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, uses established patterns
- Architecture: HIGH -- follows useGsiSync.ts pattern exactly, pure functions for trigger detection
- GSI extension (roshan_state): MEDIUM -- map data should include it, but player mode not definitively documented
- GSI extension (buildings): LOW-MEDIUM -- may not be available in player mode; has gold swing fallback
- Lane benchmarks: HIGH -- simple pure function, values locked in D-11
- Pitfalls: HIGH -- identified from existing codebase patterns and GSI reconnection edge cases
- Cooldown/queue logic: HIGH -- straightforward timestamp comparison

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, no fast-moving dependencies)
