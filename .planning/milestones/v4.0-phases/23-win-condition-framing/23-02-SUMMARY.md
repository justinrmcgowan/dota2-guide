---
phase: 23-win-condition-framing
plan: "02"
subsystem: frontend-ui
tags: [win-condition, typescript, react, tailwind, zustand, item-timeline]

dependency_graph:
  requires:
    - phase: 23-01
      provides: WinConditionResponse Pydantic model, win_condition on RecommendResponse, all_opponents on RecommendRequest
  provides:
    - WinConditionResponse TypeScript interface
    - all_opponents field on RecommendRequest TypeScript type
    - win_condition field on RecommendResponse TypeScript type
    - WinConditionBadge component (allied gold pill, enemy dire-red pill, opacity-based confidence)
    - ItemTimeline renders WinConditionBadge above strategy text when win_condition present
    - useRecommendation sends full 5-hero enemy team as all_opponents
  affects: [ItemTimeline.tsx, useRecommendation.ts, WinConditionBadge.tsx, recommendation.ts]

tech-stack:
  added: []
  patterns:
    - "WinConditionBadge uses opacity-100/75/50 for confidence — visual encoding without text labels"
    - "Edge case: WinConditionBadge renders even when overall_strategy is absent (fallback mode)"

key-files:
  created:
    - prismlab/frontend/src/components/timeline/WinConditionBadge.tsx
  modified:
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/components/timeline/ItemTimeline.tsx
    - prismlab/frontend/src/hooks/useRecommendation.ts

key-decisions:
  - "Triangle glyphs (HTML entity &#9650;/&#9660;) instead of SVG icons — zero-dependency directional indicators for allied/enemy"
  - "Badge absent when win_condition is null/undefined — zero regressions to existing ItemTimeline rendering"
  - "all_opponents uses game.opponents (full 5 slots filtered for nulls); lane_opponents uses game.laneOpponents — two distinct concerns"

patterns-established:
  - "Badge confidence: opacity-100 high, opacity-75 medium, opacity-50 low — consistent with DESIGN.md show-dont-tell principle"
  - "text-secondary (gold) for allied archetype, text-dire (dire red) for enemy archetype — matches design token semantics"

requirements-completed: [WCON-02, WCON-03, WCON-04]

duration: 6min
completed: 2026-03-27
---

# Phase 23 Plan 02: Win Condition Frontend Display Summary

**WinConditionBadge component displaying allied (gold) and enemy (dire-red) archetype pills above ItemTimeline strategy text, with opacity-based confidence encoding and full enemy team wiring via all_opponents.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-27T21:40:00Z
- **Completed:** 2026-03-27T21:46:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- TypeScript interfaces for WinConditionResponse added to recommendation.ts, matching backend Pydantic model field-for-field
- WinConditionBadge component renders allied archetype in gold (text-secondary) and enemy in dire red (text-dire), confidence via opacity only
- ItemTimeline integrates WinConditionBadge between "Strategy" label and overall_strategy paragraph; handles fallback mode edge case
- useRecommendation now sends all_opponents (full 5-hero enemy team filtered for nulls) satisfying WCON-04
- 163 frontend tests pass, zero TypeScript errors

## Task Commits

1. **Task 1: TypeScript types + WinConditionBadge component** - `3f384df` (feat)
2. **Task 2: Wire WinConditionBadge into ItemTimeline + all_opponents into useRecommendation** - `444a246` (feat)

## Files Created/Modified

- `prismlab/frontend/src/types/recommendation.ts` - Added WinConditionResponse interface, all_opponents to RecommendRequest, win_condition to RecommendResponse
- `prismlab/frontend/src/components/timeline/WinConditionBadge.tsx` - New component: allied/enemy archetype pills with opacity confidence encoding
- `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` - Import and render WinConditionBadge above strategy text; edge-case for absent overall_strategy
- `prismlab/frontend/src/hooks/useRecommendation.ts` - Added all_opponents field using game.opponents.filter(Boolean)

## Decisions Made

- Used HTML entity triangle glyphs (&#9650; allied, &#9660; enemy) rather than SVG icons — lightweight directional indicators, no extra dependencies, no emojis (CLAUDE.md rule)
- Badge renders conditionally on data.win_condition truthiness — null/undefined = no rendering, zero regressions
- Confidence is visual-only (opacity), not text labels — matches "show, don't tell" from DESIGN.md

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — WinConditionBadge receives live data from backend RecommendResponse.win_condition, which is populated by the post-LLM enrichment from 23-01. No placeholder data.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 23 (win-condition-framing) is complete end-to-end: backend classifier (23-01) + frontend display (23-02)
- Win condition archetype badges are visible to users above strategy text on every recommendation that reaches the 3-hero threshold
- Phase 23 was the final phase of v4.0 Coaching Intelligence milestone

## Self-Check: PASSED
