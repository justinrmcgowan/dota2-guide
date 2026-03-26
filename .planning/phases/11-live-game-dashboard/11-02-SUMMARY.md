---
phase: 11-live-game-dashboard
plan: 02
subsystem: ui
tags: [react, zustand, gsi, websocket, hooks, animation]

# Dependency graph
requires:
  - phase: 11-01
    provides: useAnimatedValue hook, findPurchasedKeys utility, neutralTiers utility
  - phase: 10-03
    provides: gsiStore, useWebSocket hook, GsiStatusIndicator
provides:
  - useGsiSync hook for cross-store GSI synchronization (gsiStore -> gameStore + recommendationStore)
  - LiveStatsBar component with animated gold/GPM/NW and KDA display
  - App.tsx mounts useGsiSync at root for global sync
affects: [11-03, 12-auto-adaptation]

# Tech tracking
tech-stack:
  added: []
  patterns: [zustand-subscribe-outside-render, ref-based-stale-closure-prevention, add-only-item-marking]

key-files:
  created:
    - prismlab/frontend/src/hooks/useGsiSync.ts
    - prismlab/frontend/src/hooks/useGsiSync.test.ts
    - prismlab/frontend/src/components/game/LiveStatsBar.tsx
    - prismlab/frontend/src/components/game/LiveStatsBar.test.tsx
  modified:
    - prismlab/frontend/src/components/layout/Sidebar.tsx
    - prismlab/frontend/src/App.tsx

key-decisions:
  - "Subscribe to gsiStore outside render cycle via useGsiStore.subscribe() to avoid cascading re-renders"
  - "Add-only item marking strategy: GSI marks items as purchased but never unmarks (prevents flicker on temporary inventory changes)"
  - "Role inference is best-effort heuristic returning null for ambiguous heroes (user selects manually)"

patterns-established:
  - "zustand-subscribe-outside-render: Use store.subscribe() in useEffect for cross-store sync without re-render cascade"
  - "ref-based-guard: Use useRef to track previous values (hero_id, gold, deaths) and skip redundant dispatches"

requirements-completed: [GSI-02, GSI-03, GSI-04, WS-02, WS-04]

# Metrics
duration: 5min
completed: 2026-03-26
---

# Phase 11 Plan 02: GSI Sync & Live Stats Summary

**Cross-store GSI synchronization hook with auto hero/role detection, item auto-marking, and animated gold/GPM/NW/KDA stats bar**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-26T18:57:53Z
- **Completed:** 2026-03-26T19:03:36Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- useGsiSync hook bridges gsiStore to gameStore (hero auto-detection, role inference) and recommendationStore (item auto-marking via findPurchasedKeys)
- LiveStatsBar displays gold/GPM/NW with smooth counting animation and KDA with Radiant/Dire colors, visible only when GSI is connected and game is in progress
- Color pulse effects on significant gold gains (+300g) and death events
- All 13 new tests passing, full suite 122/122 green, TypeScript clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Create useGsiSync hook with tests (TDD)** - `6d693e0` (test: RED), `2967c6b` (feat: GREEN)
2. **Task 2: Create LiveStatsBar component and wire into Sidebar and App** - `89aecd4` (feat)

## Files Created/Modified
- `prismlab/frontend/src/hooks/useGsiSync.ts` - Cross-store sync hook: gsiStore -> gameStore (hero/role) + recommendationStore (purchased items)
- `prismlab/frontend/src/hooks/useGsiSync.test.ts` - 9 tests covering hero detection, role inference, item marking, guards, cleanup
- `prismlab/frontend/src/components/game/LiveStatsBar.tsx` - Compact gold/GPM/NW/KDA display with counting animation and pulse effects
- `prismlab/frontend/src/components/game/LiveStatsBar.test.tsx` - 4 tests covering visibility guards and value rendering
- `prismlab/frontend/src/components/layout/Sidebar.tsx` - Added LiveStatsBar above GameStatePanel
- `prismlab/frontend/src/App.tsx` - Mounted useGsiSync(heroes) at app root

## Decisions Made
- Used `useGsiStore.subscribe()` in useEffect (outside render cycle) to prevent cascading re-renders when syncing across stores
- Add-only item marking: GSI marks items as purchased via togglePurchased but never unmarks them (prevents flickering on temporary inventory changes like selling/buying)
- Role inference uses a simple heuristic (Carry->1, Nuker->2, Initiator+Durable->3, Support+Disabler->4, Support->5) and returns null for ambiguous heroes, leaving role unselected for user choice

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Test isolation required careful store resetting: using `useGsiStore.setState({...}, true)` (replace mode) stripped action methods from the store, causing `updateLiveState is not a function` errors. Fixed by using partial setState without the replace flag.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- useGsiSync and LiveStatsBar are fully wired and tested
- Plan 11-03 (NeutralItemSection highlight + GameClock) can proceed -- it uses the same gsiStore data that is now properly synced
- Manual controls (GameStatePanel) remain fully functional below LiveStatsBar

---
*Phase: 11-live-game-dashboard*
*Completed: 2026-03-26*
