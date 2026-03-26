---
phase: 12-auto-refresh-lane-detection
verified: 2026-03-26T21:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Live game: confirm auto-refresh fires once after a death occurs"
    expected: "Toast appears bottom-right with 'Death -- reassessing priorities', recommendations update, 120s cooldown starts"
    why_human: "Requires actual Dota 2 GSI data stream; cannot simulate the full subscription-to-refresh path in a static check"
  - test: "Live game: confirm lane result auto-sets at 10:00 with 'auto-detected from GPM' indicator visible"
    expected: "LaneResultSelector shows correct won/even/lost based on GPM, indicator text appears below the buttons"
    why_human: "Requires live game_clock advancing to 600 with real GSI data"
  - test: "Confirm 'auto in M:SS' countdown appears below Re-Evaluate when cooldown is active and an event is queued"
    expected: "After auto-refresh fires, pressing Re-Evaluate within 120s with a subsequent event queued shows countdown text"
    why_human: "Requires UI interaction with active cooldown state"
  - test: "Confirm item purchase does NOT trigger auto-refresh (D-02 design decision)"
    expected: "Buying an item during a game produces no toast and no new recommendation request"
    why_human: "Item purchase detection exclusion must be verified against live GSI inventory changes"
---

# Phase 12: Auto-Refresh & Lane Detection Verification Report

**Phase Goal:** Recommendations update hands-free when the game state changes significantly, and lane outcome is determined automatically from gold data
**Verified:** 2026-03-26T21:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | At 10:00, lane result auto-set from GPM vs role benchmark; player can confirm or override | VERIFIED | `useAutoRefresh.ts:157-165` checks `game_clock >= 600 && !laneAutoDetectedRef.current`, calls `detectLaneResult(gpm, role)`, then `setLaneResult(result)`. `LaneResultSelector` shows "auto-detected from GPM" when flag is true. User override works via any button click calling `setLaneResult`. |
| 2 | Recommendations auto-refresh on death, gold swing, tower kill, roshan kill, phase transition — without player pressing Re-Evaluate | VERIFIED | `useAutoRefresh.ts` subscribes to `gsiStore` via `useGsiStore.subscribe()`, calls `detectTriggers()` on each 1Hz update, calls `fireRefresh()` when an event is detected and no cooldown is active. Item purchase is explicitly excluded per D-02. |
| 3 | Auto-refresh never fires more than once per 2 minutes | VERIFIED | `cooldownEndRef` set to `Date.now() + 120_000` in `fireRefresh()` at line 65. Guard at line 196: `if (now < cooldownEndRef.current)` queues the event instead of firing. Manual Re-Evaluate also resets the cooldown via `recommendationStore` subscription at line 246. |
| 4 | Toast notification appears after each auto-refresh explaining the trigger | VERIFIED | `fireRefresh()` calls `useRefreshStore.getState().showToast(event.message)` at line 83. `AutoRefreshToast.tsx` reads `lastToast` from `refreshStore`, renders bottom-right with lightning bolt and "Recommendations updated" header, auto-dismisses after 4 seconds. |

**Score:** 4/4 truths verified (all phase-level truths from ROADMAP)

---

### Required Artifacts

All 9 artifacts from all 3 plan `must_haves` blocks verified across levels 1-3.

