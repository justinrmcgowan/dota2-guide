---
phase: 19-data-foundation-prompt-architecture
plan: 03
subsystem: ai-engine
tags: [system-prompt, claude-api, tdd, prompt-engineering, directives]

requires:
  - phase: 19-01
    provides: "Ability and timing data models in DB"
provides:
  - "SYSTEM_PROMPT v4.0 with timing, counter-item, win-condition, and build-path directive sections"
  - "test_system_prompt.py with 14 tests covering token budget, no-dynamic-data, v4.0 directives, and constant assertions"
affects: [context-builder, llm-integration, prompt-optimization]

tech-stack:
  added: []
  patterns: ["Conditional 'If section is present' guards for optional context sections in system prompt"]

key-files:
  created:
    - prismlab/backend/tests/test_system_prompt.py
  modified:
    - prismlab/backend/engine/prompts/system_prompt.py

key-decisions:
  - "v4.0 directives use conditional If guards so Claude ignores them when context sections are absent"
  - "New sections placed between Neutral Items and Output Fields to preserve output format at prompt end"
  - "No hero names, damage numbers, or win rate percentages in new directive sections (data boundary enforced)"

patterns-established:
  - "System prompt data boundary: directives only, no dynamic data (enforced by test_no_specific_win_rates, test_no_item_catalog)"
  - "Token budget test: math.ceil(chars / 3.5) < 5000 as automated guard"

requirements-completed: [DATA-04]

duration: 4min
completed: 2026-03-27
---

# Phase 19 Plan 03: System Prompt v4.0 Directives Summary

**System prompt extended with 4 directive sections (Timing Benchmarks, Counter-Item Specificity, Win Condition Framing, Build Path Awareness) and 14 TDD tests enforcing token budget and data boundary**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-27T06:09:02Z
- **Completed:** 2026-03-27T06:13:54Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created 14-test suite covering token budget (<5000), no-dynamic-data constraints, v4.0 section presence, and constant stability
- Added 4 new directive sections to SYSTEM_PROMPT using conditional "If section is present" guards
- System prompt at ~1708 estimated tokens (well under 5000 budget) with all v4.0 directives
- Established automated data boundary enforcement -- no percentages, no timing targets, no item catalogs in prompt

## Task Commits

Each task was committed atomically:

1. **Task 1: Create system prompt tests (RED phase)** - `855a2e6` (test)
2. **Task 2: Add v4.0 directive sections to system prompt (GREEN phase)** - `eaee9b4` (feat)

_TDD flow: RED phase confirmed 4 directive tests failing, GREEN phase made all 14 pass._

## Files Created/Modified
- `prismlab/backend/tests/test_system_prompt.py` - 14 tests across 4 classes: Budget, NoDynamicData, V4Directives, IsConstant
- `prismlab/backend/engine/prompts/system_prompt.py` - Extended SYSTEM_PROMPT with Timing Benchmarks, Counter-Item Specificity, Win Condition Framing, Build Path Awareness sections

## Decisions Made
- v4.0 directives use conditional "If section is present" guards so Claude ignores them when optional context sections are absent from the user message
- New directive sections placed between Neutral Items and Output Fields, keeping JSON output instructions last
- No dynamic data (hero names, damage numbers, win rates) in new sections -- enforces system-vs-user message data boundary (D-05, D-06)

## Deviations from Plan

None - plan executed exactly as written.

## Known Pre-existing Issues

Pre-existing test failures in `test_context_builder.py` (TestSystemPromptAllyRules, TestSystemPromptNeutralRules) expect prompt content that was compacted in a prior phase. Logged to `deferred-items.md`. These are NOT caused by this plan's changes.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- System prompt v4.0 directives in place, ready for context_builder to assemble timing/ability/strategy sections in user messages
- Token budget test provides automated guard against prompt bloat in future phases
- Data boundary tests prevent accidental dynamic data leaking into the cacheable system prompt

## Self-Check: PASSED

- FOUND: prismlab/backend/tests/test_system_prompt.py
- FOUND: prismlab/backend/engine/prompts/system_prompt.py (modified)
- FOUND: .planning/phases/19-data-foundation-prompt-architecture/19-03-SUMMARY.md
- FOUND: commit 855a2e6 (Task 1)
- FOUND: commit eaee9b4 (Task 2)

---
*Phase: 19-data-foundation-prompt-architecture*
*Completed: 2026-03-27*
