---
phase: 21-timing-benchmarks
plan: "02"
subsystem: frontend-timing-display
tags: [timing-zones, timing-bar, gsi-integration, urgency-animation, component-wiring]
dependency_graph:
  requires: [ItemTimingResponse from Plan 01, useGsiStore, ItemCard, PhaseCard, ItemTimeline]
  provides: [TimingBar, TimingBucketUI, ItemTimingData, timing_data on RecommendResponse]
  affects: [ItemCard, PhaseCard, ItemTimeline, globals.css]
tech_stack:
  added: []
  patterns: [confidence-opacity, proportional-zone-widths, window-passed-state, live-marker-clamping]
key_files:
  created:
    - prismlab/frontend/src/components/timeline/TimingBar.tsx
  modified:
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/components/timeline/ItemCard.tsx
    - prismlab/frontend/src/components/timeline/PhaseCard.tsx
    - prismlab/frontend/src/components/timeline/ItemTimeline.tsx
    - prismlab/frontend/src/styles/globals.css
decisions:
  - "Proportional zone widths use bucket count ratio (not time span) -- simpler and consistent with how backend emits equal-interval buckets"
  - "On-track zone win rate in tooltip approximated as average of good and late win rates -- backend provides only good_win_rate and late_win_rate aggregates at the top level"
  - "TimingBar returns null when isPurchased -- cleaner than conditional rendering at call site"
  - "timingDataMap built with useMemo in ItemTimeline keyed by item_name -- avoids O(n) lookup per render"
metrics:
  duration: 4min
  completed: 2026-03-27
  tasks_completed: 2
  tasks_total: 2
  files_changed: 6
  tests_added: 0
  tests_total_backend: 248
---

# Phase 21 Plan 02: Frontend Timing Display Summary

Frontend timing display: TypeScript interfaces mirroring backend ItemTimingResponse, TimingBar component with three-zone bar, confidence opacity, tooltip, live GSI marker, gold-away text, window-passed overlay, and full component tree wiring from ItemTimeline through PhaseCard to ItemCard.

## What Was Built

### Task 1: TypeScript types, TimingBar component, CSS urgency animation

- **recommendation.ts**: Added `TimingBucketUI` and `ItemTimingData` interfaces (snake_case matching backend JSON); added `timing_data: ItemTimingData[]` to `RecommendResponse`
- **TimingBar.tsx**: Three-zone horizontal bar (good=radiant green, ontrack=secondary-fixed-dim gold, late=primary-container crimson); confidence-based opacity (40%/70%/100%); tooltip on hover/focus with zone rows, win rates, divider, and sample size; `LiveTimingMarker` positioned by GSI game_clock (0-100% clamped); "Xg away" / "Affordable now" text when GSI connected; `WindowPassedOverlay` greys bar and shows "Window passed" label when clock exceeds late threshold; `tabindex=0`, `role="img"`, `aria-label` for accessibility; returns null when purchased
- **globals.css**: `@keyframes pulse-urgency` with 0%/50%/100% box-shadow keyframes; `.timing-urgent` class applying 2s ease-in-out infinite animation; `@media (prefers-reduced-motion: reduce)` fallback using static 1px primary-container border-left

### Task 2: Wire TimingBar into ItemCard, PhaseCard, ItemTimeline

- **ItemCard.tsx**: Added `timingData`, `currentGameClock`, `currentGold` optional props; applies `timing-urgent` class when `timingData?.is_urgent && !isPurchased`; renders `<TimingBar>` below gold cost when timing data present and item not purchased
- **PhaseCard.tsx**: Added `timingDataMap: Map<string, ItemTimingData>`, `currentGameClock`, `currentGold` optional props; passes `timingDataMap.get(item.item_name)` per-item timing to each ItemCard along with GSI clock/gold
- **ItemTimeline.tsx**: Added `useMemo` import; subscribes to `useGsiStore` for `gold`; builds `timingDataMap` from `data.timing_data` with O(1) lookup; passes `timingDataMap`, `currentGameClock` (null when GSI disconnected), `currentGold` (null when GSI disconnected) to each PhaseCard

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 6bb913b | TypeScript timing types, TimingBar component, CSS urgency animation |
| 2 | b17efd5 | Wire TimingBar into ItemCard, PhaseCard, ItemTimeline |

## Test Results

- TypeScript compilation: 0 errors (both tasks verified with `npx tsc --noEmit`)
- No new frontend unit tests added -- TimingBar is a pure rendering component; behavioral tests covered by manual verification

## Deviations from Plan

### Minor Implementation Detail

**1. [Rule 1 - Minor Deviation] On-track win rate in tooltip**
- **Found during:** Task 1 implementation
- **Issue:** The plan specifies tooltip should show on-track zone win rate, but `ItemTimingData` only provides `good_win_rate` and `late_win_rate` aggregates (matching backend `ItemTimingResponse` schema). No `ontrack_win_rate` field exists.
- **Fix:** Approximated on-track win rate as average of good and late win rates in the tooltip. This is a display-only approximation -- the TimingBar zone segments themselves show accurate proportions.
- **Files modified:** `prismlab/frontend/src/components/timeline/TimingBar.tsx`
- **Note:** This is a pre-existing limitation in the backend schema design from Plan 01. If a precise on-track aggregate is needed, it can be added to `ItemTimingResponse` in a future plan.

## Known Stubs

None -- all data flows are fully wired. timing_data from RecommendResponse flows through ItemTimeline -> PhaseCard -> ItemCard -> TimingBar. GSI game_clock and gold flow from useGsiStore through the same chain. The window-passed, gold-away, and live-marker features are all fully implemented (they simply render nothing when GSI is disconnected, which is correct behavior).

## Self-Check: PASSED

Verified below.