| Artifact | Expected | Level 1 (Exists) | Level 2 (Substantive) | Level 3 (Wired) | Status |
|----------|----------|------------------|-----------------------|-----------------|--------|
| `prismlab/backend/gsi/models.py` | GsiBuilding, GsiBuildings, GsiMap.roshan_state | EXISTS | 127 lines; GsiMap has `roshan_state: str = "alive"` and `roshan_state_end_seconds`; GsiBuilding and GsiBuildings models present; GsiPayload has `buildings: GsiBuildings | None = None` | Imported in `state_manager.py` | VERIFIED |
| `prismlab/backend/gsi/state_manager.py` | ParsedGsiState with roshan_state, radiant_tower_count, dire_tower_count | EXISTS | 189 lines; All 3 new fields in ParsedGsiState; `_count_alive_towers()` helper; full extraction logic in `update()` method; `to_broadcast_dict()` uses `dataclasses.asdict()` which includes all fields | Used by GSI route; broadcasts via WebSocket | VERIFIED |
| `prismlab/backend/api/routes/settings.py` | GSI config template with "buildings" data section | EXISTS | `"buildings"     "1"` confirmed present at line 29 of file | Config generated when user downloads GSI file | VERIFIED |
| `prismlab/frontend/src/utils/laneBenchmarks.ts` | GPM_BENCHMARKS, detectLaneResult() | EXISTS | 37 lines; exports `GPM_BENCHMARKS` with all 5 roles (1:500, 2:480, 3:400, 4:280, 5:230); exports `detectLaneResult()` with correct +/-10% thresholds | Imported in `useAutoRefresh.ts:11` and called at line 160 | VERIFIED |
| `prismlab/frontend/src/utils/triggerDetection.ts` | TriggerEvent, PreviousState, CurrentState, detectTriggers() | EXISTS | 108 lines; exports all 4 types/functions; 5 trigger types in correct priority order; fire-once semantics via `firedPhases` Set mutation; item purchase explicitly excluded per D-02 comment | Imported in `useAutoRefresh.ts:6-10` and called at line 178 | VERIFIED |
| `prismlab/frontend/src/stores/gsiStore.ts` | Extended GsiLiveState with roshan_state, tower counts | EXISTS | `GsiLiveState` has `roshan_state: string`, `radiant_tower_count: number`, `dire_tower_count: number` at lines 21-23 | Used by `useAutoRefresh.ts` subscription to access new fields | VERIFIED |
| `prismlab/frontend/src/stores/refreshStore.ts` | Cooldown state, queued event, toast, tick countdown | EXISTS | 68 lines; `cooldownEnd`, `queuedEvent`, `secondsRemaining`, `lastToast`, `laneAutoDetected`; all 7 actions implemented; 120s cooldown (`120_000`); queue-latest-only; tick uses `Math.ceil` | Used by `useAutoRefresh.ts`, `ReEvaluateButton.tsx`, `LaneResultSelector.tsx`, `AutoRefreshToast.tsx` | VERIFIED |
| `prismlab/frontend/src/hooks/useAutoRefresh.ts` | Core auto-refresh hook with all behaviors | EXISTS | 263 lines; `useGsiStore.subscribe()` for event detection; `detectTriggers()` integration; 120s cooldown with queue; lane auto-detect at 600s; toast via `showToast()`; manual Re-Evaluate reset tracking | Called in `App.tsx:16` as `useAutoRefresh()` | VERIFIED |
| `prismlab/frontend/src/components/toast/AutoRefreshToast.tsx` | Bottom-right toast with trigger messages | EXISTS | 58 lines; fixed bottom-right positioning; lightning bolt SVG icon; "Recommendations updated" header; reads `lastToast` from `refreshStore`; 4s auto-dismiss with animation | Rendered in `App.tsx:53` as `<AutoRefreshToast />` | VERIFIED |

---

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `state_manager.py` | `models.py` | `GsiMap.roshan_state`, `GsiBuildings` | WIRED | Line 12: `from gsi.models import GsiBuilding, GsiPayload`; `payload.map.roshan_state` at line 115; `payload.buildings` at line 120 |
| `useAutoRefresh.ts` | `gsiStore.ts` | `useGsiStore.subscribe()` | WIRED | Line 125: `const unsubscribe = useGsiStore.subscribe((state) => {...})` |
| `useAutoRefresh.ts` | `triggerDetection.ts` | `detectTriggers()` call | WIRED | Line 7: `import { detectTriggers, ... } from "../utils/triggerDetection"`, called at line 178 |
| `useAutoRefresh.ts` | `refreshStore.ts` | `useRefreshStore.getState()` | WIRED | Lines 66, 80, 83, 163, 199, 217, 223, 247, 257: multiple `useRefreshStore.getState()` calls |
| `useAutoRefresh.ts` | `useRecommendation.ts` (equivalent) | Direct store access calling `api.recommend()` | WIRED | Lines 56-57: reads `useGameStore.getState()` and `useRecommendationStore.getState()`; calls `api.recommend(request)` at line 110. Note: replicates `useRecommendation.recommend()` logic directly (hooks cannot be called inside effects — documented as key decision in SUMMARY) |
| `useAutoRefresh.ts` | `gameStore.ts` | `setLaneResult()` at 10:00 | WIRED | Line 161: `useGameStore.getState().setLaneResult(result)` |
| `AutoRefreshToast.tsx` | `refreshStore.ts` | Reads `lastToast` | WIRED | Line 5: `const toast = useRefreshStore((s) => s.lastToast)` |
| `App.tsx` | `useAutoRefresh.ts` | `useAutoRefresh()` hook call | WIRED | Line 7: `import { useAutoRefresh }`, called at line 16 |
| `LaneResultSelector.tsx` | `refreshStore.ts` | Reads `laneAutoDetected` | WIRED | Line 8: `const laneAutoDetected = useRefreshStore((s) => s.laneAutoDetected)`, rendered at line 32 |
| `ReEvaluateButton.tsx` | `refreshStore.ts` | Reads `secondsRemaining`, `queuedEvent` | WIRED | Lines 6-7: both fields read from `useRefreshStore`; countdown rendered at lines 26-31 |

