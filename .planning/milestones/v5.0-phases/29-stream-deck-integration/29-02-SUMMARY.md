---
phase: 29-stream-deck-integration
plan: "02"
subsystem: infra
tags: [stream-deck, typescript, svg, elgato-sdk, dota2, websocket]

# Dependency graph
requires:
  - phase: 29-01
    provides: BackendConnection singleton, GsiState interface, stub action files, plugin.ts entry point

provides:
  - GoldAction SingletonAction with gold/GPM SVG display (com.prismlab.dota2.gold)
  - KdaAction SingletonAction with K/D/A + level SVG display (com.prismlab.dota2.kda)
  - ClockAction SingletonAction with MM:SS / PRE + DAY/NIGHT SVG display (com.prismlab.dota2.clock)
  - ItemsAction SingletonAction with 3x2 inventory grid SVG display (com.prismlab.dota2.items)
  - RoshAction SingletonAction with ALIVE/DEAD/unknown Roshan status SVG (com.prismlab.dota2.rosh)
  - TowersAction SingletonAction with radiant vs dire tower count SVG (com.prismlab.dota2.towers)
  - Clean TypeScript build producing com.prismlab.dota2.sdPlugin/bin/plugin.js

affects:
  - stream-deck plugin deployment
  - plugin.ts entry point (all 6 actions registered and wired)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SingletonAction subclass pattern: @action UUID decorator + onWillAppear + handleState + this.actions.forEach setImage"
    - "SVG data URL rendering: buildXxxSvg() -> setImage(data:image/svg+xml, encodeURIComponent(svg))"
    - "TC39 stage-3 decorators: tsconfig without experimentalDecorators to match @elgato/streamdeck SDK expectations"

key-files:
  created:
    - prismlab/stream-deck-plugin/src/actions/gold-action.ts
    - prismlab/stream-deck-plugin/src/actions/kda-action.ts
    - prismlab/stream-deck-plugin/src/actions/clock-action.ts
    - prismlab/stream-deck-plugin/src/actions/items-action.ts
    - prismlab/stream-deck-plugin/src/actions/rosh-action.ts
    - prismlab/stream-deck-plugin/src/actions/towers-action.ts
  modified:
    - prismlab/stream-deck-plugin/tsconfig.json
    - prismlab/stream-deck-plugin/src/plugin.ts

key-decisions:
  - "Removed experimentalDecorators from tsconfig — SDK uses TC39 stage-3 ClassDecoratorContext signature, legacy mode incompatible"
  - "Fixed plugin.ts onDidReceiveGlobalSettings to use .settings directly (not .payload.settings) per SDK event type"
  - "SVG size kept minimal (under 500 bytes each) by using abbreviated labels, small font sizes, and no path/shape elements beyond background rect"
  - "Clock formatClock returns PRE for negative seconds (pre-game), avoiding negative MM:SS display"

patterns-established:
  - "All 6 actions follow identical SingletonAction pattern: @action decorator, onWillAppear for immediate render, handleState for live updates, _render private via this.actions.forEach"
  - "SVG color coding: #6aff97 Radiant/positive, #ff5555 Dire/negative/threat, #FFD700 gold, #00d4ff time/info, #888 muted/unknown"

requirements-completed: [SDECK-03, SDECK-04, SDECK-05, SDECK-06]

# Metrics
duration: 5min
completed: 2026-03-29
---

# Phase 29 Plan 02: Stream Deck Action Implementations Summary

**6 SingletonAction classes with SVG renderers wired to live Dota 2 GSI data via BackendConnection, compiling cleanly with zero TypeScript errors**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-29T11:28:53Z
- **Completed:** 2026-03-29T11:33:04Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Implemented all 6 Stream Deck XL action classes as SingletonAction subclasses with correct UUID decorators
- Each action renders live Dota 2 data as compact SVG images onto buttons via setImage() data URLs
- Fixed two pre-existing bugs in Plan 01 outputs (tsconfig decorator mode, plugin.ts payload access), enabling a clean TypeScript build

