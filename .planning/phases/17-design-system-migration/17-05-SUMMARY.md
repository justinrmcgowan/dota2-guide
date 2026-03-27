---
phase: 17-design-system-migration
plan: 05
subsystem: ui
tags: [css, tailwind, design-system, texture, audit, cleanup]

# Dependency graph
requires:
  - phase: 17-02-PLAN
    provides: "Component migration to new tokens (wave 1)"
  - phase: 17-03-PLAN
    provides: "Component migration to new tokens (wave 2a)"
  - phase: 17-04-PLAN
    provides: "Component migration to new tokens (wave 2b)"
provides:
  - "Parchment noise texture overlay on base background"
  - "Zero deprecated token references across codebase"
  - "Clean globals.css without bridge tokens"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: ["SVG feTurbulence data URI for noise texture at 3.5% opacity"]

key-files:
  modified:
    - "prismlab/frontend/src/styles/globals.css"
    - "prismlab/frontend/src/App.tsx"
    - "prismlab/frontend/src/components/timeline/ItemCard.tsx"
    - "prismlab/frontend/src/components/screenshot/ParsedHeroRow.tsx"

key-decisions:
  - "SVG feTurbulence noise via data URI (~200 bytes) instead of external asset for zero-dependency texture"
  - "3.5% opacity provides subtle grain without affecting text readability"
  - "z-10 on main content flex container ensures content stacks above fixed noise overlay"

patterns-established:
  - "Noise overlay uses ::before pseudo-element with fixed positioning and pointer-events:none"

requirements-completed: [DESIGN-07, DESIGN-08]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 17 Plan 05: Cleanup & Audit Summary

**Parchment noise texture overlay via SVG feTurbulence, deprecated bridge tokens removed, full visual audit confirms zero old token references across all components**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T01:39:16Z
- **Completed:** 2026-03-27T01:44:01Z
- **Tasks:** 2 of 3 (Task 3 is visual verification checkpoint)
- **Files modified:** 4

## Accomplishments
- Added SVG feTurbulence parchment noise texture at 3.5% opacity on base #131313 background, preventing the "sterile" look per DESIGN.md Section 6
- Removed all 6 deprecated bridge tokens from globals.css (cyan-accent, bg-primary, bg-secondary, bg-elevated, text-muted, font-stats)
- Full visual audit confirmed zero instances of: old color tokens, text-white, #FFFFFF, rounded-lg/md/xl/2xl, blue links (text-blue/sky/indigo), font-mono across all .tsx/.ts files
- Fixed 2 text-white instances (ItemCard checkmark, ParsedHeroRow remove button) to text-on-surface per DESIGN.md "Don't use 100% white"
- Documented all 12 rounded-full exceptions as functional (checkmarks, status dots, avatars, badges, spinners, remove buttons)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add parchment noise texture and remove deprecated token aliases** - `584e56e` (feat)
2. **Task 2: Full visual audit -- grep for all old tokens and fix stragglers** - `41e4c40` (fix)
3. **Task 3: Human visual verification** - PENDING (checkpoint:human-verify)

## Files Created/Modified
- `prismlab/frontend/src/styles/globals.css` - Added noise-overlay CSS, removed 6 deprecated token aliases and font-stats
- `prismlab/frontend/src/App.tsx` - Added noise-overlay and relative classes to root div, z-10 to content container
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` - Replaced text-white with text-on-surface on purchased checkmark SVG
- `prismlab/frontend/src/components/screenshot/ParsedHeroRow.tsx` - Replaced text-white with text-on-surface and hover:bg-red-400 with hover:bg-dire/80 on remove button

## Decisions Made
- Used SVG feTurbulence as inline data URI (~200 bytes) rather than an external PNG/SVG asset. Zero network requests, zero build dependency, works in all modern browsers.
- Set opacity at 3.5% (0.035) -- this adds visible grain at close inspection without interfering with text readability or creating a distracting pattern.
- Applied z-10 to the main content flex container to ensure all child content renders above the fixed noise overlay pseudo-element.

## Deviations from Plan

None - plan executed exactly as written.

## Visual Audit Results

### Old Color Tokens (ZERO matches)
- `cyan-accent` in .tsx/.ts: 0
- `bg-primary` (standalone, not bg-primary-container): 0
- `bg-secondary` (standalone, not bg-secondary-container): 0 (bg-secondary/10 and bg-secondary are NEW secondary gold token references)
- `bg-elevated`: 0
- `text-muted`: 0

### Hardcoded White (ZERO matches after fix)
- `text-white`: 0 (fixed 2 instances -> text-on-surface)
- `#FFFFFF` / `#ffffff`: 0

### Non-Exempt Rounded Corners (ZERO matches)
- `rounded-lg`: 0
- `rounded-md`: 0
- `rounded-xl`: 0
- `rounded-2xl`: 0

### Blue Links (ZERO matches)
- `text-blue`: 0
- `text-sky`: 0
- `text-indigo`: 0

### Old Font References (ZERO matches)
- `font-mono`: 0
- `font-stats`: 0

### Documented rounded-full Exceptions (12 instances, all functional)
1. LaneOpponentPicker: hero avatar circle (D-05: avatar)
2. GsiStatusIndicator: WebSocket status dot (D-05: status dot)
3. ScreenshotParser: loading spinner (D-05: functional)
4. HeroSlot x3: circular hero slot placeholder/portrait/overlay (D-05: functional)
5. ItemCard: purchased checkmark overlay (D-04)
6. ParsedHeroRow: low confidence badge dot (D-05: badge)
7. ParsedHeroRow: remove button circle (D-05: action affordance)
8. NeutralItemSection: rank badge circle (D-05: rank indicator)
9. HeroPortrait: attribute dot (D-05: status dot)

### Documented rounded (base) Exceptions (7 instances, all avatar softening)
- HeroPortrait, MainPanel, DecisionTreeCard, ItemCard, NeutralItemSection, ParsedHeroRow x2: hero/item image softening (D-05: avatar)

## Issues Encountered

Pre-existing TypeScript errors in test files (GameClock.test.tsx, LiveStatsBar.test.tsx, GsiStatusIndicator.test.tsx, useGameIntelligence.test.ts, recommendationStore.test.ts, itemMatching.test.ts, triggerDetection.test.ts) due to missing properties in GsiLiveState and RecommendResponse type fixtures. These are NOT caused by this plan's changes and are out of scope. `npx vite build` succeeds; only `tsc -b` fails on test files.

## Known Stubs

None - no stubs introduced by this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Task 3 (visual verification checkpoint) remains pending -- user needs to inspect the design system in-browser
- All automated work for Phase 17 design system migration is complete
- Ready for Phase 18+ work (in-memory data cache, GSI integration gaps, tech debt cleanup)

---
*Phase: 17-design-system-migration*
*Completed: 2026-03-27*
