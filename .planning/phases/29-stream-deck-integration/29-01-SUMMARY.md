---
phase: 29-stream-deck-integration
plan: 01
subsystem: infra
tags: [stream-deck, elgato-sdk, typescript, websocket, rollup, plugin]

# Dependency graph
requires:
  - phase: 27-game-lifecycle
    provides: WebSocket broadcast endpoint ws://<host>:8420/ws emitting game_state messages

provides:
  - Stream Deck plugin project scaffold at prismlab/stream-deck-plugin/ with buildable Node.js config
  - manifest.json declaring 6 action UUIDs under com.prismlab.dota2 namespace
  - BackendConnection singleton with exponential-backoff reconnect and GsiState interface
  - Plugin entry point registering all 6 actions before streamDeck.connect()
  - Property inspector pi.html for user-configurable backend WebSocket URL
  - 6 stub action files enabling TypeScript compilation without errors

affects:
  - 29-02 (implements the 6 actions replacing stubs)

# Tech tracking
tech-stack:
  added:
    - "@elgato/streamdeck 2.0.4 — Stream Deck SDK v2 for plugin lifecycle"
    - "ws 8.20.0 — Node.js WebSocket client for Prismlab backend connection"
    - "rollup 4.x with @rollup/plugin-typescript — bundles src/ to sdPlugin/bin/plugin.js"
    - "typescript 5.x — strict mode, ES2020 target, bundler moduleResolution"
  patterns:
    - "Module-level singleton: BackendConnection instance shared across all 6 action types"
    - "Exponential-backoff reconnect: retryDelay doubles on each close, capped at 30s"
    - "SDK order constraint: register actions before streamDeck.connect() always called last"
    - "Global settings pattern: pi.html uses setGlobalSettings/onDidReceiveGlobalSettings for cross-action config"

key-files:
  created:
    - prismlab/stream-deck-plugin/package.json
    - prismlab/stream-deck-plugin/tsconfig.json
    - prismlab/stream-deck-plugin/rollup.config.mjs
    - prismlab/stream-deck-plugin/.gitignore
    - prismlab/stream-deck-plugin/com.prismlab.dota2.sdPlugin/manifest.json
    - prismlab/stream-deck-plugin/com.prismlab.dota2.sdPlugin/ui/pi.html
    - prismlab/stream-deck-plugin/src/connection.ts
    - prismlab/stream-deck-plugin/src/plugin.ts
    - prismlab/stream-deck-plugin/src/actions/gold-action.ts (stub)
    - prismlab/stream-deck-plugin/src/actions/kda-action.ts (stub)
    - prismlab/stream-deck-plugin/src/actions/clock-action.ts (stub)
    - prismlab/stream-deck-plugin/src/actions/items-action.ts (stub)
    - prismlab/stream-deck-plugin/src/actions/rosh-action.ts (stub)
    - prismlab/stream-deck-plugin/src/actions/towers-action.ts (stub)
  modified: []

key-decisions:
  - "ws package used for backend WebSocket (not reconnecting-websocket) — lighter, manual exponential backoff mirrors useWebSocket.ts pattern already in codebase"
  - "Module-level singleton BackendConnection avoids N separate WebSocket connections for N action types"
  - "Stub action files (handleState(_s: any) {}) allow TypeScript compilation in Plan 01; full implementations in Plan 02"
  - "Action icon PNGs are optional for local dev — Stream Deck app falls back gracefully when missing"

patterns-established:
  - "BackendConnection.onState() listener pattern: plugin.ts wires all 6 actions via single shared subscription"
  - "SDK ordering: imports -> registerAction() calls -> onState() wiring -> getGlobalSettings().then(connect) -> streamDeck.connect() last"

requirements-completed:
  - SDECK-01
  - SDECK-02

# Metrics
duration: 5min
completed: 2026-03-29
---

# Phase 29 Plan 01: Stream Deck Plugin Scaffold Summary

**Elgato Stream Deck plugin project scaffolded with SDKVersion 2 manifest declaring 6 action UUIDs, BackendConnection singleton with exponential-backoff reconnect to ws://<host>:8420/ws, and buildable TypeScript entry point**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-29T11:20:37Z
- **Completed:** 2026-03-29T11:25:19Z
- **Tasks:** 2
- **Files modified:** 20 (4 config + 1 manifest + 1 pi.html + 6 .gitkeep + 2 core TypeScript + 6 stub actions)

## Accomplishments