## Task Commits

1. **Task 1: Gold, KDA, Clock actions** - `d1dee67` (feat)
2. **Task 2: Items, Rosh, Towers actions + build fixes** - `faaed00` (feat)

## Files Created/Modified

- `prismlab/stream-deck-plugin/src/actions/gold-action.ts` - Gold amount (Xk format) + GPM, gold color dims when dead
- `prismlab/stream-deck-plugin/src/actions/kda-action.ts` - K/D/A with color highlights (green kills >=10, red deaths >=5) + hero level
- `prismlab/stream-deck-plugin/src/actions/clock-action.ts` - Game clock: PRE pre-game, MM:SS live, DAY/NIGHT phase indicator
- `prismlab/stream-deck-plugin/src/actions/items-action.ts` - 3x2 inventory grid, item names stripped of prefixes/underscores, empty slots as "---"
- `prismlab/stream-deck-plugin/src/actions/rosh-action.ts` - Roshan status: ALIVE (green), DEAD (red), unknown (gray)
- `prismlab/stream-deck-plugin/src/actions/towers-action.ts` - Radiant (green) vs Dire (red) tower count side-by-side
- `prismlab/stream-deck-plugin/tsconfig.json` - Removed experimentalDecorators for TC39 stage-3 decorator compatibility
- `prismlab/stream-deck-plugin/src/plugin.ts` - Fixed onDidReceiveGlobalSettings to use .settings (not .payload.settings)

## Decisions Made

- **TC39 decorators**: Removed `experimentalDecorators: true` from tsconfig. The `@elgato/streamdeck` SDK exports decorators typed with `ClassDecoratorContext` (new TC39 stage-3 standard), incompatible with TypeScript's legacy `experimentalDecorators` mode which expects a 2-argument signature.
- **SVG budget**: All SVGs kept under 500 bytes using minimal element counts (1 background rect + 2-6 text elements), abbreviated labels, and no vector icons.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript decorator errors from tsconfig experimentalDecorators**
- **Found during:** Task 2 (npm run build after implementing all 6 actions)
- **Issue:** tsconfig had `"experimentalDecorators": true` but `@elgato/streamdeck` SDK uses TC39 stage-3 decorator signature (`ClassDecoratorContext`). Legacy mode caused TS1238 errors on all 6 `@action()` decorators.
- **Fix:** Removed `experimentalDecorators` and `emitDecoratorMetadata` from tsconfig.json
- **Files modified:** prismlab/stream-deck-plugin/tsconfig.json
- **Verification:** npm run build produces clean output with no TypeScript errors
- **Committed in:** faaed00 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed plugin.ts onDidReceiveGlobalSettings payload access**
- **Found during:** Task 2 (npm run build)
- **Issue:** `DidReceiveGlobalSettingsEvent<T>` exposes `.settings: T` directly, but plugin.ts was destructuring `{ payload }` which doesn't exist on the event type. Caused TS2339 error.
- **Fix:** Changed destructuring from `{ payload }` to `{ settings }` and removed the `.settings` indirection
- **Files modified:** prismlab/stream-deck-plugin/src/plugin.ts
- **Verification:** TypeScript accepts the code, build clean
- **Committed in:** faaed00 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs in Plan 01 output files)
**Impact on plan:** Both fixes required for a clean TypeScript build. No scope creep — both issues were in files already introduced by Plan 01.

## Issues Encountered

- build artifact `com.prismlab.dota2.sdPlugin/bin/` is gitignored (standard for compiled output) — build verified locally, not committed to repo.

## Next Phase Readiness

- All 6 action classes are fully implemented and building cleanly
- Plugin is ready for developer-machine testing: `streamdeck link` and `streamdeck pack` steps are documented in the phase README
- Phase 29 is complete — both plans executed

---
*Phase: 29-stream-deck-integration*
*Completed: 2026-03-29*