---

### Data-Flow Trace (Level 4)

Artifacts that render dynamic data were traced for real data flow.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `AutoRefreshToast.tsx` | `lastToast` | `refreshStore.lastToast`, set by `showToast()` in `useAutoRefresh.fireRefresh()` | Yes — `event.message` comes from `detectTriggers()` which compares live GSI state diffs | FLOWING |
| `ReEvaluateButton.tsx` | `secondsRemaining` | `refreshStore.secondsRemaining`, updated by `tick(Date.now())` in 1Hz interval | Yes — computed as `Math.ceil((cooldownEnd - now) / 1000)` from real timestamps | FLOWING |
| `LaneResultSelector.tsx` | `laneAutoDetected` | `refreshStore.laneAutoDetected`, set by `setLaneAutoDetected(true)` in `useAutoRefresh` | Yes — set only after `detectLaneResult(gpm, role)` fires at game_clock >= 600 | FLOWING |

---

### Behavioral Spot-Checks

Step 7b: SKIPPED for server-dependent behaviors (requires live Dota 2 GSI stream). Static module checks performed instead.

| Behavior | Check | Result | Status |
|----------|-------|--------|--------|
| `triggerDetection.ts` exports expected functions | `grep "export function detectTriggers\|export interface TriggerEvent" triggerDetection.ts` | Both found | PASS |
| `laneBenchmarks.ts` exports GPM_BENCHMARKS and detectLaneResult | `grep "export const GPM_BENCHMARKS\|export function detectLaneResult" laneBenchmarks.ts` | Both found | PASS |
| `refreshStore.ts` exports useRefreshStore with 120s cooldown | `grep "120_000" refreshStore.ts` | Found at line 43 | PASS |
| `useAutoRefresh.ts` exports `useAutoRefresh` | `grep "export function useAutoRefresh" useAutoRefresh.ts` | Found at line 37 | PASS |
| Item purchase is NOT a trigger | No item/inventory comparison in `detectTriggers()` or subscription handler | Confirmed absent from detection logic | PASS |
| Phase transitions fire exactly once | `firedPhasesRef` (Set) checked before add at `useAutoRefresh.ts:45`, `detectTriggers()` adds to Set and returns | Fire-once semantics implemented | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GSI-05 | 12-01, 12-03 | Lane result auto-determined from GPM vs role benchmarks at 10 minutes | SATISFIED | `detectLaneResult()` in `laneBenchmarks.ts` with `GPM_BENCHMARKS` for all 5 roles; called in `useAutoRefresh.ts:160` at game_clock >= 600; `laneAutoDetected` flag surfaces in `LaneResultSelector.tsx` |
| REFRESH-01 | 12-01, 12-02, 12-03 | Auto-refresh on key game events (death, tower, Roshan, gold swing). NOTE: REQUIREMENTS.md lists "item purchase" as a trigger, but CONTEXT.md D-02 establishes item purchase does NOT trigger auto-refresh — this is a deliberate design decision. The implementation correctly excludes item purchase per D-02. | SATISFIED (with design variance) | `detectTriggers()` implements 5 event types; wired into `useAutoRefresh.ts` subscription; item purchase explicitly excluded per D-02 |
| REFRESH-02 | 12-02, 12-03 | Rate limiter: max 1 auto-refresh per 2 minutes | SATISFIED | `cooldownEndRef = Date.now() + 120_000`; guard at `useAutoRefresh.ts:196`; manual Re-Evaluate also resets 120s timer |
| REFRESH-03 | 12-02, 12-03 | Toast shows reason for update | SATISFIED | `showToast(event.message)` with trigger-specific messages from D-16: "Death -- reassessing priorities", "Gold swing: +Xg", "Tower destroyed -- map changed", "Roshan killed -- updating", "Lane phase ended (10:00)", etc. |

