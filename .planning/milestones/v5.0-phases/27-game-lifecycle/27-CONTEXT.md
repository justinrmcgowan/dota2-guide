# Phase 27: Game Lifecycle Management - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Handle the full game lifecycle: persist session state across refreshes/restarts, detect new games, reset between matches, and gracefully handle disconnects — so stale data never leaks between games.

</domain>

<decisions>
## Implementation Decisions

### State Persistence
- **D-01:** Primary: localStorage for instant save/restore on page refresh and container restart.
- **D-02:** Secondary: periodic sync to backend (SQLite) for durability across browser changes and multi-device scenarios.
- **D-03:** Persisted state includes: hero, role, playstyle, side, lane, allies, opponents, purchased items, dismissed items, lane result, damage profile, enemy items spotted, recommendations data, game clock.
- **D-04:** Settings (Steam ID, recommendation mode, volume, API budget) persisted separately — already in localStorage via Settings panel.

### New Game Detection
- **D-05:** Primary trigger: GSI `map.matchid` change — unique per match, most reliable.
- **D-06:** Secondary confirmation: game state transition to `DOTA_GAMERULES_STATE_HERO_SELECTION` — catches the full end→new flow.
- **D-07:** Both signals required for maximum reliability — belt and suspenders approach.

### Reset Behavior
- **D-08:** On new game detected, clear ALL match state: hero, role, playstyle, allies, opponents, purchased items, dismissed items, lane result, damage profile, enemy items, recommendations, game clock, trigger history.
- **D-09:** KEEP all settings: Steam ID, recommendation mode (Fast/Auto/Deep), volume, API budget cap.
- **D-10:** localStorage match session is overwritten (not appended) — only one active session at a time.

### Abandon / Disconnect Handling
- **D-11:** On GSI disconnect, preserve match state for 10 minutes. Show "Reconnecting..." indicator in header.
- **D-12:** After 10 minutes with no GSI reconnect, auto-clear match state and show "Session expired" toast.
- **D-13:** On GSI reconnect within 10 minutes, resume seamlessly — no state loss, no re-fetch needed.

### Claude's Discretion
- localStorage serialization format (JSON shape, versioning)
- Backend sync endpoint design and frequency
- Match ID tracking implementation in GSI state manager
- Reconnection indicator UI placement and animation
- Edge case: what happens if user opens two browser tabs

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend State
- `prismlab/frontend/src/stores/gameStore.ts` — Hero, role, allies, opponents, lane result, etc.
- `prismlab/frontend/src/stores/recommendationStore.ts` — Recommendations, purchased items, dismissed items
- `prismlab/frontend/src/stores/gsiStore.ts` — GSI live state, connection status
- `prismlab/frontend/src/stores/refreshStore.ts` — Trigger cooldowns, queued events
- `prismlab/frontend/src/hooks/useGameIntelligence.ts` — GSI → store bridge (add new game detection here)

### Backend GSI
- `prismlab/backend/gsi/state_manager.py` — ParsedGsiState, game_state field
- `prismlab/backend/gsi/models.py` — GsiMap.matchid field (already parsed)
- `prismlab/frontend/src/components/layout/GsiStatusIndicator.tsx` — Connection status display (add reconnecting state)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useGsiStore.subscribe()` — already fires on every GSI update, natural place for match ID tracking
- `GsiMap.matchid` — already parsed from GSI payload, just not tracked across updates
- `GsiStatusIndicator` — already shows connected/idle/lost, extend with "reconnecting" state
- Zustand `persist` middleware — built-in localStorage persistence for Zustand stores

### Established Patterns
- Zustand stores with `create()` — add `persist()` middleware for localStorage
- GSI subscription in `useGameIntelligence` — add match ID change detection
- Toast system (`AutoRefreshToast`) — reuse for "Session expired" notification

### Integration Points
- `useGameIntelligence` hook: add match ID tracking, new game detection, disconnect timeout
- `gameStore`: add `clear()` method for full match reset
- `recommendationStore`: already has `clear()` — call it on new game
- `gsiStore`: track `matchId` and `previousMatchId` for change detection
- Backend: new `/api/session` endpoint for sync (or extend existing)

</code_context>

<specifics>
## Specific Ideas

- Zustand `persist` middleware is the cleanest approach for localStorage — zero custom serialization code
- The 10-minute disconnect timeout was chosen based on typical Dota 2 reconnect windows (5 min pause + buffer)
- Match ID is a string in GSI — simple equality check detects new game

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 27-game-lifecycle*
*Context gathered: 2026-03-28*
