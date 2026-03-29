---
phase: 19-data-foundation-prompt-architecture
verified: 2026-03-27T06:22:59Z
status: gaps_found
score: 6/7 must-haves verified
gaps:
  - truth: "Timing data uses stale-while-revalidate pattern -- fetched per-hero on first request, background refresh when stale"
    status: failed
    reason: "get_or_fetch_hero_timings, _parse_timings_json, and _refresh_hero_timings were committed in 168546c but have been removed from the working tree of matchup_service.py. The file is currently 257 lines (working tree) vs 357 lines (committed HEAD). The function cannot be imported."
    artifacts:
      - path: "prismlab/backend/data/matchup_service.py"
        issue: "Working tree is missing get_or_fetch_hero_timings, _parse_timings_json, and _refresh_hero_timings. Unstaged modification strips 100 lines of timing service code from HEAD."
    missing:
      - "Restore get_or_fetch_hero_timings() stale-while-revalidate function in matchup_service.py"
      - "Restore _parse_timings_json() helper in matchup_service.py"
      - "Restore _refresh_hero_timings() with per-hero locking in matchup_service.py"
      - "Restore imports: from data.models import MatchupData, Item, ItemTimingData and from data.cache import TimingBucket"
---

# Phase 19: Data Foundation & Prompt Architecture Verification Report

**Phase Goal:** Ability metadata, hero-ability mappings, and item timing benchmarks are fetched, cached, and available in DataCache -- and the prompt architecture cleanly separates static directives (system message) from dynamic data (user message)
**Verified:** 2026-03-27T06:22:59Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | OpenDotaClient has fetch_abilities(), fetch_hero_abilities(), and fetch_item_timings(hero_id) methods | VERIFIED | All 3 methods present in opendota_client.py (lines 69-113), follow existing httpx pattern, correct URL paths confirmed |
| 2 | HeroAbilityData and ItemTimingData SQLAlchemy models exist with correct column types | VERIFIED | Both models in models.py (lines 90-109), JSON columns, hero_id ForeignKey with unique=True, docstrings match spec |
| 3 | After DataCache.load(), ability metadata is queryable by hero_id with behavior, damage type, BKB-pierce, and dispellable fields | VERIFIED | AbilityCached frozen dataclass (cache.py lines 75-92), get_hero_abilities() method (line 314), load() builds ability cache from HeroAbilityData (lines 209-234), all 16 test_cache.py tests pass |
| 4 | After DataCache.load(), timing benchmarks are queryable by hero_id with parsed int games/wins and confidence levels | VERIFIED | TimingBucket frozen dataclass (cache.py lines 95-106), get_hero_timings() method (line 318), load() builds timing cache with string-to-int cast and D-07 confidence classification (lines 236-261), tests pass |
| 5 | After a data refresh, DataCache contains fresh ability data AND timing data alongside heroes and items -- atomically swapped | VERIFIED | Atomic swap block (cache.py lines 263-271) includes _hero_abilities and _timing_benchmarks. test_atomic_swap_coherence passes. |
| 6 | Timing data uses stale-while-revalidate pattern -- fetched per-hero on first request, background refresh when stale | FAILED | get_or_fetch_hero_timings() was committed in 168546c but has been removed from the working tree of matchup_service.py. Working tree: 257 lines vs HEAD: 357 lines. Import fails with ImportError. |
| 7 | System prompt stays under 5,000 tokens, contains only directives, and includes all 4 v4.0 sections | VERIFIED | ~1,708 tokens (5,975 chars / 3.5). All 4 sections present: Timing Benchmarks, Counter-Item Specificity, Win Condition Framing, Build Path Awareness. All 14 test_system_prompt.py tests pass. |

