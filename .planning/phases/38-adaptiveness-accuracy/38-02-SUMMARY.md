---
phase: 38-adaptiveness-accuracy
plan: 02
subsystem: api, ui
tags: [fastapi, sqlalchemy, react, match-analytics, accuracy-metrics]

# Dependency graph
requires:
  - phase: 38-01
    provides: match logging with follow_rate and MatchRecommendation model
provides:
  - follow_win_rate and deviate_win_rate on /match-stats endpoint
  - flagged items detection for prompt tuning
  - Accuracy Insights dashboard section in Match History
affects: [prompt-tuning, recommendation-engine, match-history]

# Tech tracking
tech-stack:
  added: []
  patterns: [sqlalchemy case() for conditional aggregation, null-safe conditional rendering]

key-files:
  created: []
  modified:
    - prismlab/backend/api/routes/match_history.py
    - prismlab/frontend/src/types/matchLog.ts
    - prismlab/frontend/src/pages/MatchHistory.tsx

key-decisions:
  - "Follow threshold >= 0.7, deviate threshold < 0.4 -- chosen to create clear separation between behavior buckets"
  - "Flagged items exclude luxury priority -- luxury items are optional by definition and low purchase rate is expected"
  - "Flagged items require 5+ recommendations minimum -- avoids noise from rarely-seen items"

patterns-established:
  - "Accuracy bucket queries: follow_rate >= 0.7 for follow, < 0.4 for deviate"
  - "Flagged item detection: core/situational items recommended 5+ times with < 30% purchase rate"

requirements-completed: [ADAPT-03, ADAPT-04, ADAPT-05]

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 38 Plan 02: Accuracy Insights Summary

**Follow vs deviate win rate comparison and flagged low-purchase items on Match History dashboard via enhanced /match-stats endpoint**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-31T09:51:15Z
- **Completed:** 2026-03-31T09:54:41Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Enhanced /match-stats endpoint with follow_win_rate (follow_rate >= 0.7) and deviate_win_rate (follow_rate < 0.4) with per-bucket game counts
- Added flagged items detection: core/situational items recommended 5+ times with < 30% purchase rate, sorted worst-first
- Built Accuracy Insights section in Match History dashboard showing follow vs deviate win rate cards, follow advantage delta, and flagged items table with item images

## Task Commits

Each task was committed atomically:

1. **Task 1: Enhance /match-stats with follow/deviate win rates and flagged items** - `e4da594` (feat)
2. **Task 2: Update frontend types and MatchHistory dashboard with accuracy section** - `21ce3dd` (feat)

## Files Created/Modified
- `prismlab/backend/api/routes/match_history.py` - Added FlaggedItemResponse schema, extended MatchStatsResponse, added follow/deviate/flagged queries
- `prismlab/frontend/src/types/matchLog.ts` - Added FlaggedItem interface, extended MatchStatsResponse with accuracy fields
- `prismlab/frontend/src/pages/MatchHistory.tsx` - Added Accuracy Insights section with win rate comparison cards and flagged items table

## Decisions Made
- Follow threshold >= 0.7 and deviate threshold < 0.4 provide clear behavioral separation (games in the 0.4-0.7 range are excluded from both buckets as ambiguous)
- Luxury-priority items excluded from flagging since low purchase rate is expected for optional luxury picks
- Minimum 5 recommendations required before an item gets flagged to avoid noise from rare items

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all data is wired from the backend endpoint through to the UI rendering.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Accuracy metrics are live on the Match History dashboard
- Flagged items surface prompt tuning opportunities for the recommendation engine
- Follow advantage metric provides clear proof-of-value signal to users

---
*Phase: 38-adaptiveness-accuracy*
*Completed: 2026-03-31*
