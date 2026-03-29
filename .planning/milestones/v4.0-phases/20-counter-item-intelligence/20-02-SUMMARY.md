---
phase: 20-counter-item-intelligence
plan: 02
subsystem: engine
tags: [rules-engine, ability-first, counter-items, threat-escalation, counter-target]

# Dependency graph
requires:
  - phase: 20-counter-item-intelligence
    plan: 01
    provides: 5 ability query helpers, counter_target field on RuleResult, compute_threat_level
provides:
  - 14 rules refactored to ability-first + fallback pattern
  - 4 new counter-rule methods (Eul's channel, Lotus/Linken's, dispel, hex/root escape)
  - BKB-pierce warning integrated into _bkb_rule
  - Threat escalation in evaluate() adjusts priority based on enemy performance
  - 17 new tests covering ability-driven rules, new counter rules, reasoning naming, threat escalation
affects: [20-03-PLAN, phase-21, phase-22, phase-23]

# Tech tracking
tech-stack:
  added: []
  patterns: [ability-first + hero-ID fallback for all enemy-matching rules, threat_map priority adjustment in evaluate()]

key-files:
  created: []
  modified:
    - prismlab/backend/engine/rules.py
    - prismlab/backend/tests/test_rules.py

key-decisions:
  - "Fallback hero ID sets kept at original size for heroes without ability data in DataCache -- ability-first fires when data exists, fallback catches the rest"
  - "BKB-pierce warning appended to BKB reasoning as a note, not a separate rule method"
  - "Eul's recommended as primary dispel item for all roles in _dispel_counter_rule"
  - "Lotus Orb / Linken's split at role boundary: Linken's for role < 3, Lotus for role >= 3"
  - "Hex/root escape split: Scythe of Vyse for role <= 3, Rod of Atos for role > 3"

patterns-established:
  - "Ability-first + fallback: query ability properties via helper, match from AbilityCached; if no match, check smaller fallback hero ID set"
  - "counter_target format: '{hero_name}: {ability.dname} ({property})' for structured downstream consumption"
  - "Threat escalation post-process: after all rules fire, match counter_target to opponent threat level and adjust priority"

requirements-completed: [CNTR-01, CNTR-02, CNTR-03, CNTR-04]

# Metrics
duration: 10min
completed: 2026-03-27
---

# Phase 20 Plan 02: Counter-Item Rule Refactoring and New Counter Rules Summary

**14 enemy-matching rules refactored to ability-first pattern, 4 new counter-rule methods added, BKB-pierce warning integrated, threat escalation wired into evaluate(), all 57 tests passing**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-27T15:59:39Z
- **Completed:** 2026-03-27T16:09:39Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Refactored all 14 enemy-matching rules to ability-first + fallback pattern with counter_target field
- Added 4 new counter-rule methods: _euls_channel_rule, _lotus_linkens_rule, _dispel_counter_rule, _hex_root_escape_rule
- Integrated BKB-pierce warning into _bkb_rule (D-04 category 3)
- Wired threat escalation into evaluate() using compute_threat_level -- fed enemies upgrade priority, behind enemies downgrade
- Added 3 new helper methods: _has_magical_ability, _has_invis_ability, _count_active_abilities
- 22 total rules registered (18 existing + 4 new methods)
- 25 counter_target= assignments across all ability-driven rules
- 17 new tests (5 ability-driven, 7 new counter rules, 1 reasoning naming, 4 threat escalation)
- 57 test_rules.py tests pass, 190 total backend suite green

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor rules + new counter rules + threat escalation** - `5bcc8c6` (feat)
2. **Task 2: Comprehensive tests for all new functionality** - `8111b5d` (test)

## Files Created/Modified

- `prismlab/backend/engine/rules.py` - Full refactor: ability-first + fallback on 14 rules, 4 new rule methods, BKB-pierce warning, threat escalation in evaluate()
- `prismlab/backend/tests/test_rules.py` - TestAbilityDrivenRules, TestNewCounterRules, TestReasoningNamesAbility, TestThreatEscalation classes; updated TestRuleCount and TestNoMatchReturnsEmpty

## Decisions Made

- Fallback hero ID sets remain full-size because many heroes lack ability data in DataCache -- ability-first fires only when data exists
- BKB-pierce warning is appended to the BKB reasoning string rather than being a separate rule method (per D-04)
- Lotus Orb vs Linken's Sphere split at role boundary (< 3 vs >= 3) matching core vs support economy
- _dispel_counter_rule recommends Eul's as universal dispel item (simplest correct choice)
- Hex vs Atos split: Scythe of Vyse for cores, Rod of Atos for supports (gold economy appropriate)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Expanded fallback sets for heroes without ability data**
- **Found during:** Task 1 (test failures for Zeus, Bristleback, etc.)
- **Issue:** Plan suggested shrinking fallback sets, but most heroes in test fixtures lack ability data in DataCache, causing rules to not fire
- **Fix:** Kept original hero ID lists as fallback sets; ability-first check fires for heroes with ability data, fallback catches the rest
- **Files modified:** prismlab/backend/engine/rules.py
- **Verification:** All 40 existing tests pass with expanded fallbacks
- **Committed in:** 5bcc8c6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fallback sets are larger than plan suggested, but the ability-first pattern is preserved. As more heroes get ability data loaded into DataCache, the fallback sets become less relevant.

## Known Stubs

None -- all rules are fully functional with both ability-first and fallback paths.

## Issues Encountered

None

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- All 22 rules with counter_target fields are ready for Plan 03 to enrich Claude's user message with ability context
- Threat escalation is active in evaluate() and ready for downstream consumers
- counter_target structured data enables future frontend tooltip work (Phase 21+)
- 57 test_rules.py tests provide regression safety for Phase 22/23 changes

## Self-Check: PASSED

- All files exist: rules.py, test_rules.py, 20-02-SUMMARY.md
- All commits exist: 5bcc8c6, 8111b5d
- 57/57 test_rules.py tests pass
- 190/190 backend suite tests pass (0 failures)

---
*Phase: 20-counter-item-intelligence*
*Completed: 2026-03-27*
