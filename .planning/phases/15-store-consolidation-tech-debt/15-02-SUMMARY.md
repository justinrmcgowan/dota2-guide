---
phase: 15-store-consolidation-tech-debt
plan: 02
subsystem: ui
tags: [react, zustand, hooks, gsi, playstyle, consolidation]

# Dependency graph
requires:
  - phase: 15-01
    provides: HERO_PLAYSTYLE_MAP, TriggerEvent single-source in triggerDetection.ts
  - phase: 12-auto-refresh
    provides: useAutoRefresh hook with event detection and cooldown
  - phase: 11-gsi-integration
    provides: useGsiSync hook with hero detection and item marking
provides:
  - useGameIntelligence consolidated hook replacing useGsiSync + useAutoRefresh
  - Playstyle auto-suggest from HERO_PLAYSTYLE_MAP on hero detection
  - Deterministic GSI event processing order (hero -> items -> lane -> events)
affects: [17-design-retheme, 18-performance]

# Tech tracking
tech-stack:
  added: []
  patterns: [consolidated-hook-pattern, separate-store-subscriptions, auto-suggest-with-manual-override]

key-files:
  created:
    - prismlab/frontend/src/hooks/useGameIntelligence.ts
    - prismlab/frontend/src/hooks/useGameIntelligence.test.ts
  modified:
    - prismlab/frontend/src/App.tsx

key-decisions:
  - "Separate gsiStore.subscribe and recommendationStore.subscribe calls within one hook to prevent cross-store write cascades"
  - "Playstyle auto-suggest only fires on hero_id change, user manual override preserved"
  - "suggestPlaystyle called immediately after setRole to prevent null playstyle flash"

patterns-established:
  - "Consolidated hook pattern: co-locate related subscriptions in one hook but keep separate subscribe() calls"
  - "Auto-suggest with override: auto-set on detection, but prevHeroIdRef guard prevents re-setting on subsequent ticks"

requirements-completed: [INT-01, INT-02]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 15 Plan 02: Hook Consolidation Summary

**Consolidated useGsiSync + useAutoRefresh into single useGameIntelligence hook with playstyle auto-suggest via HERO_PLAYSTYLE_MAP**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T00:20:42Z
- **Completed:** 2026-03-27T00:25:46Z
- **Tasks:** 2
- **Files modified:** 6 (1 created, 1 created test, 1 modified, 3 deleted)

## Accomplishments
- Single useGameIntelligence hook replaces both useGsiSync and useAutoRefresh with deterministic processing order
- Playstyle auto-suggest from HERO_PLAYSTYLE_MAP with PLAYSTYLE_OPTIONS[role][0] fallback
- 12 tests passing (9 adapted from useGsiSync + 3 new for playstyle auto-suggest)
- Old hooks deleted, zero dangling imports, full 163-test suite green

## Task Commits

Each task was committed atomically:

1. **Task 1: Create useGameIntelligence hook** - `21a0b52` (feat)
2. **Task 2: Wire App.tsx, create tests, delete old hooks** - `2e9e1ba` (feat)

## Files Created/Modified
- `prismlab/frontend/src/hooks/useGameIntelligence.ts` - Consolidated GSI intelligence hook (347 lines)
- `prismlab/frontend/src/hooks/useGameIntelligence.test.ts` - 12 tests covering hero detection, role inference, playstyle auto-suggest, item marking, cleanup
- `prismlab/frontend/src/App.tsx` - Replaced useGsiSync + useAutoRefresh with single useGameIntelligence call
- `prismlab/frontend/src/hooks/useGsiSync.ts` - DELETED
- `prismlab/frontend/src/hooks/useAutoRefresh.ts` - DELETED
- `prismlab/frontend/src/hooks/useGsiSync.test.ts` - DELETED

## Decisions Made
- Kept separate gsiStore.subscribe() and recommendationStore.subscribe() calls within the hook per D-02 to prevent cross-store write cascades
- suggestPlaystyle() called immediately after setRole() in the same synchronous block to avoid null playstyle flash (per Pitfall 15)
- Auto-suggest only fires on hero_id change (prevHeroIdRef guard), allowing user manual override to persist

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 15 fully complete (2/2 plans done)
- Store consolidation and TriggerEvent dedup are resolved
- Ready for Phase 16 (backend data cache) or Phase 17 (design retheme)

## Self-Check: PASSED

All created files exist. All deleted files confirmed removed. Both task commit hashes verified in git log.

---
*Phase: 15-store-consolidation-tech-debt*
*Completed: 2026-03-27*
