---
phase: 35-quality-foundation
plan: 01
subsystem: engine
tags: [opendota, data-pipeline, context-builder, claude-prompt, pro-baselines]

requires:
  - phase: 34-ux-speed
    provides: "Two-pass recommendation and fast feedback loop for testing quality changes"
provides:
  - "Divine/Immortal bracket item popularity fetched from OpenDota via minMmr param"
  - "DataCache stores pro baselines per hero with atomic swap"
  - "Refresh pipeline fetches baselines for all heroes with 0.1s rate limiting"
  - "Context builder injects 'What Divine/Immortal Players Build' section into Claude prompt"
  - "Claude instructed to explain deviations from pro builds"
affects: [35-02, 35-03, 36-prompt-intelligence, 37-latency-caching]

tech-stack:
  added: []
  patterns:
    - "Bracket-filtered OpenDota API calls with minMmr parameter"
    - "Pro baselines stored as dict[int, dict[str, list[tuple]]] in DataCache"

key-files:
  created: []
  modified:
    - "prismlab/backend/data/opendota_client.py"
    - "prismlab/backend/data/cache.py"
    - "prismlab/backend/data/refresh.py"
    - "prismlab/backend/engine/context_builder.py"
    - "prismlab/backend/tests/test_context_builder.py"

key-decisions:
  - "Used minMmr=5420 for Divine+ bracket filtering (OpenDota's Divine threshold)"
  - "win_rate=0.0 placeholder since OpenDota itemPopularity only provides counts, not win/loss"
  - "0.1s sleep between hero API calls (~124 calls) to respect OpenDota rate limits"
  - "Pro baselines refresh is non-fatal: failure logs warning but doesn't break pipeline"

patterns-established:
  - "Bracket-filtered API methods return empty dict on failure (non-fatal)"
  - "Pro baselines use atomic swap pattern matching existing DataCache conventions"

requirements-completed: [QUAL-01, QUAL-02]

duration: 5min
completed: 2026-03-30
---

# Phase 35 Plan 01: Pro Build Baselines Summary

**Divine/Immortal item popularity from OpenDota injected into Claude context as build reference with deviation explanation prompting**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-30T19:52:30Z
- **Completed:** 2026-03-30T19:57:28Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- OpenDota client fetches bracket-filtered item popularity (Divine+ at 5400+ MMR)
- DataCache stores pro baselines per hero with get/set accessors and atomic swap
- Refresh pipeline fetches baselines for all ~124 heroes with 0.1s rate limiting
- Context builder injects "What Divine/Immortal Players Build" section showing top 5 items per phase with game counts
- Claude is instructed to explain deviations from pro builds in both the section header and matchup instructions
- 5 new tests covering presence/absence/empty/integration scenarios (all 50 tests pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pro baselines data pipeline** - `7c4e0dd` (feat)
2. **Task 2: Context builder pro reference section + Claude deviation prompt** - `133198b` (feat)

## Files Created/Modified
- `prismlab/backend/data/opendota_client.py` - Added fetch_hero_item_popularity_by_bracket with minMmr param
- `prismlab/backend/data/cache.py` - Added _hero_item_baselines dict, get/set methods
- `prismlab/backend/data/refresh.py` - Added baselines fetch to pipeline + _parse_item_baselines helper
- `prismlab/backend/engine/context_builder.py` - Added _build_pro_reference_section method, deviation prompting
- `prismlab/backend/tests/test_context_builder.py` - Added TestProReferenceSection class with 5 tests

## Decisions Made
- Used minMmr=5420 for Divine+ bracket (OpenDota's threshold) per design spec
- Set win_rate=0.0 as placeholder since itemPopularity endpoint only provides counts, not wins
- Added 0.1s sleep between hero API calls to respect OpenDota rate limits (~12.4s total)
- Made pro baselines refresh entirely non-fatal: any exception logs warning and continues

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pro baselines data pipeline is complete and ready for Plan 02 (response validation layer)
- Context builder now provides the foundation that Plan 03 (expanded rules engine) will build upon
- Baselines data will be used by Phase 37 cache warming (pre-computed pro builds)

---
*Phase: 35-quality-foundation*
*Completed: 2026-03-30*