**Orphaned requirements check:** All 4 requirement IDs declared in plans (GSI-05, REFRESH-01, REFRESH-02, REFRESH-03) match the 4 IDs mapped to Phase 12 in REQUIREMENTS.md. No orphaned requirements.

---

### Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `refreshStore.ts:3-11` | `TriggerEvent` defined locally, duplicating definition from `triggerDetection.ts` | INFO | Documented in SUMMARY as deliberate (parallel wave execution). Both definitions are identical. Plan 03 SUMMARY notes reconciliation was not performed — the duplicate persists. Not a functional issue; TypeScript structural typing means they are interchangeable. |

No stubs, no placeholder returns, no TODO/FIXME blockers found.

---

### Human Verification Required

#### 1. Live Game: Auto-refresh fires on death
**Test:** With GSI running in an active Dota 2 game, intentionally die
**Expected:** Toast appears bottom-right showing "Death -- reassessing priorities", new recommendations load, cooldown timer shows below Re-Evaluate button
**Why human:** Requires actual Dota 2 GSI stream advancing `deaths` field; cannot mock full subscription chain in a static check

#### 2. Live Game: Lane result auto-detection at 10:00
**Test:** Start a game with any hero, reach the 10-minute mark with GSI active
**Expected:** LaneResultSelector auto-selects won/even/lost, "auto-detected from GPM" text appears in italic below the buttons
**Why human:** Requires live `game_clock` advancing to 600 seconds with real GPM data

#### 3. Cooldown countdown visibility
**Test:** Trigger an auto-refresh, then within 2 minutes trigger another significant event (death, etc.)
**Expected:** "auto in M:SS" countdown appears below the Re-Evaluate button and counts down
**Why human:** Requires active cooldown state with a queued event simultaneously present

#### 4. Item purchase does not trigger auto-refresh
**Test:** Buy an item during an active game session with GSI connected
**Expected:** No toast appears, no new recommendation request fires
**Why human:** Item purchase exclusion (D-02) must be verified against live GSI inventory changes advancing `items_inventory` field

---

### Gaps Summary

No gaps. All must-have truths are verified, all required artifacts exist and are substantive and wired, all key links are confirmed, and all 4 requirement IDs are satisfied.

One design note: REFRESH-01 in REQUIREMENTS.md lists "item purchase" as a trigger, but CONTEXT.md D-02 explicitly removes it as a deliberate design decision. The implementation correctly follows D-02 (CONTEXT.md takes precedence over the requirements text per the verification prompt instruction). This is not a gap — it is an intentional design variance documented in the phase context.

One minor code duplication: `TriggerEvent` is defined in both `triggerDetection.ts` and `refreshStore.ts`. This is structurally harmless (TypeScript duck typing), documented in the SUMMARY, and flagged INFO-only.

---

## Test Coverage Summary

| Test Suite | File | Count | Status |
|-----------|------|-------|--------|
| Backend: Roshan/Buildings | `test_gsi.py::TestRoshanAndBuildings` | 10 tests | Verified present with complete coverage of all spec behaviors |
| Frontend: laneBenchmarks | `laneBenchmarks.test.ts` | 9 tests | All 5 roles, boundary conditions (won/even/lost transitions) |
| Frontend: triggerDetection | `triggerDetection.test.ts` | 16 tests | All 5 event types, priority order, fire-once semantics, null return |
| Frontend: refreshStore | `refreshStore.test.ts` | 12 tests | Cooldown, queue-latest-only, toast, tick countdown, reset |
| Frontend: gsiStore extension | `gsiStore.test.ts` | 7 tests (1 new) | Extended fields preserved through `updateLiveState` |

---

_Verified: 2026-03-26T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
