---
phase: 04-item-timeline-and-end-to-end-flow
plan: 03
subsystem: api, ui
tags: [pydantic, fastapi, react, typescript, sqlalchemy, gold-cost]

# Dependency graph
requires:
  - phase: 04-item-timeline-and-end-to-end-flow (plan 01)
    provides: ItemRecommendation schema and recommend endpoint
  - phase: 04-item-timeline-and-end-to-end-flow (plan 02)
    provides: ItemCard component and timeline UI
provides:
  - gold_cost field on ItemRecommendation across backend schema, recommender, frontend type, and ItemCard display
affects: [05-mid-game-adaptation, 06-polish]

# Tech tracking
tech-stack:
  added: []
  patterns: [model_copy with update for enriching validated items, cost_map dict for combined ID validation and cost lookup]

key-files:
  created: []
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/recommender.py
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/components/timeline/ItemCard.tsx

key-decisions:
  - "gold_cost populated via model_copy during _validate_item_ids -- zero additional DB queries"
  - "cost_map dict replaces valid_ids set for dual-purpose ID validation and cost lookup"
  - "ItemCard shows raw gold number (no comma formatting) since Dota players read raw numbers"

patterns-established:
  - "Enrichment during validation: server-side field population piggybacks on existing DB queries"

requirements-completed: [DISP-02]

# Metrics
duration: 2min
completed: 2026-03-21
---

# Phase 04 Plan 03: Gold Cost Gap Closure Summary

**Per-item gold cost from Item.cost DB column through backend ItemRecommendation schema to frontend ItemCard amber text display**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T22:10:58Z
- **Completed:** 2026-03-21T22:12:42Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added gold_cost field to ItemRecommendation Pydantic model (optional, default null)
- Modified _validate_item_ids to query Item.cost alongside Item.id with zero additional DB calls
- Added gold_cost to TypeScript ItemRecommendation interface
- ItemCard displays gold cost in amber text below portrait, falls back to item name when null

## Task Commits

Each task was committed atomically:

1. **Task 1: Add gold_cost to backend schema and populate in recommender** - `55b6c30` (feat)
2. **Task 2: Add gold_cost to frontend type and display in ItemCard** - `7fca9aa` (feat)

## Files Created/Modified
- `prismlab/backend/engine/schemas.py` - Added gold_cost: int | None = None to ItemRecommendation
- `prismlab/backend/engine/recommender.py` - Changed select(Item.id) to select(Item.id, Item.cost), built cost_map dict, populate gold_cost via model_copy
- `prismlab/frontend/src/types/recommendation.ts` - Added gold_cost: number | null to ItemRecommendation interface
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` - Conditional render: gold_cost when present, formatItemName fallback when null

## Decisions Made
- Used cost_map (dict[int, int | None]) instead of valid_ids (set[int]) to serve dual purpose: ID validation and cost lookup in one data structure
- gold_cost appears in LLM_OUTPUT_SCHEMA as optional/defaulted field (unavoidable since LLMRecommendation nests ItemRecommendation), but LLM won't populate it since it's not required
- Raw number display without comma formatting matches Dota UI conventions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DISP-02 gap is closed: gold cost flows end-to-end from Item DB table to ItemCard display
- Phase 04 is fully complete with all 3 plans done
- Ready to proceed to Phase 05 (mid-game adaptation)

## Self-Check: PASSED

All 4 modified files verified on disk. Both task commits (55b6c30, 7fca9aa) verified in git log.

---
*Phase: 04-item-timeline-and-end-to-end-flow*
*Completed: 2026-03-21*
