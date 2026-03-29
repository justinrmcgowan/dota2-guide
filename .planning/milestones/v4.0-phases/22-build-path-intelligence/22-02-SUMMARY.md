---
phase: 22-build-path-intelligence
plan: "02"
subsystem: frontend-timeline
tags: [build-path, component-strip, affordability, react, typescript]
dependency_graph:
  requires: [22-01]
  provides: [BuildPathSteps, buildPathMap, build_paths-frontend-types]
  affects:
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/components/timeline/BuildPathSteps.tsx
    - prismlab/frontend/src/components/timeline/PhaseCard.tsx
    - prismlab/frontend/src/components/timeline/ItemTimeline.tsx
tech_stack:
  added: []
  patterns: [useMemo-map-pattern, post-render-enrichment-display, affordability-highlight]
key_files:
  created:
    - prismlab/frontend/src/components/timeline/BuildPathSteps.tsx
  modified:
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/components/timeline/PhaseCard.tsx
    - prismlab/frontend/src/components/timeline/ItemTimeline.tsx
decisions:
  - buildPathMap useMemo mirrors timingDataMap pattern — O(1) per-item lookup keyed by item_name
  - BuildPathSteps returns null for empty steps arrays — base items with no components show reasoning only
  - currentGold flows through ItemTimeline -> PhaseCard -> BuildPathSteps to drive affordability highlight
metrics:
  duration: "5 min"
  completed_date: "2026-03-27"
  tasks_completed: 2
  files_modified: 4
---

# Phase 22 Plan 02: Build Path Intelligence — Frontend Component Strip Summary

## One-Liner

Frontend build path UI added: BuildPathSteps component renders ordered component icons with position numbers, gold costs, and GSI affordability highlights inside PhaseCard's existing selectedItem reasoning panel.

## What Was Built

### Task 1: TypeScript Interface Extensions (recommendation.ts)

- Added `ComponentStep` interface: item_name (internal_name for Steam CDN), item_id, cost (nullable), reason, position (1-based)
- Added `BuildPathResponse` interface: item_name, steps array, build_path_notes paragraph
- Extended `RecommendResponse` with `build_paths: BuildPathResponse[]` field to match backend schema from Plan 01

### Task 2: BuildPathSteps Component and Wiring (3 files)

**BuildPathSteps.tsx (new file):**
- Renders `build_path_notes` paragraph above the component strip in italic `text-on-surface-variant` text (PATH-02)
- Renders horizontal strip of component icons from `steps` array, ordered by `position` (PATH-01)
- Each component shows: position number badge, 32x32 item image from Steam CDN via `itemImageUrl()`, cost in gold
- Affordability highlight: `text-radiant` (#6aff97) when `currentGold >= step.cost`, `text-on-surface-variant` otherwise (PATH-03)
- Returns null early when steps array is empty — base items show no component section

**PhaseCard.tsx:**
- Added `BuildPathResponse` import and `BuildPathSteps` import
- Added `buildPathMap?: Map<string, BuildPathResponse>` to `PhaseCardProps` interface
- Added `buildPathMap = new Map()` default in destructured props
- Extended `selectedItem` reasoning panel to call `buildPathMap.get(selectedItem.item_name)` and render `<BuildPathSteps>` when steps exist; passes `currentGold` through for GSI affordability

**ItemTimeline.tsx:**
- Added `BuildPathResponse` to the recommendation type import
- Added `buildPathMap` useMemo after existing `timingDataMap` — same Map keying pattern, keyed by `bp.item_name`
- Passes `buildPathMap` to all `PhaseCard` instances in the phases render loop

## Verification

All checks passed:
- TypeScript strict-mode compile: 0 errors
- `BuildPathSteps` present in PhaseCard.tsx
- `buildPathMap` present in ItemTimeline.tsx
- `text-radiant` present in BuildPathSteps.tsx
- `build_paths` present in recommendation.ts

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 12c6d58 | feat(22-02): add ComponentStep, BuildPathResponse interfaces and build_paths to RecommendResponse |
| 2 | 485e659 | feat(22-02): create BuildPathSteps component and wire into PhaseCard and ItemTimeline |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All data flows from the real `build_paths` backend field populated by Plan 01's `_enrich_build_paths` enrichment step. No hardcoded values or placeholder text.

## Self-Check: PASSED
