---
phase: 17-design-system-migration
plan: 01
subsystem: ui
tags: [tailwind-v4, css-custom-properties, fonts, design-tokens, newsreader, manrope]

# Dependency graph
requires: []
provides:
  - Complete DESIGN.md token set in @theme block (surfaces, accents, text, shadows, radii)
  - Variable font imports for Newsreader (display) and Manrope (body/stats)
  - Deprecated color aliases bridging old token names to new palette
affects: [17-02, 17-03, 17-04, 17-05]

# Tech tracking
tech-stack:
  added: ["@fontsource-variable/newsreader", "@fontsource-variable/manrope"]
  removed: ["@fontsource/inter", "@fontsource/jetbrains-mono"]
  patterns: ["CSS @theme block as single source of truth for all design tokens", "Deprecated aliases for safe incremental migration"]

key-files:
  created: []
  modified:
    - prismlab/frontend/src/styles/globals.css
    - prismlab/frontend/src/main.tsx
    - prismlab/frontend/package.json
    - prismlab/frontend/package-lock.json

key-decisions:
  - "Deprecated color aliases (cyan-accent, bg-primary, bg-secondary, bg-elevated, text-muted) remapped to new palette equivalents rather than removed, preventing invisible text per DESIGN.md Pitfall 6"
  - "All --radius-* tokens set to explicit 0px rather than 'initial' for reliable Tailwind v4 resolution"
  - "--font-stats remapped to Manrope Variable with tnum feature settings instead of JetBrains Mono"

patterns-established:
  - "Token bridge pattern: deprecated aliases map to new palette values during incremental migration"
  - "Variable fonts: single import per typeface covers all weights"

requirements-completed: [DESIGN-01, DESIGN-02]

# Metrics
duration: 2min
completed: 2026-03-27
---

# Phase 17 Plan 01: Token Foundation Summary

**Newsreader + Manrope variable fonts installed, @theme block replaced with full DESIGN.md obsidian surface hierarchy, crimson/gold/slate accents, ambient glow shadows, and 0px radius overrides**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T01:23:57Z
- **Completed:** 2026-03-27T01:26:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Swapped 2 static font packages (Inter, JetBrains Mono) for 2 variable font packages (Newsreader, Manrope), reducing 6 CSS imports to 2
- Replaced the entire @theme block with 60+ design tokens covering surfaces, accents, text, shadows, fonts, and radii
- Preserved game colors (radiant/dire) and attribute colors unchanged
- Deprecated aliases bridge existing components to the new palette without breakage

## Task Commits

Each task was committed atomically:

1. **Task 1: Swap font packages and update imports** - `37aff9d` (feat)
2. **Task 2: Replace @theme block with full DESIGN.md token set** - `d5444e2` (feat)

## Files Created/Modified
- `prismlab/frontend/package.json` - Replaced @fontsource/inter and @fontsource/jetbrains-mono with @fontsource-variable/newsreader and @fontsource-variable/manrope
- `prismlab/frontend/package-lock.json` - Lock file updated for new font dependencies
- `prismlab/frontend/src/main.tsx` - 2 variable font imports replacing 6 static weight imports
- `prismlab/frontend/src/styles/globals.css` - Complete @theme block with DESIGN.md token set (8 surface tones, crimson/gold/slate palette, text/outline tokens, typography stacks, ambient glow shadows, 0px radii, deprecated bridge aliases)

## Decisions Made
- **Deprecated aliases kept as bridge tokens:** `cyan-accent`, `bg-primary`, `bg-secondary`, `bg-elevated`, `text-muted` now map to new palette equivalents. This prevents invisible text or broken styling in components that still reference old token names. Will be removed in Plan 05 after a grep confirms zero references.
- **Explicit 0px for all radius tokens:** Using `0px` instead of `initial` or removing the tokens entirely, because Tailwind v4's @theme resolution is more reliable with explicit values.
- **Manrope replaces JetBrains Mono for stats:** DESIGN.md specifies Manrope with `font-feature-settings: "tnum"` for tabular numbers, replacing the monospace approach.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing TypeScript errors in test files (missing properties on GsiLiveState and RecommendResponse mocks, type-only import issues) cause `tsc -b` to fail. These are unrelated to the design token migration. The Vite build (CSS + JS bundling) succeeds. Logged to `deferred-items.md` for future resolution.

## Known Stubs

None - all tokens are fully wired values, no placeholders.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Token foundation is complete; all subsequent plans (17-02 through 17-05) can reference the new color, font, shadow, and radius tokens
- Components using old class names (bg-cyan-accent, bg-bg-primary, etc.) will continue working via deprecated bridge aliases
- Pre-existing TypeScript test errors should be addressed before production builds

---
*Phase: 17-design-system-migration*
*Completed: 2026-03-27*