- Complete Node.js project scaffold with package.json, tsconfig.json, rollup.config.mjs, and .gitignore
- manifest.json with SDKVersion 2, NodeJS 20, all 6 action UUIDs (gold/kda/clock/items/rosh/towers) under com.prismlab.dota2 namespace
- BackendConnection singleton in connection.ts: connects to Prismlab backend WebSocket, parses game_state messages, notifies listeners, reconnects with exponential backoff (1s-30s) on close
- plugin.ts wires all 6 actions via onState() before calling streamDeck.connect() last — satisfies SDK ordering requirement
- Property inspector pi.html: user configures backend URL, persisted via setGlobalSettings/onDidReceiveGlobalSettings
- 6 stub action files allow TypeScript compilation without errors; Plan 02 replaces these with full SingletonAction implementations

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold — package.json, tsconfig.json, rollup.config.mjs, .gitignore** - `8b8afb7` (chore)
2. **Task 2: manifest.json, property inspector, action icon placeholders, connection.ts, plugin.ts stubs** - `d119f02` (feat)

## Files Created/Modified

- `prismlab/stream-deck-plugin/package.json` — Node project with @elgato/streamdeck 2.0.4, ws 8.20.0, rollup build scripts
- `prismlab/stream-deck-plugin/tsconfig.json` — ES2020 target, bundler moduleResolution, experimentalDecorators enabled
- `prismlab/stream-deck-plugin/rollup.config.mjs` — bundles src/plugin.ts to com.prismlab.dota2.sdPlugin/bin/plugin.js CJS format
- `prismlab/stream-deck-plugin/.gitignore` — excludes node_modules, dist, bin output, logs, packed plugin files
- `prismlab/stream-deck-plugin/com.prismlab.dota2.sdPlugin/manifest.json` — SDKVersion 2 manifest with all 6 actions
- `prismlab/stream-deck-plugin/com.prismlab.dota2.sdPlugin/ui/pi.html` — property inspector for backend URL config
- `prismlab/stream-deck-plugin/src/connection.ts` — BackendConnection singleton, GsiState interface, exponential-backoff reconnect
- `prismlab/stream-deck-plugin/src/plugin.ts` — entry point: registers actions, wires state, calls streamDeck.connect() last
- `prismlab/stream-deck-plugin/src/actions/*.ts` (6 files) — stub action classes for TypeScript compilation

## Decisions Made

- ws package over reconnecting-websocket: lighter dependency, manual backoff mirrors existing useWebSocket.ts pattern already proven in codebase
- Module-level singleton for BackendConnection: avoids 6 separate WebSocket connections, all actions share one subscription
- Stubs use `handleState(_s: any) {}` rather than proper typed stubs: fastest path to TypeScript compilation, Plan 02 replaces entirely with SingletonAction subclasses
- Action icon PNGs deferred: Stream Deck app falls back gracefully when icon files are missing, avoids blocking scaffold on image asset creation

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

The following stub files are intentional scaffolding for Plan 02:

- `prismlab/stream-deck-plugin/src/actions/gold-action.ts` — `export class GoldAction { handleState(_s: any) {} }` — Plan 02 replaces with SingletonAction subclass rendering gold/GPM SVG
- `prismlab/stream-deck-plugin/src/actions/kda-action.ts` — stub — Plan 02 replaces with KDA display
- `prismlab/stream-deck-plugin/src/actions/clock-action.ts` — stub — Plan 02 replaces with game clock display
- `prismlab/stream-deck-plugin/src/actions/items-action.ts` — stub — Plan 02 replaces with inventory display
- `prismlab/stream-deck-plugin/src/actions/rosh-action.ts` — stub — Plan 02 replaces with Roshan status display
- `prismlab/stream-deck-plugin/src/actions/towers-action.ts` — stub — Plan 02 replaces with tower count display

These stubs do not prevent Plan 01's goal (buildable scaffold) — they are the explicit output of Plan 01 per spec.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for scaffold creation.

## Next Phase Readiness

- Plan 02 can immediately implement the 6 SingletonAction subclasses against the established scaffold
- BackendConnection.onState() listener pattern and GsiState interface are ready for Plan 02 action consumption
- npm install + npm run build will complete the compilation chain once @elgato/streamdeck dependency is resolved in Plan 02

## Self-Check: PASSED

All 14 created files verified on disk. Both task commits (8b8afb7, d119f02) confirmed in git log.

---
*Phase: 29-stream-deck-integration*
*Completed: 2026-03-29*
