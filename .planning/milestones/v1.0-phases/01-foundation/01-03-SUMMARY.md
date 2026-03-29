---
phase: 01-foundation
plan: 03
subsystem: ui
tags: [react, fuse.js, fuzzy-search, zustand, steam-cdn, vitest, typescript]

# Dependency graph
requires:
  - phase: 01-foundation plan 01
    provides: Backend API endpoints (GET /api/heroes) for hero data
  - phase: 01-foundation plan 02
    provides: React/Vite/Tailwind frontend shell, layout components, Zustand store, type definitions, image URL utils
provides:
  - Fuse.js fuzzy hero search utility with hybrid matching (substring + initials + fuzzy)
  - Behavioral test suite for hero search (6 tests)
  - useHeroes hook for fetching and caching hero list from API
  - HeroPortrait component rendering Steam CDN hero images with attribute dots
  - HeroPicker searchable dropdown with excludedHeroIds prop for Phase 2 multi-picker
  - End-to-end Zustand wiring from Sidebar hero selection to MainPanel display
affects: [02-draft-inputs, 04-item-timeline]

# Tech tracking
tech-stack:
  added: [fuse.js 7.1.0]
  patterns: [hybrid search combining substring/initials/Fuse.js fuzzy matching, excludedHeroIds prop pattern for multi-picker reuse, useRef+mousedown for click-outside dropdown dismissal]

key-files:
  created:
    - prismlab/frontend/src/utils/heroSearch.ts
    - prismlab/frontend/src/utils/heroSearch.test.ts
    - prismlab/frontend/src/hooks/useHeroes.ts
    - prismlab/frontend/src/components/draft/HeroPortrait.tsx
    - prismlab/frontend/src/components/draft/HeroPicker.tsx
  modified:
    - prismlab/frontend/src/components/layout/Sidebar.tsx
    - prismlab/frontend/src/components/layout/MainPanel.tsx

key-decisions:
  - "Hybrid search (substring + initials + Fuse.js fuzzy) instead of pure Fuse.js -- abbreviation matching like 'am' to 'Anti-Mage' requires substring/initials fallback"
  - "HeroSearcher interface wrapping Fuse instance to fix TypeScript compilation issues with Fuse.js type exports"
  - "excludedHeroIds as Set<number> prop on HeroPicker -- prepares multi-picker pattern for Phase 2 without coupling to store"

patterns-established:
  - "Hybrid search pattern: substring match first, then initials match, then Fuse.js fuzzy -- covers abbreviations that fuzzy alone misses"
  - "HeroPicker excludedHeroIds prop: greyed-out heroes sorted to bottom, not clickable -- reusable for ally/opponent pickers in Phase 2"
  - "useHeroes hook pattern: fetch-on-mount with cancelled flag cleanup for safe async state updates"

requirements-completed: [DRFT-01]

# Metrics
duration: 5min
completed: 2026-03-21
---

# Phase 01 Plan 03: Hero Picker Summary

**Fuse.js hero picker with hybrid fuzzy search (substring + initials + fuzzy), Steam CDN portraits, attribute dots, and Zustand-wired selection**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-21T19:01:02Z
- **Completed:** 2026-03-21T19:03:35Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 7

## Accomplishments
- Hero search utility with hybrid matching strategy (substring, initials, Fuse.js fuzzy) that correctly handles Dota abbreviations like "am" for Anti-Mage
- 6 behavioral tests verifying fuzzy search accuracy for partial names, abbreviations, and edge cases (empty/whitespace)
- HeroPicker component with searchable dropdown, click-outside dismissal, Escape key support, and excludedHeroIds prop ready for Phase 2
- HeroPortrait component rendering Steam CDN images with colored attribute dots, size variants, and disabled state
- End-to-end Zustand wiring: selecting a hero in the Sidebar HeroPicker updates the MainPanel display

## Task Commits

Each task was committed atomically:

