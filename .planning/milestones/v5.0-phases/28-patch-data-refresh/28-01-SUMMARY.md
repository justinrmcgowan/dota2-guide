---
phase: 28-patch-data-refresh
plan: 01
subsystem: database, testing
tags: [seed, upsert, pytest, patch-741, item-data]

# Dependency graph
requires:
  - phase: 19-data-architecture
    provides: DataCache, HeroAbilityData model, seed pipeline
provides:
  - Fixed seed.py upsert for HeroAbilityData (no more IntegrityError on re-seed)
  - 7.41 test fixtures (Shiva's 4500g, Blade Mail 2300g, Splintmail 950g)
  - Automated 7.41 data correctness test suite (16 tests)
affects: [28-02-PLAN, future-patch-refreshes]

# Tech tracking
tech-stack:
  added: []
  patterns: [session.merge upsert for idempotent seed, parametrized skip-marked new-item tests]

key-files:
  created:
    - prismlab/backend/tests/test_patch_741.py
  modified:
    - prismlab/backend/data/seed.py
    - prismlab/backend/tests/conftest.py

key-decisions:
  - "session.merge() for HeroAbilityData upserts -- matches refresh.py pattern, fixes IntegrityError on container restart"
  - "New-item existence tests skip-marked until production re-seed -- validates after deploy, not before"

patterns-established:
  - "Patch validation pattern: parametrized skip-marked tests for new items, immediate tests for cost changes and removed items"

requirements-completed: [PATCH-01, PATCH-02]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 28 Plan 01: Seed Upsert Fix and 7.41 Data Tests Summary

**Fixed HeroAbilityData IntegrityError via session.merge() upsert, updated test fixtures for 7.41 costs, created 16-test regression suite for patch data correctness**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T18:33:29Z
- **Completed:** 2026-03-28T18:37:57Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Fixed critical seed.py IntegrityError that crashed containers on restart (session.add -> session.merge for HeroAbilityData)
- Updated test fixtures to reflect 7.41 costs: Shiva's Guard 4500g, Blade Mail 2300g, Splintmail 950g
- Created comprehensive test_patch_741.py with 16 tests covering new items, removed items, cost changes, rules integrity, prompt budget, and EXCLUDED_ITEMS audit
- All 279 existing tests pass (8 new-item tests correctly skip-marked for post-re-seed validation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix seed.py upsert bug and update test fixtures** - `5154470` (fix)
2. **Task 2: Create automated 7.41 data correctness test suite** - `0389c25` (test)

## Files Created/Modified
- `prismlab/backend/data/seed.py` - Changed session.add() to session.merge() for HeroAbilityData (line 151)
- `prismlab/backend/tests/conftest.py` - Shiva's Guard cost 4750->4500, added Splintmail and Blade Mail fixtures
- `prismlab/backend/tests/test_patch_741.py` - 16-test suite: item existence, costs, cornucopia removal, rules integrity, prompt budget, EXCLUDED_ITEMS

## Decisions Made
- Used `session.merge()` for HeroAbilityData upserts to match the existing pattern in `refresh.py` -- this is the idiomatic SQLAlchemy way to handle INSERT-or-UPDATE on primary key
- New-item existence tests are `@pytest.mark.skip`-marked rather than removed -- they serve as a smoke test after production re-seed and document the expected 7.41 item catalog
- Added `TestPatch741ExcludedItems` beyond what plan specified -- validates EXCLUDED_ITEMS set does not wrongly exclude purchasable 7.41 items (Rule 2: missing critical validation)

## Deviations from Plan

None - plan executed exactly as written. The additional TestPatch741ExcludedItems test class was explicitly called for in the plan's behavior section ("EXCLUDED_ITEMS set does not contain any valid purchasable 7.41 items").

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- seed.py is now safe for container restarts and re-seeds (merge instead of add)
- Test fixtures are 7.41-ready for Plan 02 (rules engine audit and system prompt updates)
- After production re-seed, unskip the 8 parametrized new-item tests in test_patch_741.py to validate live data

---
*Phase: 28-patch-data-refresh*
*Completed: 2026-03-28*
