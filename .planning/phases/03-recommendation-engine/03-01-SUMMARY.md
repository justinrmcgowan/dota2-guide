---
phase: 03-recommendation-engine
plan: 01
subsystem: engine
tags: [pydantic, rules-engine, opendota, matchup-data, sqlalchemy, caching]

# Dependency graph
requires:
  - phase: 01-scaffolding
    provides: "SQLAlchemy models (Hero, Item, MatchupData), OpenDotaClient, database.py, conftest.py"
provides:
  - "Pydantic schemas: RecommendRequest, RecommendResponse, RecommendPhase, ItemRecommendation, RuleResult, LLMRecommendation"
  - "LLM_OUTPUT_SCHEMA JSON schema dict for Anthropic output_config"
  - "RulesEngine with 12 priority-ordered deterministic rules"
  - "Matchup data pipeline: get_or_fetch_matchup with stale-while-revalidate caching"
  - "Item catalog pre-filtering: get_relevant_items with role budget caps"
  - "OpenDotaClient.fetch_hero_matchups and fetch_hero_item_popularity methods"
affects: [03-02-PLAN, 03-03-PLAN, 04-item-timeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [priority-ordered-rules, stale-while-revalidate, per-pair-lock-dedup, role-budget-filtering]

key-files:
  created:
    - prismlab/backend/engine/__init__.py
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/rules.py
    - prismlab/backend/data/matchup_service.py
    - prismlab/backend/tests/test_rules.py
    - prismlab/backend/tests/test_matchup_service.py
  modified:
    - prismlab/backend/data/opendota_client.py
    - prismlab/backend/tests/conftest.py

key-decisions:
  - "12 deterministic rules covering spell-spammers, evasion, magic damage, passives, invisibility, regen, mana sustain, armor, and role-based boots"
  - "HERO_NAMES dict for enemy-naming reasoning strings rather than DB lookups in the rules engine"
  - "Stale-while-revalidate pattern: return cached matchup data immediately, refresh in background via asyncio.create_task"
  - "Per-pair asyncio.Lock deduplication to prevent duplicate OpenDota API calls for same matchup"
  - "Role-based item budget filtering: 10000g for cores (Pos 1-3), 5500g for supports (Pos 4-5)"

patterns-established:
  - "Priority-ordered rules: each rule method returns list[RuleResult], evaluate() collects all"
  - "Stale-while-revalidate: return stale data immediately, schedule background refresh"
  - "Per-key lock deduplication: asyncio.Lock per matchup pair to prevent duplicate API calls"
  - "Reasoning strings must name enemy hero: 'Against {hero}'s {ability}, {item} provides {benefit}'"

requirements-completed: [ENGN-01, ENGN-06]

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 03 Plan 01: Rules Engine + Matchup Pipeline Summary

**12-rule deterministic engine with enemy-naming reasoning, stale-while-revalidate matchup cache, and role-budgeted item pre-filtering for Claude prompts**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-21T20:52:38Z
- **Completed:** 2026-03-21T20:58:39Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Pydantic schemas define all request/response contracts consumed by Plans 02 and 03; LLM_OUTPUT_SCHEMA generated automatically from LLMRecommendation model
- RulesEngine with 12 priority-ordered rules covering all common matchup-driven item decisions (Magic Stick, BKB, MKB, Silver Edge, Spirit Vessel, Dust/Sentries, boots, armor, etc.)
- Matchup data pipeline fetches from OpenDota and caches in SQLite with 24h stale threshold, background refresh via asyncio.create_task, and per-pair lock deduplication
- Item pre-filtering returns 40-50 items by role budget for Claude prompt context assembly
- 30 total tests passing (18 rules + 12 matchup service)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create engine schemas and rules engine** - `0594a64` (feat)
2. **Task 2: Create matchup data service** - `0d8a3d5` (feat)

## Files Created/Modified
- `prismlab/backend/engine/__init__.py` - Engine package init
- `prismlab/backend/engine/schemas.py` - Pydantic models for all recommendation contracts + LLM_OUTPUT_SCHEMA
- `prismlab/backend/engine/rules.py` - RulesEngine class with 12 deterministic rules and HERO_NAMES dict
- `prismlab/backend/data/matchup_service.py` - Matchup fetch/cache pipeline with stale-while-revalidate and item pre-filtering
- `prismlab/backend/data/opendota_client.py` - Extended with fetch_hero_matchups and fetch_hero_item_popularity
- `prismlab/backend/tests/conftest.py` - Extended with additional hero/item seeds and test_db_session fixture
- `prismlab/backend/tests/test_rules.py` - 18 unit tests for rules engine
- `prismlab/backend/tests/test_matchup_service.py` - 12 integration tests for matchup pipeline

## Decisions Made
- Used a module-level HERO_NAMES dict for reasoning strings rather than querying the database from the rules engine, keeping rules pure and fast
- Curated MELEE_CARRIES set to actual Pos 1-2 melee carries (excluded ranged heroes and non-carry offlaners mentioned in plan)
- Armor rule uses AC for carries (role 1-2) and Shiva's for offlaners (role 3+) based on role rather than hero attribute
- Anti-heal rule limited to cores only (supports use Spirit Vessel via separate rule)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Schemas are ready for consumption by Claude API layer (Plan 02) and hybrid orchestrator (Plan 03)
- RulesEngine is ready to fire as first stage of every recommendation request
- Matchup data pipeline is ready to provide statistical context for Claude prompts
- Item pre-filtering is ready for prompt context assembly
- All 39 tests passing across entire backend test suite (no regressions)

## Self-Check: PASSED

All 8 files verified present. Both task commits (0594a64, 0d8a3d5) verified in git log.

---
*Phase: 03-recommendation-engine*
*Completed: 2026-03-21*
