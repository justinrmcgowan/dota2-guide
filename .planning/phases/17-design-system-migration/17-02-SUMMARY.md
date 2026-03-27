---
phase: 17-design-system-migration
plan: 02
subsystem: ui
tags: [tailwind-v4, design-tokens, surface-hierarchy, component-migration, blade-pattern, sacrificial-table]

# Dependency graph
requires:
  - phase: 17-01
    provides: "Complete DESIGN.md token set in @theme block (surfaces, accents, text, shadows, radii)"
provides:
  - "Layout shell (App, Header, Sidebar, MainPanel) using obsidian surface hierarchy"
  - "All draft-input components using primary/secondary accents instead of cyan"
  - "GetBuildButton following Blade pattern with primary-container background"
  - "HeroPicker search input following Sacrificial Table pattern"
  - "Zero cyan-accent references in layout, clock, and draft components"
affects: [17-03, 17-04, 17-05]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Surface hierarchy: lowest(sidebar) < low(header) < surface(main)", "Blade pattern: primary-container bg + gold-leaf outline on hover", "Sacrificial Table: recessed input with underline-only border", "Ghost border: outline-variant/15 on inactive toggles"]

key-files:
  created: []
  modified:
    - prismlab/frontend/src/App.tsx
    - prismlab/frontend/src/components/layout/Header.tsx
    - prismlab/frontend/src/components/layout/Sidebar.tsx
    - prismlab/frontend/src/components/layout/MainPanel.tsx
    - prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx
    - prismlab/frontend/src/components/clock/GameClock.tsx
    - prismlab/frontend/src/components/draft/RoleSelector.tsx
    - prismlab/frontend/src/components/draft/PlaystyleSelector.tsx
    - prismlab/frontend/src/components/draft/SideSelector.tsx
    - prismlab/frontend/src/components/draft/LaneSelector.tsx
    - prismlab/frontend/src/components/draft/LaneOpponentPicker.tsx
    - prismlab/frontend/src/components/draft/GetBuildButton.tsx
    - prismlab/frontend/src/components/draft/HeroPicker.tsx
    - prismlab/frontend/src/components/draft/HeroPortrait.tsx
    - prismlab/frontend/src/components/draft/HeroSlot.tsx
    - prismlab/frontend/src/utils/constants.ts

key-decisions:
  - "Kept border utility on toggle buttons for state communication but using ghost-border colors (outline-variant/15 inactive, primary/40 active)"
  - "SVG prism gradient rethemed from cyan (#00d4ff) to crimson (#FFB4AC) + radiant (#6aff97)"
  - "GameClock uses font-body with tabular-nums instead of font-mono (Manrope tnum replaces JetBrains Mono)"
  - "Sidebar CTA area uses bg-surface-container-low tonal shift instead of border-t for visual separation"

patterns-established:
  - "Toggle button pattern: active=primary-container/20+primary, inactive=surface-container-high+outline-variant/15"
  - "No-Line Rule applied: layout borders replaced with background color shifts"
  - "D-05 functional exceptions: rounded-full preserved on status dots, hero avatars, slot placeholders"

requirements-completed: [DESIGN-03]

# Metrics
duration: 6min
completed: 2026-03-27
---

# Phase 17 Plan 02: Layout Shell & Draft Component Migration Summary

