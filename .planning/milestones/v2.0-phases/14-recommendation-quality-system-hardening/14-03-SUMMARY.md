---
phase: 14-recommendation-quality-system-hardening
plan: 03
subsystem: api, ui
tags: [pydantic, validation, react, sliders, error-handling, rate-limiting]

# Dependency graph
requires:
  - phase: 14-01
    provides: "FallbackReason enum, fallback_reason field on RecommendResponse, fallback strategy dict"
provides:
  - "Backend damage_profile sum validator (model_validator, rejects != 100%)"
  - "Backend playstyle-role validator (field_validator, rejects invalid combos)"
  - "VALID_PLAYSTYLES mapping (single source of truth for backend, mirrors frontend constants.ts)"
  - "Frontend auto-rebalancing damage profile sliders (proportional redistribution)"
  - "Frontend fallback reason-specific banner messages with 5s auto-dismiss"
  - "Frontend friendly 429 (rate limit) and 422 (validation) error messages"
  - "fallback_reason field on TypeScript RecommendResponse type"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic model_validator for cross-field validation (damage profile sum)"
    - "Pydantic field_validator with info.data for dependent field validation (playstyle depends on role)"
    - "Proportional redistribution with remainder assignment for slider rebalancing"
    - "FALLBACK_MESSAGES record for reason-specific user-facing error text"

key-files:
  created: []
  modified:
    - "prismlab/backend/engine/schemas.py"
    - "prismlab/backend/tests/test_api.py"
    - "prismlab/backend/tests/test_rules.py"
    - "prismlab/backend/tests/test_recommender.py"
    - "prismlab/backend/tests/test_context_builder.py"
    - "prismlab/frontend/src/types/recommendation.ts"
    - "prismlab/frontend/src/api/client.ts"
    - "prismlab/frontend/src/components/game/DamageProfileInput.tsx"
    - "prismlab/frontend/src/components/timeline/ErrorBanner.tsx"
    - "prismlab/frontend/src/components/layout/MainPanel.tsx"

key-decisions:
  - "VALID_PLAYSTYLES as module-level dict in schemas.py -- single source of truth for backend, mirrors frontend constants.ts"
  - "Proportional redistribution with remainder assignment for slider rebalancing -- avoids rounding drift"
  - "5s auto-dismiss for both error and fallback banners (toast pattern) while overall_strategy provides persistent context"

patterns-established:
  - "Cross-field Pydantic validation: model_validator(mode='after') for computed cross-field constraints"
  - "Dependent field validation: field_validator with info.data for fields that depend on other fields"
  - "Auto-rebalancing UI: proportional redistribution preserving ratios between non-dragged sliders"

requirements-completed: [D-07, D-09, D-10]

# Metrics
duration: 7min
completed: 2026-03-26
---

# Phase 14 Plan 03: Validation & Error Transparency Summary

**Backend damage profile sum and playstyle-role validators with frontend auto-rebalancing sliders, reason-specific fallback banners, and friendly 429/422 handling**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-26T21:17:58Z
- **Completed:** 2026-03-26T21:25:21Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Backend rejects damage_profile with sum != 100% (HTTP 422) and invalid playstyle-role combinations (HTTP 422)
- Damage profile sliders auto-rebalance proportionally to always maintain 100% total
- Fallback banners show reason-specific messages (timeout, parse error, API error, rate limited) with 5s auto-dismiss
- 429 responses show "Please wait N seconds" with Retry-After header support instead of raw HTTP error
- 422 validation errors surface the specific Pydantic error message to the user

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend validation -- damage profile sum + playstyle-role mapping** - `afe0953` (feat)
2. **Task 2: Frontend -- slider rebalancing, fallback reason display, 429 handling** - `79c01e6` (feat)

## Files Created/Modified
- `prismlab/backend/engine/schemas.py` - Added VALID_PLAYSTYLES mapping, validate_damage_profile_sum model_validator, validate_playstyle field_validator
- `prismlab/backend/tests/test_api.py` - Added TestDamageProfileValidation (3 tests) and TestPlaystyleValidation (2 tests) classes
- `prismlab/backend/tests/test_rules.py` - Updated _make_request helper to auto-select valid playstyle per role
- `prismlab/backend/tests/test_recommender.py` - Updated sample_request fixture playstyle to "Farm-first"
- `prismlab/backend/tests/test_context_builder.py` - Updated _make_request helper and assertion for new playstyle
- `prismlab/frontend/src/types/recommendation.ts` - Added fallback_reason field to RecommendResponse
- `prismlab/frontend/src/api/client.ts` - Added 429 and 422 specific error handling in postJson
- `prismlab/frontend/src/components/game/DamageProfileInput.tsx` - Replaced simple setter with proportional auto-rebalancing logic
- `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` - Added FALLBACK_MESSAGES map, fallbackReason prop, 5s auto-dismiss for fallback type
- `prismlab/frontend/src/components/layout/MainPanel.tsx` - Wired fallbackReason={data.fallback_reason} to ErrorBanner

## Decisions Made
- VALID_PLAYSTYLES mapping lives in schemas.py as module-level dict (mirrors frontend constants.ts exactly)
- Used proportional redistribution with remainder assignment for slider rebalancing (avoids rounding errors)
- Both error and fallback banners auto-dismiss after 5s (toast pattern); overall_strategy text provides persistent fallback context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing tests using invalid playstyle values**
- **Found during:** Task 1 (Backend validation)
- **Issue:** Existing tests used "farming" and "aggressive" (not in VALID_PLAYSTYLES), which would fail the new playstyle-role validator
- **Fix:** Updated test_api.py, test_recommender.py, test_context_builder.py to use valid playstyles ("Farm-first", "Aggressive"). Updated test_rules.py helper to auto-select a valid default playstyle per role.
- **Files modified:** test_api.py, test_recommender.py, test_context_builder.py, test_rules.py
- **Verification:** All 128 non-pre-existing tests pass
- **Committed in:** afe0953 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix -- existing tests used freeform playstyle strings that the new validator correctly rejects. No scope creep.

## Issues Encountered
- 6 pre-existing test failures in test_context_builder.py (TestSystemPromptAllyRules, TestSystemPromptNeutralRules) unrelated to this plan's changes -- system prompt content strings don't match test expectations. Logged to deferred-items.md.

## Known Stubs
None -- all data flows are fully wired.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 14 is now complete (all 3 plans done)
- Validation gaps closed: damage profile sum enforcement and playstyle-role validation
- Error transparency complete: fallback reasons flow from backend through frontend with specific user-facing messages
- Ready for verifier pass

---
*Phase: 14-recommendation-quality-system-hardening*
*Completed: 2026-03-26*

## Self-Check: PASSED
- All 7 key files exist
- Both task commits found (afe0953, 79c01e6)
- SUMMARY.md created
