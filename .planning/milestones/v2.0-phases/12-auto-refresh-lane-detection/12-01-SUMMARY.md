---
phase: 12-auto-refresh-lane-detection
plan: 01
subsystem: gsi, utils
tags: [gsi, roshan, buildings, towers, lane-detection, trigger-detection, tdd, vitest, pytest]

# Dependency graph
requires:
  - phase: 10-gsi-websocket-bridge
    provides: GSI models, state manager, WebSocket broadcast, GSI config template
provides:
  - GsiMap.roshan_state and roshan_state_end_seconds fields
  - GsiBuilding and GsiBuildings models for tower health parsing
  - ParsedGsiState with roshan_state, radiant_tower_count, dire_tower_count
  - GSI config template with buildings data section
  - laneBenchmarks utility with GPM_BENCHMARKS and detectLaneResult()
  - triggerDetection utility with detectTriggers() for 5 event types
affects: [12-02-auto-refresh-hook, 12-03-lane-result-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure utility functions with comprehensive boundary tests (laneBenchmarks, triggerDetection)"
    - "Set mutation for fire-once semantics in trigger detection"
    - "_count_alive_towers helper filtering building keys by 'tower' substring"

key-files:
  created:
    - prismlab/frontend/src/utils/laneBenchmarks.ts
    - prismlab/frontend/src/utils/laneBenchmarks.test.ts
    - prismlab/frontend/src/utils/triggerDetection.ts
    - prismlab/frontend/src/utils/triggerDetection.test.ts
  modified:
    - prismlab/backend/gsi/models.py
    - prismlab/backend/gsi/state_manager.py
    - prismlab/backend/api/routes/settings.py
    - prismlab/backend/tests/test_gsi.py

key-decisions:
  - "Tower counting filters by 'tower' substring in building key names, excluding rax and fort entries"
  - "Phase transition thresholds checked highest-first (2100 > 1200 > 600) to catch jumps past multiple thresholds"

patterns-established:
  - "Pure trigger detection with Set<number> mutation for fire-once phase transitions"
  - "Factory helpers (makeCurrentState, makePrevState) for clean trigger detection test setup"

requirements-completed: [GSI-05, REFRESH-01]

# Metrics
duration: 5min
completed: 2026-03-26
---

# Phase 12 Plan 01: GSI Roshan/Buildings Pipeline and Frontend Trigger Detection Summary

**Extended GSI backend to parse roshan_state and tower counts from buildings data, created pure laneBenchmarks and triggerDetection utility modules with 59 tests total**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-26T19:39:30Z
- **Completed:** 2026-03-26T19:44:56Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- GsiMap now parses roshan_state and roshan_state_end_seconds from Dota 2 GSI map data
- GsiBuilding/GsiBuildings models parse tower health, StateManager counts alive towers per team
- GSI config template includes "buildings" "1" so Dota 2 sends building health data
- laneBenchmarks.ts classifies GPM vs role-specific benchmarks (5 roles) into won/even/lost
- triggerDetection.ts detects 5 event types with correct priority and fire-once phase transitions
- 59 total tests (34 backend + 25 frontend), all passing, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend backend GSI pipeline for Roshan state and buildings data**
   - `25d982c` (test) - RED: failing tests for roshan/buildings
   - `c86d9b7` (feat) - GREEN: implementation passing all tests

2. **Task 2: Create laneBenchmarks and triggerDetection frontend utility modules with tests**
   - `c92ee0d` (test) - RED: failing tests for laneBenchmarks and triggerDetection
   - `0777401` (feat) - GREEN: implementation passing all tests

## Files Created/Modified
- `prismlab/backend/gsi/models.py` - Added GsiMap.roshan_state, GsiBuilding, GsiBuildings models
- `prismlab/backend/gsi/state_manager.py` - Added roshan_state, tower counts to ParsedGsiState with _count_alive_towers helper
- `prismlab/backend/api/routes/settings.py` - Added "buildings" "1" to GSI config template data section
- `prismlab/backend/tests/test_gsi.py` - 10 new tests for roshan/buildings parsing
- `prismlab/frontend/src/utils/laneBenchmarks.ts` - GPM_BENCHMARKS constant and detectLaneResult() function
- `prismlab/frontend/src/utils/laneBenchmarks.test.ts` - 9 tests covering all roles and boundary conditions
- `prismlab/frontend/src/utils/triggerDetection.ts` - TriggerEvent/PreviousState/CurrentState types, detectTriggers() pure function
- `prismlab/frontend/src/utils/triggerDetection.test.ts` - 16 tests covering all 5 event types, priority, fire-once, and edge cases

## Decisions Made
- Tower counting uses substring match on "tower" in building key names to exclude rax/fort entries (e.g., "dota_goodguys_tower1_top" matches but "dota_goodguys_melee_rax_top" does not)
- Phase transition thresholds checked highest-first (2100, 1200, 600) so if game clock jumps past multiple thresholds at once, the highest fires first
- Gold swing message includes sign prefix for positive deltas and uses toLocaleString() for number formatting

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all modules fully implemented with real logic, no placeholders.

## Next Phase Readiness
- Backend broadcasts roshan_state, radiant_tower_count, dire_tower_count via WebSocket -- ready for Plan 02 (useAutoRefresh hook)
- laneBenchmarks and triggerDetection utilities ready to be consumed by useAutoRefresh hook
- GsiLiveState interface in gsiStore.ts will need to be extended in Plan 02 to include the three new fields

## Self-Check: PASSED

All 9 files verified present. All 4 task commits verified in git log.

---
*Phase: 12-auto-refresh-lane-detection*
*Completed: 2026-03-26*
