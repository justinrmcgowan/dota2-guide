---
phase: 35-quality-foundation
plan: 02
subsystem: engine
tags: [validation, retry, response-quality, logging, recommender]

# Dependency graph
requires:
  - phase: 34-ux-speed
    provides: HybridRecommender with 3-mode routing and merge/dedup pipeline
provides:
  - ResponseValidator module with 4 logical consistency checks
  - Retry-on-failure mechanism appending error feedback to Claude prompt
  - Validation failure rate metrics for prompt tuning
affects: [36-prompt-intelligence, 38-adaptiveness-accuracy]

# Tech tracking
tech-stack:
  added: []
  patterns: [post-parse-validation, retry-with-feedback, module-level-metrics-counters]

key-files:
  created:
    - prismlab/backend/engine/response_validator.py
  modified:
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/tests/test_recommender.py

key-decisions:
  - "Counter-logic audit uses curated RELIABLE_STUN_HEROES set (28 heroes) since ability data lacks explicit stun tags"
  - "Phase-cost core items below 1000g are warnings not errors (some cheap items like BKB components are legitimate)"
  - "Validation retry always goes through Claude (not Ollama) even in auto path for higher correction quality"

patterns-established:
  - "Post-parse validation pattern: validate after merge/dedup, before enrichment"
  - "Retry-with-feedback: append error descriptions to user message for single retry"
  - "Module-level counters for operational metrics (validation_runs, validation_failures)"

requirements-completed: [QUAL-03, QUAL-05]

# Metrics
duration: 6min
completed: 2026-03-30
---

# Phase 35 Plan 02: Response Validation Layer Summary

**Post-parse ResponseValidator with phase-cost, duplicate, counter-logic, and empty-phase checks plus single-retry-on-failure via Claude error feedback**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-30T19:55:02Z
- **Completed:** 2026-03-30T20:01:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- ResponseValidator catches 4 classes of logically wrong recommendations before the user sees them
- Retry mechanism appends specific error descriptions to Claude's prompt for self-correction
- Validation failure rates tracked and logged at module level for prompt tuning opportunities
- Both deep path (Claude) and auto path (Ollama success) covered with validation

## Task Commits

Each task was committed atomically:

1. **Task 1: ResponseValidator module with validation checks** - `0364666` (feat)
2. **Task 2: Integrate validator into recommender with retry-on-failure** - `36db491` (feat)

## Files Created/Modified
- `prismlab/backend/engine/response_validator.py` - New module: ResponseValidator with 4 checks, ValidationResult/Issue dataclasses, get_validation_metrics()
- `prismlab/backend/engine/recommender.py` - Added ResponseValidator import, __init__ creation, _validate_and_retry method, integration in _deep_path and _auto_path
- `prismlab/backend/tests/test_recommender.py` - Added 2 integration tests (validator created with cache, None without)

## Decisions Made
- Used curated RELIABLE_STUN_HEROES set (28 hero IDs with reliable hard disables) for counter-logic audit since ability data behavior tuples don't tag stuns explicitly
- Core items below CORE_MIN_PER_ITEM (1000g) are warnings only, not errors, to avoid false positives on legitimate cheap core items
- Counter-logic missing BKB check is a warning not error since Claude may have valid context-specific reasons to omit it
- Retry always uses Claude LLM (self.llm.generate) even in auto path for higher correction quality

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ResponseValidator ready for use by Phase 36 (Prompt Intelligence) for validating exemplar-influenced outputs
- Validation metrics available via get_validation_metrics() for Phase 38 accuracy tracking
- All 15 existing + 2 new recommender tests pass

---
*Phase: 35-quality-foundation*
*Completed: 2026-03-30*
