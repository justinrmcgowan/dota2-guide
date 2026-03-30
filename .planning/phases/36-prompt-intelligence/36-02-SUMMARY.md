---
phase: 36-prompt-intelligence
plan: 02
subsystem: engine
tags: [timing-gates, turbo-mode, game-clock, partial-draft, unusual-role, pydantic, rules-engine, context-builder]

# Dependency graph
requires:
  - phase: 36-01
    provides: Few-shot exemplar system and exemplar loader
  - phase: 35-quality-foundation
    provides: 52 deterministic rules, hero_attack_type helper, HERO_ROLE_VIABLE map
provides:
  - game_time_seconds and turbo fields on RecommendRequest (backend + frontend)
  - Timing-gate filter blocking Midas after 20min, Rapier before 35min, BKB urgency escalation
  - Turbo mode support halving all timing thresholds
  - Game clock injection into Claude context for time-aware reasoning
  - Unusual role detection flagging uncommon hero-role combos in Claude context
  - Partial draft caveats for incomplete drafts (<10 heroes)
  - Frontend wiring of GSI game_clock into recommendation requests
affects: [recommender, system-prompt, gsi-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Timing gate as post-rule filter in evaluate() -- removes items rather than adding"
    - "Context annotations as conditional section builders returning empty string when inactive"
    - "Turbo multiplier pattern: turbo_mult = 0.5 if req.turbo else 1.0"

key-files:
  created: []
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/rules.py
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/tests/test_rules.py
    - prismlab/backend/tests/test_context_builder.py
    - prismlab/frontend/src/types/recommendation.ts
    - prismlab/frontend/src/hooks/useRecommendation.ts
    - prismlab/frontend/src/stores/gameStore.ts

key-decisions:
  - "Timing gates implemented as post-processing filter in evaluate(), not as separate rule methods"
  - "BKB urgency escalation by item_name.lower() match on 'black king bar' (not 'bkb')"
  - "Frontend sends game_time_seconds only when positive, turbo only when true -- keeps requests compact"
  - "Unusual role detection uses HERO_ROLE_VIABLE from hero_selector -- no new data structures"

patterns-established:
  - "Timing gate filter: _apply_timing_gates runs after all rules, before threat adjustment"
  - "Context annotation builders: return empty string when condition not met, non-empty section otherwise"

requirements-completed: [PROM-02, PROM-03, PROM-04, PROM-05]

# Metrics
duration: 12min
completed: 2026-03-30
---

# Phase 36 Plan 02: Game Clock + Timing Gates + Edge Case Context Summary

**Game-clock-aware timing gates blocking inappropriate items, unusual role detection, partial draft caveats, and turbo mode halving all thresholds**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-30T20:36:41Z
- **Completed:** 2026-03-30T20:48:51Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Timing-gate filter blocks Midas after 20min, Rapier before 35min, escalates BKB urgency after 25min
- Turbo mode halves all timing thresholds (Midas 10min, Rapier 17.5min, BKB 12.5min)
- Game clock injected into Claude context with formatted time string and turbo annotation
- Unusual hero-role combos (e.g., pos 1 Zeus) flagged in Claude context with adjusted expectations
- Partial drafts (<10 heroes) produce recommendations with uncertainty caveats
- Frontend wires GSI game_clock into recommendation requests via gsiStore
- 20 new tests (11 rules + 9 context builder) covering all new functionality

## Task Commits

Each task was committed atomically:

1. **Task 1: Schema fields + timing-gate rules (TDD)** - `2d8a845` (feat)
2. **Task 2: Context builder annotations** - `eaa1315` (feat)
3. **Task 3: Frontend wiring** - `5012360` (feat)

## Files Created/Modified
- `prismlab/backend/engine/schemas.py` - Added game_time_seconds (int|None) and turbo (bool) to RecommendRequest
- `prismlab/backend/engine/rules.py` - Added _apply_timing_gates filter with Midas/Rapier/BKB gates and turbo multiplier
- `prismlab/backend/engine/context_builder.py` - Added _build_game_clock_section, _build_unusual_role_section, _build_partial_draft_section
- `prismlab/backend/tests/test_rules.py` - 11 new tests for schema fields and timing gates
- `prismlab/backend/tests/test_context_builder.py` - 9 new tests for context annotations
- `prismlab/frontend/src/types/recommendation.ts` - Added game_time_seconds and turbo to RecommendRequest interface
- `prismlab/frontend/src/hooks/useRecommendation.ts` - Reads GSI game_clock, passes as game_time_seconds
- `prismlab/frontend/src/stores/gameStore.ts` - Added turbo field, setTurbo action, reset in clear()

## Decisions Made
- Timing gates as post-processing filter rather than separate rules -- existing rules return RuleResult objects (additive), timing gates are subtractive (remove items). Filter pattern is cleaner than adding "anti-rules."
- BKB urgency matches on "black king bar" in lowered item_name, not "bkb" abbreviation -- the RuleResult.item_name uses full display names.
- Frontend sends game_time_seconds only when positive (game has started), turbo only when true -- keeps backward-compatible and compact.
- Unusual role detection reuses HERO_ROLE_VIABLE from hero_selector rather than creating a new data structure.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed BKB name matching in timing gates and tests**
- **Found during:** Task 1 (timing gate implementation)
- **Issue:** Plan suggested matching "bkb" in item_name.lower(), but RuleResult uses "Black King Bar" as display name -- "bkb" is not a substring of "black king bar"
- **Fix:** Changed to match on "black king bar" in lowered item_name
- **Files modified:** prismlab/backend/engine/rules.py, prismlab/backend/tests/test_rules.py
- **Verification:** BKB urgency escalation test passes
- **Committed in:** 2d8a845 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor string matching fix. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All PROM requirements (02-05) implemented and tested
- Backend timing gates and context annotations ready for production
- Frontend turbo toggle UI deferred (field exists on gameStore, can be wired to UI later)
- 157 total backend tests passing (98 rules + 59 context builder)

## Self-Check: PASSED

All 8 modified files verified present. All 3 task commits verified in git log.

---
*Phase: 36-prompt-intelligence*
*Completed: 2026-03-30*
