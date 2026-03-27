---
phase: 17-design-system-migration
plan: 04
subsystem: ui
tags: [tailwind, design-system, blood-glass, backdrop-blur, crimson-glow, modal, toast, panel]

# Dependency graph
requires:
  - phase: 17-01
    provides: "Design tokens in globals.css @theme block (surface hierarchy, crimson/gold palette, shadow-glow, 0px radii)"
provides:
  - "Blood-glass overlay pattern on SettingsPanel and ScreenshotParser modals"
  - "Ambient crimson glow (shadow-glow) on all floating elements"
  - "Sacrificial Table input pattern on GSI config inputs and item search"
  - "Crimson tonal ErrorBanner and gold tonal fallback warning"
  - "Performance-safe solid toast (no backdrop-blur per Pitfall 13)"
affects: [17-05-audit, future-modal-components]

# Tech tracking
tech-stack:
  added: []
  patterns: ["blood-glass overlay (primary-container + backdrop-blur-md)", "Pitfall 13: no backdrop-blur on high-frequency toasts", "Sacrificial Table (surface-container-lowest + bottom border only)", "Blade button (primary-container + gold ghost outline on hover)"]

key-files:
  created: []
  modified:
    - prismlab/frontend/src/components/settings/SettingsPanel.tsx
    - prismlab/frontend/src/components/screenshot/ScreenshotParser.tsx
    - prismlab/frontend/src/components/screenshot/ParsedHeroRow.tsx
    - prismlab/frontend/src/components/screenshot/ItemEditPicker.tsx
    - prismlab/frontend/src/components/toast/AutoRefreshToast.tsx
    - prismlab/frontend/src/components/timeline/ErrorBanner.tsx

key-decisions:
  - "Blood-glass backdrop uses primary-container/25 for slide-over, /30 for modal (heavier overlay for centered modals)"
  - "Toast uses solid bg-surface-container-highest instead of backdrop-blur per Pitfall 13 (1Hz GSI updates cause frame drops)"
  - "ErrorBanner error type uses crimson tonal (primary-container/15), fallback uses gold tonal (secondary/10) to differentiate severity"

patterns-established:
  - "Blood-glass overlay: bg-primary-container/[20-40] backdrop-blur-md on modal/panel backdrops"
  - "Floating element: bg-surface-container-highest shadow-glow, no rounded corners, no border dividers"
  - "Sacrificial Table input: bg-surface-container-lowest border-b border-outline-variant/15, no side/top borders, no rounded"
  - "Blade button: bg-primary-container text-on-surface, hover:outline hover:outline-1 hover:outline-[#AA8986]"

requirements-completed: [DESIGN-04, DESIGN-06]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 17 Plan 04: Floating Elements Migration Summary

**Blood-glass overlays with ambient crimson glow on all floating elements (modals, panels, toasts, banners) using surface-container-highest and backdrop-blur-md**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T01:29:07Z
- **Completed:** 2026-03-27T01:34:14Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- SettingsPanel and ScreenshotParser modals now use blood-glass backdrop (primary_container at 25-30% opacity + backdrop-blur 12px) with surface-container-highest panels
- All floating elements (modals, toasts, picker dropdowns) emit ambient crimson glow via shadow-glow token
- AutoRefreshToast uses solid background (no backdrop-blur) per Pitfall 13 to avoid frame drops during 1Hz GSI updates
- ErrorBanner differentiates error severity: crimson tonal for errors, gold tonal for fallback warnings
- All inputs follow Sacrificial Table pattern (recessed surface-container-lowest, bottom border only)
- Zero cyan-accent references remain across all 6 modified files

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate SettingsPanel and ScreenshotParser (blood-glass modals)** - `be8bb2d` (feat)
2. **Task 2: Migrate AutoRefreshToast and ErrorBanner** - `a2f4293` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `prismlab/frontend/src/components/settings/SettingsPanel.tsx` - Blood-glass slide-over with Sacrificial Table inputs and Blade download button
- `prismlab/frontend/src/components/screenshot/ScreenshotParser.tsx` - Blood-glass modal with surface-container-highest, No-Line Rule applied to header/footer
- `prismlab/frontend/src/components/screenshot/ParsedHeroRow.tsx` - Surface-container-high rows, design token colors, kept rounded on portraits per D-05
- `prismlab/frontend/src/components/screenshot/ItemEditPicker.tsx` - Surface-container-highest dropdown with shadow-glow and Sacrificial Table search input
- `prismlab/frontend/src/components/toast/AutoRefreshToast.tsx` - Solid surface-container-highest with shadow-glow, gold icon/title, no backdrop-blur
- `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` - Crimson tonal error surface, gold tonal fallback surface, no rounded corners

## Decisions Made
- Blood-glass backdrop opacity differentiated by context: 25% for slide-over (lighter, peripheral), 30% for modal (heavier, central focus)
- Toast deliberately avoids backdrop-blur per Pitfall 13 -- it appears during 1Hz GSI polling and blur causes compositor overhead
- ErrorBanner error vs fallback uses different palette families (crimson vs gold) to communicate severity visually

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing TypeScript errors in unrelated test files (GameClock.test.tsx, LiveStatsBar.test.tsx, triggerDetection.test.ts) cause `tsc -b` to fail. These are from prior phases adding new GsiLiveState fields without updating test fixtures. Vite build succeeds (production code compiles cleanly). Logged as pre-existing -- not caused by this plan's changes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All floating elements now use DESIGN.md tokens consistently
- Ready for 17-05 audit to verify zero legacy token references remain across the full frontend
- Patterns established here (blood-glass, Sacrificial Table, Blade button) serve as templates for any future modal/panel components

## Self-Check: PASSED

- All 7 files verified present on disk
- Commit be8bb2d (Task 1) verified in git log
- Commit a2f4293 (Task 2) verified in git log

---
*Phase: 17-design-system-migration*
*Completed: 2026-03-27*
