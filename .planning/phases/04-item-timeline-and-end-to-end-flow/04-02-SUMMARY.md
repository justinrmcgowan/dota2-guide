---
phase: 04-item-timeline-and-end-to-end-flow
plan: 02
subsystem: ui
tags: [react, typescript, tailwind, timeline, item-cards, skeleton, error-handling]

requires:
  - phase: 04-item-timeline-and-end-to-end-flow
    plan: 01
    provides: "Recommendation types, useRecommendationStore, useRecommendation hook, API client"
  - phase: 03-recommendation-engine
    provides: "Backend /api/recommend endpoint returning phased item recommendations with reasoning"
provides:
  - "ItemTimeline component rendering phased item recommendations with reasoning panels"
  - "ItemCard with Steam CDN portraits, priority borders, and click-to-expand reasoning"
  - "PhaseCard rendering phase headers, item rows, and expandable reasoning"
  - "DecisionTreeCard for situational branching item options"
  - "LoadingSkeleton with pulsing placeholders matching timeline layout"
  - "ErrorBanner for error and fallback states"
  - "MainPanel integration rendering timeline, skeleton, error, or empty state based on store"
affects: [05-mid-game-adaptation]

tech-stack:
  added: []
  patterns: [composite-key item selection across phases, priority-based border coloring, phase-specific color accents]

key-files:
  created:
    - prismlab/frontend/src/components/timeline/LoadingSkeleton.tsx
    - prismlab/frontend/src/components/timeline/ErrorBanner.tsx
    - prismlab/frontend/src/components/timeline/ItemCard.tsx
    - prismlab/frontend/src/components/timeline/PhaseCard.tsx
    - prismlab/frontend/src/components/timeline/DecisionTreeCard.tsx
    - prismlab/frontend/src/components/timeline/ItemTimeline.tsx
  modified:
    - prismlab/frontend/src/components/layout/MainPanel.tsx

key-decisions:
  - "ItemCard shows item name below portrait instead of gold cost because ItemRecommendation lacks gold_cost field"
  - "Phase-specific color accents: gray for starting, cyan for laning, amber for core, purple for late game"
  - "DecisionTreeCard filters items with non-null conditions for situational branching display"

patterns-established:
  - "Timeline component hierarchy: ItemTimeline > PhaseCard > ItemCard/DecisionTreeCard"
  - "ErrorBanner dual-mode: type=error with dismiss, type=fallback without dismiss"
  - "MainPanel state-driven rendering: loading > error > data > empty state priority chain"

requirements-completed: [DISP-01, DISP-02, DISP-03, DISP-04]

duration: 5min
completed: 2026-03-22
---

# Phase 04 Plan 02: Item Timeline UI Summary

**Phased item timeline with Steam CDN portraits, click-to-expand reasoning panels, situational decision trees, loading skeletons, and error/fallback banners integrated into MainPanel**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-22T00:00:00Z
- **Completed:** 2026-03-22T00:05:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 7

## Accomplishments
- Six timeline components rendering phased item recommendations with analytical reasoning
- Complete end-to-end flow working: draft inputs -> Get Item Build -> loading skeleton -> item timeline with reasoning
- Situational items displayed as branching decision tree cards with condition text
- Error and fallback banners with amber styling for graceful degradation
- MainPanel rewritten as central hub routing between loading, error, data, and empty states

## Task Commits

Each task was committed atomically:

1. **Task 1: Create timeline components** - `1aba266` (feat)
2. **Task 2: Integrate timeline into MainPanel** - `476ece5` (feat)
3. **Task 3: Visual verification checkpoint** - No commit (human-verify, approved)

## Files Created/Modified
- `prismlab/frontend/src/components/timeline/LoadingSkeleton.tsx` - Pulsing skeleton with 4 phase card placeholders matching timeline layout
- `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` - Amber alert bar (error with dismiss) and subtle fallback banner
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` - 48px Steam CDN portrait with priority border (cyan/amber/purple), click-to-select
- `prismlab/frontend/src/components/timeline/PhaseCard.tsx` - Phase header with color accent, horizontal item row, expandable reasoning panel
- `prismlab/frontend/src/components/timeline/DecisionTreeCard.tsx` - Branching card with condition text and situational item options
- `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` - Vertical stack of PhaseCards with optional strategy summary
- `prismlab/frontend/src/components/layout/MainPanel.tsx` - Rewritten to render timeline/skeleton/error/empty based on recommendation state

## Decisions Made
- ItemCard displays item name (formatted: underscores to spaces, title case) below portrait instead of gold cost, because the ItemRecommendation type lacks a gold_cost field. The phase-level gold_budget is shown in the PhaseCard header instead.
- Phase-specific color accents for visual distinction: gray-400 for starting, cyan for laning, amber for core, purple for late game.
- MainPanel uses priority-based rendering: error banner first (with data still showing below if partial), then loading skeleton, then data with optional fallback banner, then empty state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ItemCard shows item name instead of gold cost**
- **Found during:** Task 1 (ItemCard creation)
- **Issue:** Plan specified gold cost below item portrait, but ItemRecommendation interface has no gold_cost field -- only item_name, reasoning, priority, and conditions
- **Fix:** Rendered formatted item_name (underscores replaced with spaces, title-cased) below the portrait instead of gold cost. Phase-level gold_budget shown in PhaseCard header provides budget context.
- **Files modified:** prismlab/frontend/src/components/timeline/ItemCard.tsx
- **Verification:** TypeScript compilation passes, item names display correctly
- **Committed in:** 1aba266 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor visual difference -- item name below portrait instead of per-item gold cost. Phase gold budget still visible. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete end-to-end recommendation flow operational: draft inputs -> API call -> phased timeline with reasoning
- Phase 5 (Mid-Game Adaptation) can build on timeline components: add click-to-mark-purchased on ItemCard, add re-evaluate flow
- All DISP requirements for Phase 4 fulfilled

## Self-Check: PASSED

All 6 created files and 1 modified file verified present on disk. Both task commits (1aba266, 476ece5) verified in git log.

---
*Phase: 04-item-timeline-and-end-to-end-flow*
*Completed: 2026-03-22*