1. **Task 1: Hero search utility with behavioral tests, useHeroes hook, HeroPortrait, and HeroPicker components** - `b9072d0` (test: TDD RED), `cc5bb44` (feat: TDD GREEN + components)
2. **Task 2: Wire HeroPicker into Sidebar and verify full build** - `b391341` (feat)
3. **Task 3: Visual verification checkpoint** - No commit (human-verify checkpoint, approved by user)

## Files Created/Modified
- `prismlab/frontend/src/utils/heroSearch.ts` - Hybrid search: substring + initials + Fuse.js fuzzy matching with HeroSearcher wrapper
- `prismlab/frontend/src/utils/heroSearch.test.ts` - 6 behavioral tests for search accuracy (am->Anti-Mage, jug->Juggernaut, crystal->Crystal Maiden, empty/whitespace)
- `prismlab/frontend/src/hooks/useHeroes.ts` - Fetch and cache hero list from /api/heroes with loading/error states
- `prismlab/frontend/src/components/draft/HeroPortrait.tsx` - Hero image from Steam CDN, colored attribute dot, sm/lg sizes, disabled state
- `prismlab/frontend/src/components/draft/HeroPicker.tsx` - Searchable dropdown with fuzzy filtering, selection, clear, excludedHeroIds prop, click-outside/Escape dismissal
- `prismlab/frontend/src/components/layout/Sidebar.tsx` - Updated to include HeroPicker with "Your Hero" heading
- `prismlab/frontend/src/components/layout/MainPanel.tsx` - Updated to show selected hero name from Zustand store

## Decisions Made
- Hybrid search strategy instead of pure Fuse.js: Fuse.js threshold was too strict for Dota abbreviation matching ("am" -> "Anti-Mage"). Added substring matching and initials matching as higher-priority layers before Fuse.js fuzzy as fallback.
- Created HeroSearcher interface wrapping the Fuse instance to resolve TypeScript compilation errors with Fuse.js named type exports.
- Designed excludedHeroIds as a Set<number> prop rather than reading from store -- keeps HeroPicker decoupled and reusable for the 3 different picker instances needed in Phase 2 (your hero, allies, opponents).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fuse.js threshold too strict for abbreviation matching**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Pure Fuse.js with threshold 0.4 could not match "am" to "Anti-Mage" -- the query is too short relative to the target for fuzzy distance scoring
- **Fix:** Implemented hybrid search: substring match (case-insensitive includes) runs first, then initials match (first letters of hyphenated/spaced words), then Fuse.js fuzzy as fallback. Results are deduplicated.
- **Files modified:** prismlab/frontend/src/utils/heroSearch.ts
- **Verification:** All 6 behavioral tests pass including "am" -> Anti-Mage
- **Committed in:** cc5bb44 (Task 1 GREEN commit)

**2. [Rule 3 - Blocking] TypeScript compilation errors with Fuse.js types**
- **Found during:** Task 1 (TDD GREEN phase)
- **Issue:** Fuse.js default export type caused "is not a constructor" and type inference failures with strict TypeScript
- **Fix:** Created HeroSearcher interface wrapping the Fuse instance, used named imports for Fuse options type
- **Files modified:** prismlab/frontend/src/utils/heroSearch.ts
- **Verification:** `npx tsc --noEmit` passes cleanly
- **Committed in:** cc5bb44 (Task 1 GREEN commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes were necessary for correctness. The hybrid search is actually superior to pure Fuse.js for Dota hero name patterns. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 is now complete: backend with seeded data, frontend with dark theme, hero picker with fuzzy search
- Ready for Phase 2 (draft inputs: allies, opponents, role, playstyle, side, lane selectors)
- Ready for Phase 3 (recommendation engine: rules + Claude API hybrid)
- HeroPicker's excludedHeroIds prop is ready for Phase 2 multi-picker pattern
- Docker Compose runs full application on ports 8420/8421

## Self-Check: PASSED

All 5 created files verified present on disk. All 2 modified files verified present on disk. All 3 task commits (b9072d0, cc5bb44, b391341) verified in git log.

---
*Phase: 01-foundation*
*Completed: 2026-03-21*
