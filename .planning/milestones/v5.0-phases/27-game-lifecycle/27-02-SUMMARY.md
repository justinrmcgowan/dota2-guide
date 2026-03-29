---
phase: 27-game-lifecycle
plan: 02
subsystem: game-lifecycle
tags: [disconnect-timeout, reconnecting, session-sync, gsi-status, toast]
dependency_graph:
  requires: [match-id-pipeline, store-persistence, new-game-reset]
  provides: [disconnect-timeout, reconnecting-indicator, session-endpoint]
  affects: [gsiStore, useGameIntelligence, GsiStatusIndicator, main.py]
tech_stack:
  added: []
  patterns: [in-memory-session-store, ref-based-timeout, gsi-status-state-machine]
key_files:
  created:
    - prismlab/backend/api/routes/session.py
    - prismlab/backend/tests/test_session.py
  modified:
    - prismlab/frontend/src/stores/gsiStore.ts
    - prismlab/frontend/src/hooks/useGameIntelligence.ts
    - prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx
    - prismlab/backend/main.py
decisions:
  - "gsiStatus 'reconnecting' replaces immediate 'lost' on WS disconnect -- 'lost' is now post-timeout only"
  - "In-memory dict for session store (not SQLite) -- single-user V1 deployment on Unraid"
  - "Frontend session sync wiring deferred -- endpoint ready for future multi-device support"
metrics:
  duration: 5min
  completed: "2026-03-28T18:22:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 27 Plan 02: Disconnect Timeout and Session Sync Summary

10-minute disconnect timeout with "Reconnecting..." amber pulsing indicator, auto-clear on expiry with "Session expired" toast, and backend /api/session POST/GET/DELETE endpoint for future state durability.

## What Was Done

### Task 1: Disconnect timeout, reconnect handling, and GsiStatusIndicator update (870a897)

**gsiStore.ts:**
- Expanded `gsiStatus` union type to include `"reconnecting"` alongside `"connected" | "idle" | "lost"`
- Changed `setWsStatus` to set `"reconnecting"` (not `"lost"`) when WS disconnects while GSI was connected
- `"lost"` is now reserved for post-timeout expiry only

**useGameIntelligence.ts:**
- Added `DISCONNECT_TIMEOUT_MS = 10 * 60 * 1000` constant (matches Dota 2 reconnect window, D-11)
- Added `disconnectTimerRef` for tracking the timeout handle
- Disconnect timeout management block fires BEFORE the `gsiStatus !== "connected"` guard:
  - On `"reconnecting"`: starts 10-minute countdown that auto-clears all match state (gameStore, recommendationStore, refreshStore, gsiStore), resets all refs, and shows "Session expired" toast
  - On `"connected"` with active timer: cancels timeout for seamless resume (D-13)
- Cleanup function clears the timeout on hook unmount

**GsiStatusIndicator.tsx:**
- Added `reconnecting: "bg-amber-400 animate-pulse"` to dotColor map (amber pulsing dot)
- Added `reconnecting: "Reconnecting..."` to statusLabel map
- Added tooltip line `"Waiting for GSI data (auto-clears after 10 min)"` when reconnecting

### Task 2: Backend session sync endpoint (386e5c7)

**session.py (new):**
- `POST /api/session` -- saves session payload (match_id, game_state dict, recommendations dict, saved_at timestamp) to in-memory store
- `GET /api/session` -- returns last saved session or `{"session": null}`
- `DELETE /api/session` -- clears stored session
- `SessionPayload` Pydantic model with `game_state: dict` (required) and `saved_at: float` (required)
- Module-level `_session_data: dict | None` for single-session in-memory storage

**main.py:**
- Registered `session_router` with `/api` prefix alongside other routers

**test_session.py (new, 5 tests):**
- `test_get_session_empty`: GET returns null when nothing stored
- `test_save_and_get_session`: POST then GET round-trip verification
- `test_save_overwrites_previous`: second POST replaces first
- `test_clear_session`: DELETE clears stored session
- `test_save_session_validation`: missing required fields returns 422

## Verification Results

- Frontend: `npx tsc --noEmit` -- zero type errors
- Backend: `python -m pytest tests/test_session.py -x -q` -- 5 passed
- Backend: `python -m pytest tests/ -x -q` -- 264 passed, 2 skipped, 7 warnings (all pre-existing)

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all data paths are fully wired. Frontend session sync (periodic POST, startup GET) is intentionally deferred per the plan -- the endpoint is ready for future wiring when multi-device support is needed.

## Decisions Made

1. **gsiStatus "reconnecting" replaces immediate "lost":** On WS disconnect, gsiStore now enters "reconnecting" instead of "lost". The "lost" state is reserved for the post-timeout expiry path, giving users clear visual feedback that the system is waiting for reconnection.

2. **In-memory session store (not SQLite):** For V1 single-user Unraid deployment, a module-level dict is sufficient. Survives container restarts but not recreations. SQLite persistence can be added later if needed.

3. **Frontend sync wiring deferred:** The backend endpoint is functional and tested, but the frontend does not yet call it. localStorage (Plan 01) remains the primary persistence mechanism. The endpoint is ready for future multi-device/browser-change scenarios.

## Self-Check: PASSED
