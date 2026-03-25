---
phase: 10-gsi-receiver-websocket-pipeline
plan: 02
subsystem: api
tags: [websocket, fastapi, nginx, real-time, broadcast, game-state]

# Dependency graph
requires:
  - phase: 10-01
    provides: "GsiStateManager singleton with to_broadcast_dict() for serialized game state"
provides:
  - "WSManager singleton with connect/disconnect/throttled broadcast at 1Hz"
  - "WebSocket endpoint at /ws for live game state push"
  - "Nginx proxy for /gsi and /ws with WebSocket upgrade headers"
affects: [10-03 (frontend WebSocket client), 11 (frontend GSI store)]

# Tech tracking
tech-stack:
  added: []
  patterns: [websocket-broadcast-loop, hash-based-change-detection, nginx-websocket-proxy]

key-files:
  created:
    - prismlab/backend/gsi/ws_manager.py
    - prismlab/backend/tests/test_ws.py
  modified:
    - prismlab/backend/main.py
    - prismlab/frontend/nginx.conf

key-decisions:
  - "Hash-based change detection: compare hash(json.dumps(state)) to skip duplicate broadcasts"
  - "WebSocket endpoint on app directly (not router) for best FastAPI WebSocket support"
  - "Nginx proxy_read_timeout 86400s (24h) prevents idle WebSocket disconnects"

patterns-established:
  - "1Hz throttled broadcast: asyncio.sleep(1.0) in background task, only push when state hash differs"
  - "Dead connection cleanup: try/except around send_text, collect dead list, remove after iteration"
  - "Nginx WebSocket proxy: proxy_http_version 1.1, Upgrade header, Connection 'upgrade'"

requirements-completed: [WS-01, INFRA-01]

# Metrics
duration: 3min
completed: 2026-03-25
---

# Phase 10 Plan 02: WebSocket Broadcast & Nginx Proxy Summary

**WebSocket ConnectionManager with 1Hz throttled broadcast loop and Nginx /gsi + /ws proxy configuration with 24-hour idle timeout**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T21:32:43Z
- **Completed:** 2026-03-25T21:35:48Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- WSManager with connect/disconnect, 1Hz broadcast loop that only pushes when game state changes (hash comparison)
- Dead WebSocket connection cleanup without blocking other clients
- WebSocket endpoint /ws registered on FastAPI app, broadcast loop started/stopped in lifespan
- Nginx config with /gsi and /ws proxy locations (WebSocket upgrade headers, 86400s read timeout)
- 8 new tests passing (7 unit + 1 integration), 24 existing GSI tests unaffected (32 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: WebSocket ConnectionManager with throttled broadcast** (TDD)
   - `ee8d9ed` (test) - Failing tests for WebSocket manager
   - `3d2600e` (feat) - Implement WebSocket manager with throttled broadcast
2. **Task 2: Nginx proxy configuration for /gsi and /ws** - `97d5191` (feat)

## Files Created/Modified

- `prismlab/backend/gsi/ws_manager.py` - WSManager class with connect/disconnect, 1Hz broadcast loop, hash-based change detection, dead connection cleanup
- `prismlab/backend/main.py` - Added WebSocket endpoint /ws, broadcast loop start/stop in lifespan, imports for ws_manager and gsi_state_manager
- `prismlab/frontend/nginx.conf` - Added /gsi and /ws proxy locations with WebSocket upgrade headers, reordered locations before SPA catch-all
- `prismlab/backend/tests/test_ws.py` - 8 tests: connect, disconnect, broadcast change detection, skip unchanged, skip None, dead cleanup, /ws endpoint integration

## Decisions Made

- **Hash-based change detection**: Using `hash(json.dumps(state_dict))` to compare current state with last sent state. Simple, fast, and avoids unnecessary WebSocket pushes when GSI sends identical data at 2Hz.
- **WebSocket endpoint on app directly**: FastAPI WebSocket endpoints work best when registered directly on the app object rather than on a router, avoiding potential routing issues.
- **24-hour Nginx timeout**: Set `proxy_read_timeout 86400s` and `proxy_send_timeout 86400s` on /ws location to prevent Nginx from closing idle WebSocket connections (default is 60s, which would cause reconnection loops when no game is running).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- WebSocket broadcast layer ready for frontend consumption (Plan 03)
- Frontend can connect to `ws://host/ws` and receive `{"type": "game_state", "data": {...}}` messages
- Nginx routes both /gsi (HTTP POST from Dota 2) and /ws (WebSocket from browser) to backend
- All traffic through single Nginx port 8421 as designed

## Self-Check: PASSED

- All 5 files verified to exist on disk
- All 3 task commits verified in git log (ee8d9ed, 3d2600e, 97d5191)
- test_ws.py has 197 lines (above 50-line minimum)
- 8 test functions in test_ws.py (above 3-function minimum)
- No stubs found in any created/modified files

---
*Phase: 10-gsi-receiver-websocket-pipeline*
*Completed: 2026-03-25*
