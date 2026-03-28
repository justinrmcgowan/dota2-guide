---
phase: 28-patch-data-refresh
plan: 02
subsystem: engine
tags: [rules-engine, system-prompt, patch-741, dota2]

# Dependency graph
requires:
  - phase: 28-patch-data-refresh-01
    provides: "Reseeded DB with 7.41 item/hero data"
provides:
  - "Audited rules engine with 7.41-accurate item references"
  - "System prompt with Patch 7.41 meta hints for Claude reasoning"
  - "Regression tests for 7.41 rule accuracy and prompt content"
affects: [engine-optimization, recommendations]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Patch notes section in system prompt for behavioral changes Claude cannot infer from data alone"]

key-files:
  created: []
  modified:
    - "prismlab/backend/engine/rules.py"
    - "prismlab/backend/engine/prompts/system_prompt.py"
    - "prismlab/backend/tests/test_rules.py"

key-decisions:
  - "Bloodstone hint uses 'spell damage amplification aura' without specific percentage to satisfy DATA-04 no-percentages test"
  - "No new rules added for 7.41 items (Crella's Crozier, Consecrated Wraps) -- meta hasn't settled, Claude handles via LLM path"
  - "Shiva's Guard _armor_rule reasoning updated with explicit 4500g cost and offlaner accessibility note"

patterns-established:
  - "Patch notes section: behavioral/mechanical changes added as concise meta hints before Output Fields section"
  - "Regression test pattern: TestPatch[version]RuleAccuracy and TestPatch[version]PromptHints classes"

requirements-completed: [PATCH-03, PATCH-04]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 28 Plan 02: Rules Audit & System Prompt 7.41 Update Summary

**Full 22-rule audit against 7.41 changes with Shiva's Guard cost update and 5-hint meta section in system prompt (3028 tokens, under 5000 budget)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T18:33:49Z
- **Completed:** 2026-03-28T18:38:43Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Audited all 22 rules: no stale Cornucopia or Refresher Orb references found
- Updated _armor_rule Shiva's Guard reasoning to reflect 4500g cost and improved offlaner timing
- Added "Patch 7.41 Notes" section to system prompt with 5 concise meta hints (Refresher Orb abilities-only, Bloodstone rework, Shiva's cost, neutral T1, facets removed)
- System prompt at 3028 estimated tokens (1972 under budget)
- Added 7 new regression tests across 2 test classes for 7.41 accuracy

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit all 23 rules against 7.41 and update system prompt** - `2e0354c` (feat)
2. **Task 2: Update rule tests for 7.41 accuracy** - `a57e965` (test)

## Files Created/Modified
- `prismlab/backend/engine/rules.py` - Updated _armor_rule Shiva's Guard reasoning for 7.41 cost (4500g)
- `prismlab/backend/engine/prompts/system_prompt.py` - Added "Patch 7.41 Notes" section with 5 meta hints
- `prismlab/backend/tests/test_rules.py` - Added TestPatch741RuleAccuracy (3 tests) and TestPatch741PromptHints (4 tests)

## Decisions Made
- Bloodstone hint reworded to avoid specific "12%" percentage, using "spell damage amplification aura" instead -- DATA-04 test enforces no percentages in system prompt
- No new rules for 7.41 items (Crella's Crozier, Consecrated Wraps) -- Claude handles these through the LLM reasoning path until meta settles
- Anti-heal rule's Shiva's Guard reference kept as-is -- functionality unchanged, internal_name resolves from DB

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed specific percentage from Bloodstone hint**
- **Found during:** Task 1 (System prompt update)
- **Issue:** "12% spell damage amplification aura" triggered DATA-04 test_no_specific_win_rates (regex catches any N% pattern)
- **Fix:** Rewrote to "spell damage amplification aura in a large radius" without percentage
- **Files modified:** prismlab/backend/engine/prompts/system_prompt.py
- **Verification:** test_no_specific_win_rates passes; all 14 system prompt tests pass
- **Committed in:** 2e0354c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor wording adjustment to comply with existing DATA-04 test constraint. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all changes are fully wired and functional.

## Next Phase Readiness
- Rules engine and system prompt fully updated for 7.41
- All 279 tests pass (78 rule/prompt tests, 201 other)
- Ready for any subsequent engine or prompt refinements

## Self-Check: PASSED

All 4 files verified present. Both task commits (2e0354c, a57e965) verified in git history.

---
*Phase: 28-patch-data-refresh*
*Completed: 2026-03-28*