**Obsidian surface hierarchy applied across App/Header/Sidebar/MainPanel shell; all 11 draft-input components and constants migrated from cyan-accent to crimson/gold primary/secondary tokens with Blade and Sacrificial Table patterns**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-27T01:28:50Z
- **Completed:** 2026-03-27T01:35:41Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Established the three-tier surface hierarchy: Sidebar (#0E0E0E) < Header (#1C1B1B) < MainPanel (#131313) with no 1px borders on layout containers
- Migrated Prismlab title from cyan to gold (text-secondary) with Newsreader font-display and tight tracking
- Converted all toggle/radio button components from cyan-accent to primary-container/primary accents while preserving radiant/dire game colors on SideSelector
- GetBuildButton now follows the Blade pattern (primary-container bg, gold-leaf outline on hover, glow-active shadow)
- HeroPicker search input follows Sacrificial Table pattern (recessed surface-container-lowest with underline-only border)
- Eliminated all cyan-accent references from layout, clock, draft components, and constants

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate layout shell (App, Header, Sidebar, MainPanel, GsiStatusIndicator, GameClock)** - `548c554` (feat)
2. **Task 2: Migrate all draft-input components and constants** - `f0ceb09` (feat)

## Files Created/Modified
- `prismlab/frontend/src/App.tsx` - Root shell: bg-surface + text-on-surface
- `prismlab/frontend/src/components/layout/Header.tsx` - surface-container-low bg, gold title, crimson prism SVG, no border-b
- `prismlab/frontend/src/components/layout/Sidebar.tsx` - surface-container-lowest bg, on-surface-variant headings, tonal CTA area
- `prismlab/frontend/src/components/layout/MainPanel.tsx` - bg-surface, font-display hero name, on-surface-variant text
- `prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx` - text-on-surface-variant label
- `prismlab/frontend/src/components/clock/GameClock.tsx` - text-secondary gold, font-body tabular-nums
- `prismlab/frontend/src/components/draft/RoleSelector.tsx` - Primary toggle pattern, no rounded-md
- `prismlab/frontend/src/components/draft/PlaystyleSelector.tsx` - Primary toggle pattern, no rounded-md
- `prismlab/frontend/src/components/draft/LaneSelector.tsx` - Primary toggle pattern, no rounded-md
- `prismlab/frontend/src/components/draft/SideSelector.tsx` - Preserved radiant/dire, updated inactive state
- `prismlab/frontend/src/components/draft/LaneOpponentPicker.tsx` - Primary toggle pattern, kept rounded-full hero icons
- `prismlab/frontend/src/components/draft/GetBuildButton.tsx` - Blade pattern: primary-container bg, gold-leaf hover outline
- `prismlab/frontend/src/components/draft/HeroPicker.tsx` - Sacrificial Table input, surface-container-low dropdown
- `prismlab/frontend/src/components/draft/HeroPortrait.tsx` - ring-secondary-fixed selection, on-surface text
- `prismlab/frontend/src/components/draft/HeroSlot.tsx` - outline-variant borders, on-surface-variant text
- `prismlab/frontend/src/utils/constants.ts` - LANE_RESULT_OPTIONS "even" uses text-primary

## Decisions Made
- **Ghost border on toggle buttons:** Kept `border` utility for toggle state communication (active: primary/40, inactive: outline-variant/15) rather than removing borders entirely -- toggles need visible state differentiation per WCAG.
- **SVG prism retheme:** Replaced cyan (#00d4ff) with crimson (#FFB4AC) in the header prism gradient while keeping radiant green (#6aff97) for visual interest.
- **GameClock tabular-nums:** Used font-body with `tabular-nums` class instead of font-mono, since DESIGN.md specifies Manrope with tnum feature settings for numeric data.
- **Sidebar CTA tonal shift:** Replaced `border-t border-bg-elevated` with `bg-surface-container-low` per the No-Line Rule -- depth from color shift, not drawn lines.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing TypeScript errors in test files (GsiLiveState mock incomplete, RecommendResponse missing fallback_reason, type-only import issues) cause `tsc -b` to fail. These are unchanged from 17-01 and unrelated to the design token migration. The Vite build (CSS + JS bundling) succeeds without issue.

## Known Stubs

None - all class name migrations are fully resolved values, no placeholders.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Layout shell and all draft-input components are fully migrated to DESIGN.md tokens
- Plans 17-03 (timeline/game state) and 17-04 (modals/toast/settings) can proceed with the same token patterns established here
- Pre-existing TypeScript test errors should be addressed before production builds

## Self-Check: PASSED

All 16 modified files verified present. Both task commits (548c554, f0ceb09) verified in git log. SUMMARY.md exists at expected path.

---
*Phase: 17-design-system-migration*
*Completed: 2026-03-27*