**Score:** 6/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/data/opendota_client.py` | 3 new fetch methods for ability + timing endpoints | VERIFIED | fetch_abilities (line 69), fetch_hero_abilities (line 84), fetch_item_timings (line 99). All use raise_for_status() and return response.json(). |
| `prismlab/backend/data/models.py` | HeroAbilityData and ItemTimingData models | VERIFIED | HeroAbilityData (line 90), ItemTimingData (line 101). Both have JSON columns, hero_id ForeignKey with unique=True. Note: working tree adds HeroItemPopularity (unstaged), which is benign. |
| `prismlab/backend/tests/conftest.py` | Test fixtures with ability and timing data rows | VERIFIED | imports HeroAbilityData, ItemTimingData (line 7). Seeds AM ability data (4 abilities, lines 244-274), CM ability data (3 abilities, lines 275-300), AM timing data (lines 305-323). data_cache.load() called after seeding (lines 328-330). |
| `prismlab/backend/tests/test_cache.py` | Test scaffolds for DataCache ability/timing extensions | VERIFIED | 16 tests covering AbilityCached, TimingBucket, DataCache loading, internal name lookup, atomic swap. All 16 pass. |
| `prismlab/backend/data/cache.py` | AbilityCached + TimingBucket frozen dataclasses, extended DataCache with ability/timing dicts and lookup methods | VERIFIED | AbilityCached (lines 75-92), TimingBucket (lines 95-106), _hero_abilities/_timing_benchmarks/__hero_internal_name_to_id in __init__ (lines 125-128), load() extended (lines 209-261), 4 new lookup methods (lines 310-332). |
| `prismlab/backend/data/matchup_service.py` | Timing data stale-while-revalidate functions | FAILED | Working tree MISSING get_or_fetch_hero_timings, _parse_timings_json, _refresh_hero_timings. Functions exist in HEAD commit 168546c but have been removed as an unstaged modification. `python -c "from data.matchup_service import get_or_fetch_hero_timings"` raises ImportError. |
| `prismlab/backend/data/refresh.py` | Ability constants fetch in daily pipeline | VERIFIED | fetch_abilities() (line 107) and fetch_hero_abilities() (line 108) in daily pipeline. generic_ and special_bonus_ filters (lines 123-128). Non-fatal try/except. HeroAbilityData upsert (lines 142-148). |
| `prismlab/backend/data/seed.py` | Ability data seeding on first startup | VERIFIED | fetch_abilities() (line 117) and fetch_hero_abilities() (line 118). Same filtering logic. HeroAbilityData.session.add() (line 150). "and ability data" in output log (lines 162-163). |
| `prismlab/backend/engine/prompts/system_prompt.py` | SYSTEM_PROMPT constant with v4.0 directives | VERIFIED | All 4 directive sections present. 1,708 tokens. No win rate percentages. Conditional "If section is present" guards. RAW JSON ONLY and 8000+ MMR preserved. |
| `prismlab/backend/tests/test_system_prompt.py` | Token budget and no-dynamic-data assertions | VERIFIED | 14 tests across 4 classes: Budget, NoDynamicData, V4Directives, IsConstant. All 14 pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `opendota_client.py` | OpenDota API | httpx GET requests with constants/abilities, constants/hero_abilities, scenarios/itemTimings | VERIFIED | All 3 URL paths confirmed in source. raise_for_status() + return response.json() pattern. |
| `cache.py` | `models.py` | select(HeroAbilityData) and select(ItemTimingData) in load() | VERIFIED | Lines 210 and 237 in cache.py. Both model classes imported at line 20. |
| `matchup_service.py` | `cache.py` | data_cache.get_hero_timings / data_cache.set_hero_timings | FAILED | These calls existed only in the removed timing service functions. Working tree matchup_service.py has no reference to get_hero_timings or set_hero_timings. |
| `refresh.py` | `opendota_client.py` | fetch_abilities + fetch_hero_abilities calls in pipeline | VERIFIED | Lines 107-108 in refresh.py. |
| `system_prompt.py` | `engine/llm.py` | SYSTEM_PROMPT imported as system= parameter | VERIFIED | llm.py line 21: `from engine.prompts.system_prompt import SYSTEM_PROMPT`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `cache.py` _hero_abilities | new_hero_abilities dict | select(HeroAbilityData) from DB, built in load() | Yes -- queries all HeroAbilityData rows, parses abilities_json into AbilityCached list | FLOWING |
| `cache.py` _timing_benchmarks | new_timing_benchmarks dict | select(ItemTimingData) from DB, built in load() | Yes -- queries all ItemTimingData rows, parses timings_json with string-to-int cast and confidence classification | FLOWING |
| `matchup_service.py` get_or_fetch_hero_timings | TimingBucket dict | OpenDota fetch + DB cache + DataCache.get_hero_timings | NOT APPLICABLE -- function removed from working tree | DISCONNECTED (working tree) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| OpenDotaClient has 3 new methods | `python -c "from data.opendota_client import OpenDotaClient; c=OpenDotaClient(); print('fetch_abilities' in dir(c), 'fetch_hero_abilities' in dir(c), 'fetch_item_timings' in dir(c))"` | True True True | PASS |
| AbilityCached.is_channeled works | `python -c "from data.cache import AbilityCached; a=AbilityCached(key='t',dname='T',behavior=('Channeled',),bkbpierce=False,dispellable=None,dmg_type=None); print(a.is_channeled)"` | True | PASS |
| System prompt token budget | `python -c "import math; from engine.prompts.system_prompt import SYSTEM_PROMPT; print(math.ceil(len(SYSTEM_PROMPT)/3.5))"` | 1708 (< 5000) | PASS |
| Timing service importable | `python -c "from data.matchup_service import get_or_fetch_hero_timings"` | ImportError: cannot import name 'get_or_fetch_hero_timings' | FAIL |
| All cache + prompt tests | `python -m pytest tests/test_cache.py tests/test_system_prompt.py -q` | 30 passed in 0.31s | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DATA-01 | Plans 01, 02 | System fetches and caches hero ability metadata (behavior, damage type, BKB-pierce, dispellable) | SATISFIED | AbilityCached dataclass with all fields, load() populates from DB, get_hero_abilities() returns populated list. 16 test_cache.py tests pass. |
| DATA-02 | Plans 01, 02 | System fetches and caches hero-to-ability mapping from OpenDota constants | SATISFIED | fetch_hero_abilities() in opendota_client.py. hero_internal_name_to_id() lookup method. Mapping built during refresh via internal_name -> id dict. |
| DATA-03 | Plans 01, 02 | System fetches and caches item timing benchmark data (hero, item, time bucket, games, win rate) from OpenDota scenarios | PARTIAL | ItemTimingData model exists, fetch_item_timings() exists, DataCache load() populates timing benchmarks from DB at startup (SATISFIED). However the on-demand stale-while-revalidate service (get_or_fetch_hero_timings) is absent from the working tree. Startup-path timing is functional; per-hero demand-fetch is not. |
| DATA-04 | Plan 03 | System prompt restructured -- directives stay in system message (~5K token budget), all dynamic data moves to user message | SATISFIED | 4 directive sections present. 1,708 tokens. test_no_specific_win_rates, test_no_specific_timing_targets, test_no_item_catalog all pass. SYSTEM_PROMPT is a plain string constant. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `matchup_service.py` | Working tree | Uncommitted removal of get_or_fetch_hero_timings, _parse_timings_json, _refresh_hero_timings (100 lines) | Blocker | Stale-while-revalidate timing service missing from runtime. On-demand per-hero timing fetch not possible. |

### Human Verification Required

None -- all items can be verified programmatically. The gap in `matchup_service.py` is a clear code-level absence.

### Gaps Summary

**One gap blocks full goal achievement.** The phase goal includes "item timing benchmarks are fetched, cached, and available in DataCache." The DataCache load path at startup IS working -- `ItemTimingData` rows in the DB are loaded into `_timing_benchmarks` at startup via `cache.py`. However, the stale-while-revalidate service (`get_or_fetch_hero_timings`) that handles per-hero on-demand fetch, DB upsert, and DataCache update is absent from the working tree of `matchup_service.py`.

The root cause is an unstaged modification: the working tree has removed 100 lines from `matchup_service.py` that were committed in `168546c`. The committed HEAD contains the full timing service. The working tree does not.

**Impact scoping:** Timing data that was already in the DB at startup is accessible through DataCache (startup path works). What fails is the ability to fetch timing data for a hero that was never fetched before, or to refresh stale timing data on demand. This is a DATA-03 partial failure.

**Fix:** Discard the unstaged changes to `matchup_service.py` (`git restore prismlab/backend/data/matchup_service.py`) or manually re-add the three removed functions.

**What passes without issue:**
- All OpenDotaClient fetch methods (Plans 01 truths)
- Both SQLAlchemy models (Plans 01 truths)
- Full DataCache extension with AbilityCached, TimingBucket, atomic swap (Plan 02)
- refresh.py and seed.py ability data integration (Plan 02)
- System prompt v4.0 directives with token budget and data boundary enforcement (Plan 03)
- 30/30 test_cache.py + test_system_prompt.py tests pass
- 185/191 total tests pass (6 pre-existing unrelated failures)

---

_Verified: 2026-03-27T06:22:59Z_
_Verifier: Claude (gsd-verifier)_
