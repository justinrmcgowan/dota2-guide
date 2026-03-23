---
phase: 09-neutral-items
plan: 01
subsystem: engine
tags: [neutral-items, pydantic, context-builder, system-prompt, claude-api, fastapi]

# Dependency graph
requires:
  - phase: 08-allied-synergy
    provides: "Context builder section pattern, system prompt Team Coordination section, recommender passthrough pattern"
provides:
  - "Fixed seed detection: neutral items identified by tier field instead of qual"
  - "get_neutral_items_by_tier() query function grouping neutral items by tier"
  - "NeutralItemPick, NeutralTierRecommendation Pydantic models"
  - "LLMRecommendation.neutral_items and RecommendResponse.neutral_items fields"
  - "_build_neutral_catalog() context builder method with tier-grouped formatting"
  - "System prompt Neutral Items section with 5 reasoning rules and output constraint"
  - "Recommender neutral_items passthrough from LLM to API response"
affects: [09-02-PLAN, frontend-neutral-section]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Neutral item catalog as separate context builder section following ally/popularity pattern"
    - "Tier-grouped neutral items with compact formatting (T{N}: item - desc)"
    - "Backward-compatible schema extension with default_factory=list"

key-files:
  created: []
  modified:
    - "prismlab/backend/data/seed.py"
    - "prismlab/backend/data/matchup_service.py"
    - "prismlab/backend/engine/schemas.py"
    - "prismlab/backend/engine/context_builder.py"
    - "prismlab/backend/engine/prompts/system_prompt.py"
    - "prismlab/backend/engine/recommender.py"
    - "prismlab/backend/tests/conftest.py"
    - "prismlab/backend/tests/test_matchup_service.py"
    - "prismlab/backend/tests/test_context_builder.py"
    - "prismlab/backend/tests/test_recommender.py"
    - "prismlab/backend/tests/test_llm.py"

key-decisions:
  - "Use tier field (not qual) for neutral item detection in seed -- qual=='rare' incorrectly marks 51 shop items"
  - "Neutral items sent as separate context builder section after popularity, before final instruction"
  - "System prompt neutral rules placed between Team Coordination and Output Constraints"
  - "Backward-compatible schema: neutral_items defaults to empty list on both LLMRecommendation and RecommendResponse"

patterns-established:
  - "Neutral catalog context section: _build_neutral_catalog() queries by tier, formats compactly"
  - "Tier-based item grouping pattern: dict[int, list[dict]] for neutral items"

requirements-completed: [NEUT-01, NEUT-02, NEUT-03]

# Metrics
duration: 5min
completed: 2026-03-23
---

# Phase 09 Plan 01: Neutral Items Backend Pipeline Summary

**Neutral item data pipeline wired end-to-end: seed fix, tier query, schema extension, context catalog, system prompt rules, and recommender passthrough with 14 new tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-23T10:39:52Z
- **Completed:** 2026-03-23T10:45:49Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Fixed critical seed detection bug: neutral items now identified by tier field instead of incorrect qual=="rare" heuristic
- Full backend pipeline wired: neutral items flow from DB query through context builder to Claude prompt to structured response to API output
- System prompt extended with 5 neutral item reasoning rules (hero synergy, build-path interaction, per-item reasoning, no-preference option, tier timing)
- 14 new tests added (96 total, zero failures) with backward-compatible schema defaults

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix seed detection, add neutral item query, extend schemas** - `77b9e63` (test) + `f7afbb9` (feat) -- TDD RED/GREEN
2. **Task 2: Add neutral catalog to context builder, system prompt rules, and recommender passthrough** - `b5da3a2` (feat)

**Plan metadata:** [pending final commit] (docs: complete plan)

_Note: Task 1 used TDD with separate test and implementation commits._

## Files Created/Modified
- `prismlab/backend/data/seed.py` - Fixed is_neutral detection from qual to tier field, added abilities fallback for active_desc
- `prismlab/backend/data/matchup_service.py` - Added get_neutral_items_by_tier() query grouping items by tier number
- `prismlab/backend/engine/schemas.py` - Added NeutralItemPick, NeutralTierRecommendation models; extended LLMRecommendation and RecommendResponse
- `prismlab/backend/engine/context_builder.py` - Added _build_neutral_catalog() method, wired into build() after popularity section
- `prismlab/backend/engine/prompts/system_prompt.py` - Added Neutral Items section with 5 rules, rule 10 output constraint, response format bullet
- `prismlab/backend/engine/recommender.py` - Added neutral_items passthrough from LLM result to RecommendResponse
- `prismlab/backend/tests/conftest.py` - Added 3 neutral item fixtures (Chipped Vest T1, Psychic Headband T3, Spider Legs T5)
- `prismlab/backend/tests/test_matchup_service.py` - Added 2 tests for get_neutral_items_by_tier
- `prismlab/backend/tests/test_context_builder.py` - Added 7 tests: 3 neutral catalog, 4 system prompt smoke
- `prismlab/backend/tests/test_recommender.py` - Added 2 tests: neutral passthrough and fallback empty
- `prismlab/backend/tests/test_llm.py` - Added 3 tests: schema backward compat, data validation, response default

## Decisions Made
- Used tier field (not qual) for neutral item detection -- qual=="rare" is a quality marker for shop items, not neutral items
- Placed neutral catalog section after popularity section in context builder -- consistent with information flow pattern
- System prompt Neutral Items section placed between Team Coordination and Output Constraints for logical grouping
- All schema extensions use default_factory=list for backward compatibility with existing code and tests

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all data paths are fully wired.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Note: existing database needs re-seeding after deploying the seed fix (delete prismlab.db and restart).

## Next Phase Readiness
- Backend pipeline complete: /api/recommend now returns neutral_items field when Claude provides them
- Ready for Plan 02 (frontend) to render NeutralItemSection component
- Frontend types (recommendation.ts) need matching NeutralTierRecommendation/NeutralItemPick interfaces
- Database re-seed required on deployment to fix existing neutral item data

## Self-Check: PASSED

- All 12 key files verified present on disk
- All 3 commit hashes verified in git log (77b9e63, f7afbb9, b5da3a2)
- Full test suite: 96 passed, 0 failed

---
*Phase: 09-neutral-items*
*Completed: 2026-03-23*
