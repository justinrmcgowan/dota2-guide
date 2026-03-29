---
phase: 20-counter-item-intelligence
plan: 03
subsystem: engine
tags: [context-builder, ability-annotations, opponent-threats, claude-prompt]

# Dependency graph
requires:
  - phase: 20-counter-item-intelligence
    plan: 01
    provides: AbilityCached dataclass, DataCache.get_hero_abilities(), ability query helpers
provides:
  - _get_counter_relevant_abilities method on ContextBuilder
  - Inline "Threats:" annotations under each opponent in Claude user message
affects: [20-02-PLAN, phase-21, phase-22, phase-23]

# Tech tracking
tech-stack:
  added: []
  patterns: [inline ability annotations in opponent context lines, counter-relevant property filtering]

key-files:
  created: []
  modified:
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/tests/test_context_builder.py

key-decisions:
  - "Sync tests use pytest.mark.usefixtures('test_db_setup') to ensure DataCache loads ability data"
  - "Counter-relevant properties: channeled, passive, BKB-pierce, undispellable (4 properties only)"
  - "Undispellable matches both 'No' and 'Strong Dispels Only' dispellable values"

patterns-established:
  - "Ability annotation format: 'Threats: AbilityName (prop1, prop2); AbilityName2 (prop3)'"
  - "Annotations inline under each opponent (D-07), not as separate section"

requirements-completed: [CNTR-03]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 20 Plan 03: Ability Annotations in Claude Context Summary

**Inline ability threat annotations under each opponent in the Claude user message, filtering to channeled, passive, BKB-pierce, and undispellable properties**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T15:59:22Z
- **Completed:** 2026-03-27T16:04:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments
- Added _get_counter_relevant_abilities method to ContextBuilder that filters hero abilities to only counter-relevant properties
- Modified _build_opponent_lines to inject "Threats:" annotation line under each opponent
- Format matches D-06 spec: "Death Ward (channeled, BKB-pierce); Maledict (undispellable)"
- Abilities without counter-relevant properties (e.g., Blink) are excluded
- Heroes with no ability data produce no Threats line
- 8 tests covering WD, AM, CM, unknown hero, and integration with opponent lines

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add failing tests for ability annotations** - `9c65dd5` (test)
2. **Task 1 GREEN: Implement ability annotations and pass all tests** - `a78ba09` (feat)

_Note: TDD task -- commit 1 is RED (failing tests), commit 2 is GREEN (implementation passes all tests)_

## Files Created/Modified
- `prismlab/backend/engine/context_builder.py` - Added _get_counter_relevant_abilities method, modified _build_opponent_lines for inline Threats annotation
- `prismlab/backend/tests/test_context_builder.py` - Added TestAbilityAnnotations class with 8 test methods

## Decisions Made
- Sync tests use `pytest.mark.usefixtures("test_db_setup")` to guarantee DataCache is loaded with ability data before test execution
- Counter-relevant property set limited to 4: channeled, passive, BKB-pierce, undispellable -- matching D-06 token budget (~150 tokens per opponent)
- Undispellable check matches both "No" and "Strong Dispels Only" dispellable values (consistent with 20-01 ability helpers)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed sync test cache dependency**
- **Found during:** Task 1 GREEN phase (first test run)
- **Issue:** Sync tests using `builder` fixture didn't trigger `test_db_setup`, so DataCache had no ability data loaded
- **Fix:** Added `@pytest.mark.usefixtures("test_db_setup")` to all 6 sync test methods
- **Files modified:** prismlab/backend/tests/test_context_builder.py
- **Verification:** All 8 tests pass
- **Committed in:** a78ba09 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking issue)
**Impact on plan:** Minor test fixture fix. No scope creep.

## Issues Encountered
- Pre-existing test failures in TestSystemPromptAllyRules and TestSystemPromptNeutralRules (8 tests) are caused by system prompt restructuring in 19-03. Not related to this plan's changes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ability annotations now flow into Claude's user message for every opponent with counter-relevant abilities
- Combined with 20-01's counter_target field and 20-02's ability-driven rules, Claude receives rich threat context per opponent
- Phase 21 (Timing Benchmarks) can leverage the same inline annotation pattern for timing data
- Phase 23 (Win Condition Framing) can use ability annotations to inform macro strategy assessment

---
*Phase: 20-counter-item-intelligence*
*Completed: 2026-03-27*
