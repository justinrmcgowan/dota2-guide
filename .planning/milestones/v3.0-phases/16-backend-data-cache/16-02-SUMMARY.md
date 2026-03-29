---
phase: 16-backend-data-cache
plan: 02
subsystem: api, engine, database
tags: [datacache, performance, hot-path, invalidation, fastapi, sqlalchemy]

# Dependency graph
requires:
  - phase: 16-backend-data-cache plan 01
    provides: DataCache class, RulesEngine refactored to accept DataCache
provides:
  - ContextBuilder consuming DataCache for all hero/item lookups (zero DB queries on hot path)
  - HybridRecommender._validate_item_ids using cache instead of DB
  - /api/heroes and /api/items served from cache with zero DB queries
  - Coordinated three-layer cache invalidation (DataCache -> RulesEngine auto -> ResponseCache.clear)
  - Lifespan cache loading after seed (no empty-cache race)
  - ResponseCache.clear() method for full invalidation
affects: [17-design-system-migration, deployment, performance-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns: [constructor-injection for DataCache, coordinated invalidation lifecycle, fresh session for refresh]

key-files:
  created: []
  modified:
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/api/routes/heroes.py
    - prismlab/backend/api/routes/items.py
    - prismlab/backend/api/routes/recommend.py
    - prismlab/backend/main.py
    - prismlab/backend/data/refresh.py
    - prismlab/backend/tests/conftest.py
    - prismlab/backend/tests/test_context_builder.py
    - prismlab/backend/tests/test_rules.py
    - prismlab/backend/tests/test_recommender.py

key-decisions:
  - "AsyncSession type hint retained in context_builder.py for matchup/popularity methods that still need DB"
  - "ResponseCache.clear() added as explicit method rather than direct _cache.clear() access"
  - "Fresh session pattern for DataCache.refresh() in pipeline -- not reusing post-commit session (INT-05)"

patterns-established:
  - "DataCache injection: all consumers receive DataCache via constructor, never import singleton directly"
  - "Three-layer invalidation order: DataCache.refresh -> RulesEngine auto-refresh via reference -> ResponseCache.clear"
  - "Test fixtures load DataCache from test DB in conftest to support cache-backed routes"

requirements-completed: [PERF-02, PERF-03, INT-05, INT-06]

# Metrics
duration: 12min
completed: 2026-03-27
---

# Phase 16 Plan 02: DataCache Hot-Path Wiring Summary

**Eliminated 12-20 DB queries per recommendation request by wiring DataCache into context builder, recommender validation, and API routes with coordinated three-layer cache invalidation**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-27T00:47:22Z
- **Completed:** 2026-03-27T00:59:48Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Context builder uses DataCache for all hero/item lookups -- zero hero/item DB queries on the hot path
- /api/heroes and /api/items serve directly from cache with zero DB dependency
- Coordinated invalidation: DataCache.refresh(fresh_session) -> ResponseCache.clear() after pipeline
- Startup ordering: seed -> cache load -> scheduler (no empty-cache race condition)
- init_lookups and refresh_lookups completely eliminated from codebase
- All test fixtures updated -- 155 tests pass (6 pre-existing system prompt content failures excluded)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire DataCache into context builder, recommender validation, and API route endpoints** - `7622a09` (feat)
2. **Task 2: Wire lifespan cache loading and coordinated three-layer refresh invalidation** - `c22fd72` (feat)

## Files Created/Modified
- `prismlab/backend/engine/context_builder.py` - Constructor accepts DataCache; _get_hero, _extract_top_items, _build_neutral_catalog now synchronous cache reads
- `prismlab/backend/engine/recommender.py` - _validate_item_ids uses cache.get_item_validation_map(); ResponseCache.clear() added
- `prismlab/backend/api/routes/heroes.py` - Serves from data_cache.get_all_heroes(), no SQLAlchemy
- `prismlab/backend/api/routes/items.py` - Serves from data_cache.get_all_items(), no SQLAlchemy
- `prismlab/backend/api/routes/recommend.py` - Singletons wired with data_cache injection
- `prismlab/backend/main.py` - Lifespan loads DataCache after seed, removed _rules.init_lookups
- `prismlab/backend/data/refresh.py` - Three-layer invalidation with fresh session for DataCache.refresh
- `prismlab/backend/tests/conftest.py` - Loads DataCache from test DB after seeding
- `prismlab/backend/tests/test_context_builder.py` - Removed stale get_relevant_items/get_neutral_items_by_tier patches
- `prismlab/backend/tests/test_rules.py` - RulesEngine fixture uses cache=data_cache
- `prismlab/backend/tests/test_recommender.py` - HybridRecommender fixture uses cache=data_cache, _validate_item_ids sync

## Decisions Made
- Retained `from sqlalchemy.ext.asyncio import AsyncSession` in context_builder.py and recommender.py because `build()` and `recommend()` still pass `db` session for matchup/popularity queries. Only `from sqlalchemy import select` and model imports were removed.
- Added `ResponseCache.clear()` as a clean public method rather than accessing `_cache.clear()` directly from refresh.py.
- Used fresh async session for DataCache.refresh in pipeline (not reusing post-commit session) to avoid stale data reads (INT-05).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test fixtures for DataCache-backed routes and constructors**
- **Found during:** Task 2 (verification)
- **Issue:** Tests failed because (a) conftest didn't load DataCache, (b) test_context_builder patched removed function imports, (c) test_rules used old RulesEngine() constructor, (d) test_recommender used old _validate_item_ids signature
- **Fix:** Updated conftest to load cache after seed; removed stale get_relevant_items/get_neutral_items_by_tier patches; updated RulesEngine and HybridRecommender fixtures with cache=data_cache; made _validate_item_ids calls sync
- **Files modified:** tests/conftest.py, tests/test_context_builder.py, tests/test_rules.py, tests/test_recommender.py
- **Verification:** 155 tests pass (6 pre-existing system prompt content failures excluded)
- **Committed in:** c22fd72 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix for test compatibility)
**Impact on plan:** Essential fix -- tests would fail without updated fixtures. No scope creep.

## Issues Encountered
- 6 pre-existing test failures in TestSystemPromptAllyRules and TestSystemPromptNeutralRules (system prompt content changed in a previous phase but tests not updated). These are out of scope for this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 16 (backend-data-cache) is complete
- All hero/item lookups on the hot path use DataCache
- Three-layer cache invalidation is wired and tested
- Ready for Phase 17 (design-system-migration)

---
*Phase: 16-backend-data-cache*
*Completed: 2026-03-27*
