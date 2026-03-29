---
phase: 19-data-foundation-prompt-architecture
plan: 01
subsystem: database, api
tags: [opendota, sqlalchemy, abilities, item-timings, test-scaffolds]

# Dependency graph
requires:
  - phase: 16-backend-data-cache
    provides: DataCache singleton with frozen dataclasses and atomic swap pattern
provides:
  - 3 new OpenDotaClient fetch methods (abilities, hero_abilities, item_timings)
  - HeroAbilityData and ItemTimingData SQLAlchemy models
  - Test fixtures with ability data for heroes 1 and 3, timing data for hero 1
  - 15 failing test scaffolds for DataCache extensions (Plan 02 target)
affects: [19-02, 19-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One DB row per hero for JSON blob storage (abilities, timings)"
    - "Test scaffolds written before implementation (Nyquist rule)"

key-files:
  created:
    - prismlab/backend/tests/test_cache.py
  modified:
    - prismlab/backend/data/opendota_client.py
    - prismlab/backend/data/models.py
    - prismlab/backend/tests/conftest.py

key-decisions:
  - "One row per hero for timing data (not per hero+item pair) -- matches one API call = one DB write pattern"
  - "games and wins stored as strings in test fixtures to match real OpenDota API response format"

patterns-established:
  - "Nyquist test scaffolds: tests import types that don't exist yet, fail with ImportError until implementation plan"

requirements-completed: [DATA-01, DATA-02, DATA-03]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 19 Plan 01: Data Foundation Summary

**3 OpenDota fetch methods + 2 SQLAlchemy models + 15 test scaffolds for ability metadata and item timing benchmarks**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T05:40:02Z
- **Completed:** 2026-03-27T05:45:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added fetch_abilities(), fetch_hero_abilities(), and fetch_item_timings(hero_id) to OpenDotaClient following existing pattern
- Created HeroAbilityData and ItemTimingData SQLAlchemy models with JSON columns and hero_id unique constraints
- Seeded test ability data for Anti-Mage (4 abilities) and Crystal Maiden (3 abilities) in conftest.py
- Seeded test timing data for Anti-Mage (bfury 4 buckets, manta 3 buckets) with string games/wins matching real API
- Created test_cache.py with 15 comprehensive test scaffolds covering AbilityCached, TimingBucket, DataCache loading, and atomic swap coherence

## Task Commits

Each task was committed atomically:

1. **Task 1: Add OpenDota fetch methods and SQLAlchemy models** - `a7dd7ba` (feat)
2. **Task 2: Extend test fixtures and create test scaffolds** - `b227e64` (test)

## Files Created/Modified
- `prismlab/backend/data/opendota_client.py` - Added 3 new async fetch methods for abilities and timing endpoints
- `prismlab/backend/data/models.py` - Added HeroAbilityData and ItemTimingData models with JSON columns
- `prismlab/backend/tests/conftest.py` - Extended test_db_setup with ability and timing seed data
- `prismlab/backend/tests/test_cache.py` - 15 test scaffolds for DataCache extensions (fail until Plan 02)

## Decisions Made
- One row per hero for timing data (JSON blob stores all items per hero ~5KB) instead of per hero+item pair -- matches "one API call = one DB write" and simplifies stale-while-revalidate
- Test fixture timing data uses string types for games/wins fields to match real OpenDota API response format
- Test scaffolds intentionally import AbilityCached and TimingBucket from data.cache which don't exist yet -- tests fail with ImportError as designed

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 6 pre-existing test failures in test_context_builder.py (TestSystemPromptAllyRules, TestSystemPromptNeutralRules) -- these check system prompt content that was restructured in prior phases and are unrelated to this plan's changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- OpenDotaClient fetch methods ready for Plan 02 to call during DataCache loading
- HeroAbilityData and ItemTimingData models ready for SQLAlchemy create_all
- Test fixtures seeded and test scaffolds ready to validate Plan 02 DataCache extensions
- All 15 tests expected to pass once Plan 02 implements AbilityCached, TimingBucket, and DataCache methods

## Self-Check: PASSED

All 4 files verified present. Both task commits (a7dd7ba, b227e64) verified in git log.

---
*Phase: 19-data-foundation-prompt-architecture*
*Completed: 2026-03-27*
