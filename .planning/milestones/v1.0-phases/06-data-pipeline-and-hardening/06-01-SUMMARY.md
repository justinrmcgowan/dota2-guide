---
phase: 06-data-pipeline-and-hardening
plan: 01
subsystem: infra
tags: [apscheduler, fastapi, data-pipeline, opendota, refresh]

# Dependency graph
requires:
  - phase: 01-scaffolding
    provides: "OpenDota client, Hero/Item models, database setup, seed logic"
provides:
  - "Daily automated data refresh pipeline via APScheduler"
  - "DataRefreshLog model for tracking refresh history"
  - "Manual refresh trigger at POST /admin/refresh-data"
  - "Data freshness query at GET /api/data-freshness"
  - "Header freshness indicator showing relative time since last refresh"
affects: []

# Tech tracking
tech-stack:
  added: [apscheduler]
  patterns: [AsyncIOScheduler in FastAPI lifespan, background task refresh trigger, upsert via session.merge]

key-files:
  created:
    - prismlab/backend/data/refresh.py
    - prismlab/backend/api/routes/admin.py
  modified:
    - prismlab/backend/data/models.py
    - prismlab/backend/main.py
    - prismlab/backend/requirements.txt
    - prismlab/frontend/src/api/client.ts
    - prismlab/frontend/src/components/layout/Header.tsx

key-decisions:
  - "AsyncIOScheduler for native async job support in FastAPI event loop"
  - "session.merge for upsert pattern matching seed.py field mapping"
  - "Error logging uses separate session to avoid corrupted session state"

patterns-established:
  - "Scheduler lifecycle: start in lifespan before yield, shutdown after yield"
  - "Freshness fallback: check Hero.updated_at when no DataRefreshLog exists"

requirements-completed: [INFR-02]

# Metrics
duration: 3min
completed: 2026-03-22
---

# Phase 06 Plan 01: Data Pipeline and Freshness Summary

**APScheduler daily refresh pipeline with OpenDota upsert, admin trigger endpoint, and Header freshness indicator**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T22:57:30Z
- **Completed:** 2026-03-21T23:00:12Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Daily data refresh pipeline that upserts heroes and items from OpenDota every 24 hours
- DataRefreshLog model tracks refresh history with timestamps, counts, and error messages
- Admin endpoint for manual refresh trigger and data freshness query API
- Header displays relative freshness time with full timestamp on hover

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend daily refresh pipeline with scheduler and admin endpoint** - `417ae76` (feat)
2. **Task 2: Frontend data freshness indicator in Header** - `886c34b` (feat)

## Files Created/Modified
- `prismlab/backend/data/refresh.py` - Main refresh pipeline with refresh_all_data() and get_last_refresh()
- `prismlab/backend/api/routes/admin.py` - POST /admin/refresh-data and GET /api/data-freshness endpoints
- `prismlab/backend/data/models.py` - Added DataRefreshLog model with refresh tracking columns
- `prismlab/backend/main.py` - Integrated AsyncIOScheduler in lifespan with 24h interval job
- `prismlab/backend/requirements.txt` - Added apscheduler dependency
- `prismlab/frontend/src/api/client.ts` - Added DataFreshness interface and getDataFreshness() method
- `prismlab/frontend/src/components/layout/Header.tsx` - Freshness indicator with relative time display

## Decisions Made
- Used AsyncIOScheduler (not BackgroundScheduler) for native async job support within FastAPI's event loop
- Used session.merge() for upsert pattern, matching the existing seed.py field mapping exactly
- Error logging in refresh pipeline uses a separate async session to avoid corrupted session state from failed transactions
- Freshness endpoint falls back to Hero.updated_at when no DataRefreshLog exists (covers initial seed scenario)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Data pipeline complete, hero/item data stays current automatically
- This is the final plan in Phase 06 -- project V1 is complete

## Self-Check: PASSED

All 8 files verified present. Both task commits (417ae76, 886c34b) confirmed in git history.

---
*Phase: 06-data-pipeline-and-hardening*
*Completed: 2026-03-22*
