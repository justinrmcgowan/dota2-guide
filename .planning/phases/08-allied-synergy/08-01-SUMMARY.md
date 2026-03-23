---
phase: 08-allied-synergy
plan: 01
subsystem: engine
tags: [context-builder, claude-api, ally-synergy, opendota, popularity]

# Dependency graph
requires:
  - phase: 03-recommendation-engine
    provides: "context_builder.py with build(), _build_opponent_lines(), _build_popularity_section()"
  - phase: 07-tech-debt
    provides: "Clean codebase with unused code removed"
provides:
  - "_build_ally_lines() method in context_builder.py"
  - "_extract_top_items() helper for merging popularity data across phases"
  - "Allied Heroes section in Claude user message between Your Hero and Lane Opponents"
affects: [08-02, system-prompt, recommendation-quality]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ally context follows same async DB pattern as _build_opponent_lines()"
    - "Popularity data merged across all game phases for per-hero top items"

key-files:
  created: []
  modified:
    - "prismlab/backend/engine/context_builder.py"
    - "prismlab/backend/tests/test_context_builder.py"
    - "prismlab/backend/tests/conftest.py"

key-decisions:
  - "Merge all phase popularity dicts (start, early, mid, late) into one ranking per ally rather than phase-separated"
  - "Top 5 items per ally keeps prompt compact while giving Claude enough build context"
  - "Allied Heroes section placed between Your Hero and Lane Opponents for logical information flow"

patterns-established:
  - "Ally data pipeline: request.allies -> _build_ally_lines() -> get_hero_item_popularity() -> _extract_top_items() -> formatted string"

requirements-completed: [ALLY-01]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 08 Plan 01: Context Builder Ally Lines Summary

**Allied hero names and popular item builds wired into Claude user message via _build_ally_lines() with OpenDota popularity data**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T09:32:11Z
- **Completed:** 2026-03-23T09:35:26Z
- **Tasks:** 1 (TDD: 3 commits - RED/GREEN/REFACTOR)
- **Files modified:** 3

## Accomplishments
- Added `_build_ally_lines()` async method to ContextBuilder that fetches hero names and top popular items for each allied hero
- Added `_extract_top_items()` helper that merges all game-phase popularity dicts, sorts by count, resolves top 5 item names from DB
- Wired "## Allied Heroes" section into build() between "Your Hero" and "Lane Opponents" -- backward compatible (no section when allies empty)
- 7 new tests in TestBuildAllyLines covering: empty list, hero names, popular items, fallback text, build integration, backward compat, section ordering
- Added Enigma (id=33) and Magnus (id=97) to test conftest for ally-relevant hero scenarios

## Task Commits

Each task was committed atomically (TDD flow):

1. **Task 1 RED: Failing tests for _build_ally_lines** - `efed044` (test)
2. **Task 1 GREEN: Implement _build_ally_lines with popularity** - `995d78c` (feat)
3. **Task 1 REFACTOR: Simplify fallback logic** - `3556c13` (refactor)

## Files Created/Modified
- `prismlab/backend/engine/context_builder.py` - Added _build_ally_lines(), _extract_top_items(), wired into build()
- `prismlab/backend/tests/test_context_builder.py` - Added TestBuildAllyLines class with 7 tests
- `prismlab/backend/tests/conftest.py` - Added Enigma and Magnus test heroes

## Decisions Made
- Merged all phase popularity dicts into one ranking per ally (simpler, keeps prompt compact)
- Top 5 items per ally balances information density vs token cost
- Allied Heroes section placed between Your Hero and Lane Opponents for logical flow (your team before their team)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all data pipelines are fully wired to real sources (get_hero_item_popularity via OpenDota).

## Next Phase Readiness
- Context builder now includes ally data in Claude prompts when allies are present
- Ready for 08-02 (system prompt updates to leverage ally context for synergy/anti-duplication reasoning)
- All 76 backend tests passing

---
*Phase: 08-allied-synergy*
*Completed: 2026-03-23*

## Self-Check: PASSED
All files exist, all commits verified.
