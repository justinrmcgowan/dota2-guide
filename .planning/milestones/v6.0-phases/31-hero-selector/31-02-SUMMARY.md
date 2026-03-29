---
phase: 31-hero-selector
plan: 02
subsystem: ui
tags: [typescript, react, api-client, types, hero-selector]

# Dependency graph
requires:
  - phase: 31-hero-selector/31-01
    provides: "POST /api/suggest-hero backend endpoint (Pydantic models define the response shape)"
provides:
  - "SuggestHeroRequest TypeScript interface in src/types/hero.ts"
  - "HeroSuggestion TypeScript interface in src/types/hero.ts"
  - "SuggestHeroResponse TypeScript interface in src/types/hero.ts"
  - "api.suggestHero() method in src/api/client.ts calling POST /api/suggest-hero"
affects: [31-hero-selector/31-03]

# Tech tracking
tech-stack:
  added: []
  patterns: ["snake_case field names in TypeScript interfaces to match backend JSON keys without conversion middleware"]

key-files:
  created: []
  modified:
    - prismlab/frontend/src/types/hero.ts
    - prismlab/frontend/src/api/client.ts

key-decisions:
  - "snake_case field names in SuggestHeroRequest/HeroSuggestion/SuggestHeroResponse match backend JSON response keys exactly — no camelCase conversion middleware in this project"
  - "HeroSuggestion imported in client.ts for re-export convenience, consistent with existing import style"
  - "No engine mode injection for suggestHero (unlike recommend which auto-injects localStorage mode)"

patterns-established:
  - "Pattern: New API methods added to api object in client.ts with matching import from types/ file"
  - "Pattern: Optional fields use ? suffix with backend default documented in comment (top_n, bracket)"

requirements-completed: [HERO-04]

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 31 Plan 02: Hero Selector TypeScript Contracts Summary

**TypeScript interfaces (SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse) added to hero.ts with api.suggestHero() method wired to POST /api/suggest-hero in client.ts**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T21:00:00Z
- **Completed:** 2026-03-29T21:03:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Three new TypeScript interfaces exported from src/types/hero.ts with snake_case fields matching backend JSON keys exactly
- api.suggestHero() method added to the api object in client.ts, typed against the new interfaces, calling POST /api/suggest-hero
- TypeScript strict-mode compilation passes with zero errors after both changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add suggestion TypeScript interfaces to src/types/hero.ts** - `f800fef` (feat)
2. **Task 2: Add api.suggestHero() to src/api/client.ts** - `ff848ae` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `prismlab/frontend/src/types/hero.ts` - Appended SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse after existing Hero interface
- `prismlab/frontend/src/api/client.ts` - Extended import from types/hero; added suggestHero method to api object

## Decisions Made
- snake_case field names chosen to match backend JSON response keys exactly — no camelCase conversion middleware exists in this project
- No localStorage engine mode injection for suggestHero (unlike recommend) — suggest-hero doesn't have an engine mode concept

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 03 (Hero Selector UI) can now import SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse from src/types/hero.ts
- Plan 03 can call api.suggestHero() directly; TypeScript will enforce the contract
- No blockers

---
*Phase: 31-hero-selector*
*Completed: 2026-03-29*
