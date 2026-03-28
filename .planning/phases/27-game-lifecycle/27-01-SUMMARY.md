---
phase: 27-game-lifecycle
plan: 01
subsystem: game-lifecycle
tags: [persistence, match-id, zustand, localStorage, new-game-detection]
dependency_graph:
  requires: []
  provides: [match-id-pipeline, store-persistence, new-game-reset]
  affects: [gameStore, recommendationStore, gsiStore, useGameIntelligence, state_manager]
tech_stack:
  added: [zustand-persist-middleware]
  patterns: [custom-set-serialization, match-id-tracking, ref-based-state-diffing]
key_files:
  created: []
  modified:
    - prismlab/backend/gsi/state_manager.py
    - prismlab/backend/tests/test_gsi.py
    - prismlab/frontend/src/stores/gsiStore.ts
    - prismlab/frontend/src/stores/gameStore.ts
    - prismlab/frontend/src/stores/recommendationStore.ts
    - prismlab/frontend/src/hooks/useGameIntelligence.ts
decisions:
  - "match_id change is the primary new-game trigger; hero_selection state is logged but not gated on"
  - "Custom storage adapter for recommendationStore handles Set<string> serialization via JSON replacer"
  - "gameStore uses default Zustand persist (all types are JSON-serializable natively)"
metrics:
  duration: 6min
  completed: "2026-03-28T18:12:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 27 Plan 01: GSI Match ID Pipeline and Store Persistence Summary

localStorage persistence for game and recommendation stores with Set serialization, match_id piped through GSI backend to frontend, and new-game detection that resets all match state on match_id change.

## What Was Done

### Task 1: Pipe match_id through GSI and add localStorage persistence to stores (57b1def)

**Backend (state_manager.py):**
- Added `match_id: str = ""` field to `ParsedGsiState` dataclass
- Extract `match_id` from `payload.map.matchid` in `GsiStateManager.update()`
- Automatically included in `to_broadcast_dict()` via `dataclasses.asdict()`

**Backend (tests/test_gsi.py):**
- Added `test_match_id_in_parsed_state` -- verifies matchid flows from GSI payload to ParsedGsiState
- Added `test_match_id_in_broadcast_dict` -- verifies match_id appears in broadcast output

**Frontend (gsiStore.ts):**
- Added `match_id: string` to `GsiLiveState` interface
- Added `matchId: string | null` to `GsiStore` interface (tracked independently from liveState)
- `updateLiveState` sets `matchId` when `data.match_id` is non-empty

**Frontend (gameStore.ts):**
- Wrapped store with Zustand `persist` middleware (key: `prismlab-game`, version: 1)
- Added `clear()` method that resets ALL match state to initial values
- No custom serialization needed -- all types are natively JSON-serializable

**Frontend (recommendationStore.ts):**
- Wrapped store with Zustand `persist` middleware (key: `prismlab-recommendations`, version: 1)
- Custom `storage` adapter that serializes `Set<string>` to arrays via JSON replacer and rehydrates arrays back to Sets on load

### Task 2: New game detection in useGameIntelligence (bbf2a9f)

- Added `prevMatchIdRef` to track match ID across GSI updates
- New-game detection block placed BEFORE hero auto-detection (section 0) so clear happens first, then new hero gets set in the same tick
- On match_id change: calls `gameStore.clear()`, `recommendationStore.clear()`, `refreshStore.resetCooldown()`
- Resets all internal refs: `prevHeroIdRef`, `firedPhasesRef`, `laneAutoDetectedRef`, `cooldownEndRef`, `queuedEventRef`, `prevStateRef`
- Hero selection state is secondary confirmation (logged but not gated on) -- match_id is definitive
- Settings (Steam ID, recommendation mode, volume, budget cap) are in separate localStorage keys and never touched

## Verification Results

- Backend: 259 passed, 2 skipped, 7 warnings (all pre-existing) in 53.5s
- Frontend: TypeScript compiles with zero errors (`npx tsc --noEmit`)

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all data paths are fully wired.

## Decisions Made

1. **Match ID is primary trigger only:** D-07 says "both signals required" but the plan (D-05 notes) correctly identifies that match_id change alone is definitive. Hero selection state is secondary confirmation logged for debugging but not gated on, avoiding missed resets when match_id changes during non-hero-selection states.

2. **Custom storage over createJSONStorage:** Used explicit custom `storage` adapter for recommendationStore rather than Zustand's `createJSONStorage` helper, because the Set serialization needs both a custom replacer (setItem) and rehydration (getItem) that are easier to reason about explicitly.

## Self-Check: PASSED

- All 7 files verified present on disk
- Both commit hashes (57b1def, bbf2a9f) verified in git log
