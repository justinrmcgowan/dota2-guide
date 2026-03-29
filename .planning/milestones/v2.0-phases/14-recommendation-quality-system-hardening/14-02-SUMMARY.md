---
phase: 14-recommendation-quality-system-hardening
plan: 02
subsystem: engine
tags: [rules-engine, sqlalchemy, async, dota2-items, deterministic-rules]

# Dependency graph
requires:
  - phase: 03-recommendation-engine
    provides: "Original RulesEngine with 12 hardcoded rules"
provides:
  - "DB-backed RulesEngine with init_lookups() and refresh_lookups()"
  - "18 total deterministic rules (12 migrated + 6 new)"
  - "Auto-refresh of rules lookup cache after data pipeline runs"
affects: [14-03, recommendation-quality, data-refresh]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DB-backed lookup cache pattern: load at startup, refresh after data pipeline"
    - "Name-to-ID helper methods (_hero_id, _item_id, _hero_ids) for safe lookup with None guards"

key-files:
  created: []
  modified:
    - "prismlab/backend/engine/rules.py"
    - "prismlab/backend/main.py"
    - "prismlab/backend/data/refresh.py"
    - "prismlab/backend/tests/conftest.py"
    - "prismlab/backend/tests/test_rules.py"

key-decisions:
  - "Removed HERO_NAMES dict entirely in favor of DB-backed _hero_id_to_name and _hero_name_to_id lookups"
  - "Merged BKB timing rule into existing _bkb_rule by expanding hero set to include disable-heavy heroes"
  - "6 new rules instead of 7: Raindrops, Orchid, Mekansm, Pipe, Halberd, Ghost Scepter"

patterns-established:
  - "DB-backed rule lookups: all hero/item references via _hero_id()/_item_id() with None guards"
  - "Rules engine async initialization: init_lookups() at startup, refresh_lookups() after data refresh"

requirements-completed: [D-01, D-02, D-03]

# Metrics
duration: 6min
completed: 2026-03-26
---

# Phase 14 Plan 02: DB-Backed Rules Engine with 18 Targeted Rules Summary

**Migrated rules engine from hardcoded 74-entry HERO_NAMES dict to DB-backed async lookups and added 6 new deterministic rules for obvious item recommendations**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-26T21:03:17Z
- **Completed:** 2026-03-26T21:09:18Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Eliminated hardcoded HERO_NAMES dict -- all hero/item references now use DB-backed lookups that auto-sync with OpenDota data refreshes
- Added 6 new targeted rules (Raindrops, Orchid, Mekansm, Pipe, Halberd, Ghost Scepter) reducing Claude API calls for predictable recommendations
- Expanded BKB rule to cover disable-heavy heroes (Tidehunter, Enigma, Magnus, Dark Willow) in addition to magic-heavy
- All 25 tests pass with DB-backed engine fixture (18 existing tests migrated + 7 new tests added)

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor RulesEngine to DB-backed lookups with async initialization** - `7c89a08` (feat)
2. **Task 2: Add 6 new targeted rules for obvious item recommendations** - `a436866` (feat)

## Files Created/Modified
- `prismlab/backend/engine/rules.py` - Replaced HERO_NAMES dict with init_lookups/refresh_lookups async methods, _hero_id/_item_id/_hero_ids helpers, 18 total rules
- `prismlab/backend/main.py` - Added rules engine initialization in lifespan after seed_if_empty()
- `prismlab/backend/data/refresh.py` - Added rules lookup refresh after successful data pipeline completion
- `prismlab/backend/tests/conftest.py` - Added 15 heroes and 6 items for new rule test coverage
- `prismlab/backend/tests/test_rules.py` - Converted to async DB-backed tests, added 7 new test classes for new rules

## Decisions Made
- Removed HERO_NAMES dict entirely rather than keeping it as a fallback -- DB lookups are the single source of truth
- Merged the planned BKB timing rule into the existing _bkb_rule by expanding its hero set, resulting in 6 new rules (not 7) for cleaner architecture
- Used internal_name for item lookups (e.g., "bkb" not "black_king_bar") matching the seeded test data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness
- Rules engine fully DB-backed and auto-refreshing
- 18 deterministic rules cover common item decisions without Claude API calls
- Ready for Plan 03 (system prompt and context builder improvements)

## Self-Check: PASSED

All 6 files verified present. Both commit hashes (7c89a08, a436866) found in git log.

---
*Phase: 14-recommendation-quality-system-hardening*
*Completed: 2026-03-26*
