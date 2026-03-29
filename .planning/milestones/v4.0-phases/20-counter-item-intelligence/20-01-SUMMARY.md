---
phase: 20-counter-item-intelligence
plan: 01
subsystem: engine
tags: [rules-engine, ability-queries, counter-items, pydantic, threat-level]

# Dependency graph
requires:
  - phase: 19-data-foundation-prompt-architecture
    provides: AbilityCached dataclass, DataCache.get_hero_abilities(), HeroAbilityData model
provides:
  - counter_target field on RuleResult schema
  - compute_threat_level utility function (schemas.py)
  - 5 ability query helpers on RulesEngine (_has_channeled_ability, _has_passive, _has_bkb_piercing, _has_escape_ability, _has_undispellable_debuff)
  - Expanded test fixtures (36 heroes, 5 items, 10 ability datasets)
  - Test scaffolds for ability-driven counter rules
affects: [20-02-PLAN, 20-03-PLAN, phase-21, phase-22]

# Tech tracking
tech-stack:
  added: []
  patterns: [ability-first query helpers on RulesEngine, compute_threat_level extraction from context_builder logic]

key-files:
  created: []
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/rules.py
    - prismlab/backend/tests/conftest.py
    - prismlab/backend/tests/test_rules.py

key-decisions:
  - "compute_threat_level placed in schemas.py co-located with EnemyContext"
  - "Ability helpers return first match (not all matches) for single-ability queries"
  - "escape_keywords set uses ability key substring matching for escape detection"

patterns-established:
  - "Ability query pattern: cache.get_hero_abilities(hero_id) -> iterate -> property check -> return AbilityCached | None"
  - "Threat classification: high (kills>=5 + K/D>=2), behind (deaths>=3 + D/K>=2), normal (else)"

requirements-completed: [CNTR-01, CNTR-03, CNTR-04]

# Metrics
duration: 6min
completed: 2026-03-27
---

# Phase 20 Plan 01: Counter-Item Intelligence Foundation Summary

**RuleResult counter_target field, 5 ability query helpers on RulesEngine, compute_threat_level function, and 36-hero test fixture expansion for ability-driven counter rules**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-27T15:47:43Z
- **Completed:** 2026-03-27T15:53:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Extended RuleResult with counter_target field for structured counter-item targeting data
- Built 5 reusable ability query helpers on RulesEngine that query AbilityCached from DataCache
- Added compute_threat_level function matching existing context_builder threat logic
- Expanded test fixtures with 36 additional heroes, 5 counter-items, and 10 hero ability datasets
- All 40 test_rules.py tests pass (25 existing + 15 new), 173 total suite green

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend RuleResult schema, expand test fixtures, add test scaffolds** - `33d4dbb` (test) - RED phase
2. **Task 2: Add ability query helper methods to RulesEngine** - `6b5ce02` (feat) - GREEN phase

_Note: TDD tasks -- Task 1 is RED (failing tests), Task 2 is GREEN (implementation passes all tests)_

## Files Created/Modified
- `prismlab/backend/engine/schemas.py` - Added counter_target field to RuleResult, added compute_threat_level function
- `prismlab/backend/engine/rules.py` - Added 5 ability query helpers, imported AbilityCached
- `prismlab/backend/tests/conftest.py` - 36 new heroes, 5 new items, 10 HeroAbilityData entries
- `prismlab/backend/tests/test_rules.py` - TestComputeThreatLevel, TestAbilityHelpers, TestCounterTargetField classes

## Decisions Made
- compute_threat_level lives in schemas.py next to EnemyContext (co-location for import convenience)
- _has_undispellable_debuff matches both "No" and "Strong Dispels Only" dispellable values
- escape_keywords uses ability key substring matching rather than hero role heuristic (more precise)
- Test for undispellable debuff accepts either Paralyzing Cask or Maledict (both qualify for Witch Doctor)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed undispellable debuff test assertion**
- **Found during:** Task 2 (GREEN phase test run)
- **Issue:** Test expected Maledict but Paralyzing Cask (dispellable="Strong Dispels Only") matched first
- **Fix:** Updated test to accept either valid ability name from Witch Doctor
- **Files modified:** prismlab/backend/tests/test_rules.py
- **Verification:** All 15 new tests pass
- **Committed in:** 6b5ce02 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test assertion fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 ability helpers are ready for Plan 02 to refactor existing rules and add 5 new counter-rule categories
- counter_target field is ready for Plan 02 to populate on all ability-driven rules
- compute_threat_level is ready for Plan 02 to wire into evaluate() for threat escalation
- Test fixtures cover all heroes referenced by existing and upcoming rules

---
*Phase: 20-counter-item-intelligence*
*Completed: 2026-03-27*
