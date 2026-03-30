---
phase: 35-quality-foundation
plan: 03
subsystem: engine
tags: [rules-engine, deterministic, item-counter, meta-aware, team-composition, dota2]

# Dependency graph
requires:
  - phase: 20
    provides: "Ability-driven rules engine with counter-item intelligence"
provides:
  - "52 total deterministic rules (up from 22)"
  - "Item-vs-item counter rules: Nullifier, Blade Mail, Diffusal, Crimson Guard, etc."
  - "Meta-aware team composition rules using all_opponents field"
  - "Self-hero optimization rules: Blink initiator, Aghs, Radiance, Guardian Greaves"
  - "Support save rules: Glimmer Cape, Aeon Disk, Solar Crest"
affects: [recommendation-engine, hybrid-orchestrator, prompt-context]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Meta-aware rules iterate req.all_opponents for team-wide analysis", "_hero_attack_type helper for melee/ranged checks"]

key-files:
  created: []
  modified:
    - "prismlab/backend/engine/rules.py"
    - "prismlab/backend/tests/test_rules.py"
    - "prismlab/backend/tests/conftest.py"

key-decisions:
  - "All 30 new rules follow existing pattern (method on RulesEngine, returns list[RuleResult])"
  - "Meta-aware rules (Shiva's team armor, Pipe team magic, Wraith Pact) iterate req.all_opponents not req.lane_opponents"
  - "Self-hero rules check hero_id and playstyle without requiring opponent matching"
  - "Gleipnir lookup tries both 'gungungir' and 'gleipnir' internal names for compatibility"

patterns-established:
  - "Meta-aware rules: use req.all_opponents with count threshold (>=3) for team-comp detection"
  - "Self-hero rules: gate on hero_id set membership + role/playstyle, no opponent check needed"
  - "Attack type checks: _hero_attack_type() returns 'Melee'/'Ranged' from HeroCached"

requirements-completed: [QUAL-04]

# Metrics
duration: 12min
completed: 2026-03-30
---

# Phase 35 Plan 03: Rules Engine Expansion Summary

**52 deterministic rules covering item-vs-item counters, team-composition meta-awareness, and self-hero optimization -- up from 22 rules**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-30T19:51:47Z
- **Completed:** 2026-03-30T20:04:09Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Expanded rules engine from 22 to 52 deterministic rules (136% increase)
- Added 15 item-vs-item counter rules including Nullifier, Blade Mail, Diffusal Blade, Crimson Guard, Gleipnir, Bloodthorn, and Glimmer Cape
- Added 15 extended matchup and self-hero rules including Blink Dagger initiator, Aghanim's Scepter/Shard, Radiance for illusion carries, Guardian Greaves, and Urn of Shadows
- Introduced 3 meta-aware team composition rules (Shiva's, Pipe, Wraith Pact) that analyze full 5-hero enemy team via req.all_opponents
- Added comprehensive test coverage: 87 total tests passing (up from ~65)

## Task Commits

Each task was committed atomically:

1. **Task 1: Item-vs-item counter rules (30 new rules)** - `82dbdc8` (feat)
2. **Task 2: Tests + conftest expansion** - `2a9a789` (test)

## Files Created/Modified
- `prismlab/backend/engine/rules.py` - 30 new rule methods, _hero_attack_type helper, updated _rules property (52 total)
- `prismlab/backend/tests/test_rules.py` - 11 new test classes with 22 new test methods, updated _make_request helper with all_opponents/allies params
- `prismlab/backend/tests/conftest.py` - 25 new test items, ability data for Zeus/Lina/Leshrac

## Decisions Made
- All 30 new rules follow existing pattern (method on RulesEngine, returns list[RuleResult]) for consistency
- Meta-aware rules iterate req.all_opponents for team-wide analysis (first rules to do so)
- Self-hero rules (Blink, Aghs, Urn, Guardian Greaves, Heart) don't require opponent matching -- they fire based on hero_id and role/playstyle
- Gleipnir lookup tries both 'gungungir' and 'gleipnir' internal names for DB compatibility
- Added _hero_attack_type helper for hood/vanguard/skadi rules that check melee/ranged

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing ability data for test heroes**
- **Found during:** Task 2 (test execution)
- **Issue:** Zeus (id=22), Lina (id=25), and Leshrac (id=52) lacked HeroAbilityData in conftest, causing _has_magical_ability() to return None and failing tests for Glimmer Cape, Hood, and Pipe team magic rules
- **Fix:** Added HeroAbilityData entries for Zeus, Lina, and Leshrac with complete ability sets
- **Files modified:** prismlab/backend/tests/conftest.py
- **Verification:** All 87 tests pass
- **Committed in:** 2a9a789 (Task 2 commit)

**2. [Rule 1 - Bug] Duplicate item IDs in conftest**
- **Found during:** Task 2 (conftest item seeding)
- **Issue:** Bloodthorn and Guardian Greaves initially used IDs that conflicted with existing items (id=250 Scythe of Vyse, id=231 Pipe)
- **Fix:** Assigned unique IDs: Bloodthorn=251, Guardian Greaves=232
- **Files modified:** prismlab/backend/tests/conftest.py
- **Committed in:** 2a9a789 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for test correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## Known Stubs
None -- all rules are fully implemented with complete reasoning strings and counter_target tagging.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Rules engine now covers 52 deterministic scenarios for instant recommendations
- Meta-aware rules provide team-composition analysis without LLM calls
- Ready for any future rules expansion using the established pattern

## Self-Check: PASSED

- FOUND: prismlab/backend/engine/rules.py
- FOUND: prismlab/backend/tests/test_rules.py
- FOUND: prismlab/backend/tests/conftest.py
- FOUND: .planning/phases/35-quality-foundation/35-03-SUMMARY.md
- FOUND: commit 82dbdc8
- FOUND: commit 2a9a789

---
*Phase: 35-quality-foundation*
*Completed: 2026-03-30*
