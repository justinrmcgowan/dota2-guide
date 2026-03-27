---
phase: 19-data-foundation-prompt-architecture
plan: 02
subsystem: cache, matchup-service, refresh-pipeline, seed
tags: [datacache, abilities, timings, stale-while-revalidate, frozen-dataclass]

# Dependency graph
requires:
  - phase: 19-data-foundation-prompt-architecture
    plan: 01
    provides: HeroAbilityData + ItemTimingData SQLAlchemy models, OpenDota fetch methods, test scaffolds
  - phase: 16-backend-data-cache
    provides: DataCache singleton with frozen dataclasses and atomic swap pattern
provides:
  - AbilityCached and TimingBucket frozen dataclasses in DataCache
  - hero_internal_name_to_id, get_hero_abilities, get_hero_timings, set_hero_timings lookup methods
  - get_or_fetch_hero_timings stale-while-revalidate timing service
  - Ability constants in daily refresh pipeline and seed
affects:
  - prismlab/backend/data/cache.py
  - prismlab/backend/data/matchup_service.py
  - prismlab/backend/data/refresh.py
  - prismlab/backend/data/seed.py
  - prismlab/backend/tests/conftest.py

# Tech stack
added: []
patterns:
  - Frozen dataclass for immutable cached data (AbilityCached, TimingBucket)
  - Stale-while-revalidate with per-hero asyncio.Lock deduplication
  - Behavior normalization: string|list -> tuple for consistent access
  - String-to-int casting for OpenDota timing games/wins (Pitfall 1)
  - D-07 confidence classification: strong >= 1000, moderate >= 200, weak < 200
  - Non-fatal ability refresh: heroes/items still commit if ability fetch fails

# Key files
created: []
modified:
  - prismlab/backend/data/cache.py
  - prismlab/backend/data/matchup_service.py
  - prismlab/backend/data/refresh.py
  - prismlab/backend/data/seed.py
  - prismlab/backend/tests/conftest.py

# Decisions
key-decisions:
  - "AbilityCached.bkbpierce is bool (raw=='Yes'), not string -- simpler downstream checks"
  - "set_hero_timings does NOT clear ResponseCache -- timing data changes slowly, 5-min TTL is sufficient"
  - "Ability refresh is non-fatal try/except -- heroes/items always commit even if ability API fails"
  - "conftest loads data_cache after seeding so all cache-dependent tests work without explicit load calls"

# Metrics
duration: 6min
completed: "2026-03-27T05:59:52Z"
tasks_completed: 2
tasks_total: 2
files_modified: 5
---

# Phase 19 Plan 02: Data Cache Extensions and Timing Service Summary

Extended DataCache with AbilityCached/TimingBucket frozen dataclasses, 8 lookup methods, stale-while-revalidate timing service, ability refresh in daily pipeline, and ability seeding at startup -- all 16 Plan 01 test scaffolds pass.

## What Was Done

### Task 1: Extend DataCache with frozen dataclasses, dicts, load(), and lookup methods
**Commit:** `4790cea`

Extended `cache.py` with:
- `AbilityCached` frozen dataclass: key, dname, behavior (tuple), bkbpierce (bool), dispellable, dmg_type. Properties: `is_channeled`, `is_passive`
- `TimingBucket` frozen dataclass: time, games (int), wins (int), confidence. Property: `win_rate` with zero-division guard
- Three new DataCache instance dicts: `_hero_internal_name_to_id`, `_hero_abilities`, `_timing_benchmarks`
- `load()` extended to query HeroAbilityData and ItemTimingData tables, normalize behavior to tuple, parse games/wins from strings to ints, classify confidence (D-07 thresholds)
- Atomic swap block includes all new dicts for coherent cache refresh
- Four new lookup methods: `hero_internal_name_to_id()`, `get_hero_abilities()`, `get_hero_timings()`, `set_hero_timings()`
- Updated conftest.py to call `data_cache.load()` after DB seeding

### Task 2: Timing service, refresh pipeline integration, and seed extension
**Commit:** `168546c`

Added to `matchup_service.py`:
- `get_or_fetch_hero_timings()`: stale-while-revalidate with DataCache check, DB fallback, OpenDota fetch on miss. Background refresh via `asyncio.create_task()` when stale
- `_parse_timings_json()`: string-to-int casting, confidence classification
- `_refresh_hero_timings()`: per-hero lock deduplication, OpenDota fetch, DB upsert, DataCache update

Extended `refresh.py`:
- Ability constants fetch (2 API calls: `fetch_abilities()` + `fetch_hero_abilities()`) runs daily after hero/item refresh
- Filters `generic_*` and `special_bonus_*` entries (Pitfall 6)
- Non-fatal try/except: heroes/items still commit if ability refresh fails

Extended `seed.py`:
- Same ability seeding logic on first startup
- Same filtering for generic and talent entries

## Verification Results

- `python -m pytest tests/test_cache.py -x -q`: 16 passed (all Plan 01 scaffolds)
- `python -m pytest tests/ -q --ignore=tests/test_context_builder.py`: 144 passed, 2 skipped
- `python -c "from data.cache import AbilityCached, TimingBucket; ..."`: is_channeled prints True
- `python -c "from data.matchup_service import get_or_fetch_hero_timings; ..."`: imports successfully
- Pre-existing test_context_builder failure (Team Coordination section) is unrelated to this plan

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] conftest.py data_cache.load() call**
- **Found during:** Task 1
- **Issue:** Test fixture seeds DB data but never calls `data_cache.load()`, so cache-based tests would fail
- **Fix:** Added `data_cache.load(session)` call after seeding in `test_db_setup` fixture
- **Files modified:** prismlab/backend/tests/conftest.py
- **Commit:** 4790cea

**2. [Rule 1 - Bug] HeroItemPopularity import removed**
- **Found during:** Task 2
- **Issue:** Plan specified importing `HeroItemPopularity` from models but this class does not exist
- **Fix:** Removed non-existent import, kept only existing model classes
- **Files modified:** prismlab/backend/data/matchup_service.py
- **Commit:** 168546c

## Known Stubs

None -- all data flows are fully wired. AbilityCached and TimingBucket are populated from real DB data via load(). Timing service fetches from OpenDota on demand.

## Self-Check: PASSED

- All 5 modified files exist on disk
- Commit 4790cea found in git log
- Commit 168546c found in git log
- SUMMARY.md exists at expected path
