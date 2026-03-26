# Phase 12: Auto-Refresh & Lane Detection - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 delivers automatic recommendation refreshing and lane result detection. Recommendations update hands-free when significant game events occur (death, gold swing, tower/Roshan kills, game phase transitions), rate-limited to max one auto-refresh per 2 minutes. Lane outcome is auto-determined from GPM vs role benchmarks at 10 minutes. A notification toast explains each auto-refresh trigger. After this phase, the player gets updated recommendations without pressing Re-Evaluate.

</domain>

<decisions>
## Implementation Decisions

### Auto-refresh Triggers
- **D-01:** Five trigger types: player death, major gold swing (>2000g net worth delta), tower kill (any team), Roshan kill, and game phase transitions (10 min, 20 min, 35 min).
- **D-02:** Item purchases do NOT trigger auto-refresh — buying an item doesn't change what you should buy next (the recommendation already knew what was coming).
- **D-03:** Tower kills detected for either team (enemy or allied) — both have itemization implications (defensive urgency vs aggressive opportunity).
- **D-04:** Gold swing threshold fixed at 2000g (not configurable). Computed as |current_net_worth - net_worth_at_last_refresh|. Baseline resets after each refresh.
- **D-05:** Game phase transition thresholds: 10:00 (laning ends, lane result determined), 20:00 (mid-game shift), 35:00 (late-game priorities). Each fires once per game.
- **D-06:** Event detection runs on each GSI update (1Hz from WebSocket). Compares current state to previous state to detect diffs (deaths++, new tower count, net_worth delta, clock crossing thresholds).

### Rate Limiting & Cooldown
- **D-07:** Max one auto-refresh per 2 minutes (120 seconds). Cooldown starts when a refresh fires (auto or manual).
- **D-08:** Events during cooldown: queue the most recent trigger only. When cooldown expires, auto-fire with that event's context. Multiple events during cooldown → last one replaces previous (most recent context is most relevant).
- **D-09:** Manual Re-Evaluate button always bypasses cooldown and fires immediately. Manual click also resets the 2-minute cooldown timer (prevents auto-refresh immediately after manual).
- **D-10:** Subtle cooldown timer displayed below the Re-Evaluate button: dim text showing "auto in 1:23" countdown. Only visible when auto-refresh is cooling down and an event is queued.

### Lane Result Auto-Detection
- **D-11:** Role-based static GPM benchmarks at 10:00 game time. Pos 1: ~500, Pos 2: ~480, Pos 3: ~400, Pos 4: ~280, Pos 5: ~230. Won = GPM > benchmark × 1.10, Even = within ±10%, Lost = GPM < benchmark × 0.90.
- **D-12:** At 10:00 game clock, lane result auto-sets in `gameStore.laneResult` based on current GPM vs role benchmark. The LaneResultSelector visually updates with a subtle "auto-detected" indicator.
- **D-13:** User can click any lane result button to override the auto-detected value at any time. Override persists (GSI does not re-detect after override).
- **D-14:** Lane result auto-detection triggers a re-evaluation as part of the 10:00 game phase transition event.

### Notification Toasts
- **D-15:** Bottom-right toast with lightning bolt icon, "Recommendations updated" header, and trigger reason text. Auto-dismiss after 4 seconds.
- **D-16:** Trigger-specific messages: "Death — reassessing priorities", "Gold swing: +2,340g", "Tower destroyed — map changed", "Roshan killed — updating", "Lane phase ended (10:00)", "Mid-game reached (20:00)", "Late game reached (35:00)".
- **D-17:** When cooldown-queued event fires, toast shows only the final trigger reason (not accumulated events). Matches queue-latest-only behavior.

### Claude's Discretion
- Toast component implementation (custom or library like react-hot-toast)
- Exact animation/transition for toast appearance and dismissal
- GSI state diff detection implementation (how to compare previous vs current state)
- Tower/Roshan detection from GSI map data fields
- Cooldown timer implementation (setInterval, requestAnimationFrame, etc.)
- Edge cases: GSI disconnects during cooldown, game ends during cooldown, reconnect after pause

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — GSI-05, REFRESH-01, REFRESH-02, REFRESH-03 requirement definitions
- `.planning/ROADMAP.md` — Phase 12 success criteria (4 criteria that must be TRUE)

### Upstream Phase Context
- `.planning/phases/10-gsi-receiver-websocket-pipeline/10-CONTEXT.md` — WebSocket 1Hz throttle (D-15/D-16), GSI data fields (D-13), in-memory state (D-14)
- `.planning/phases/11-live-game-dashboard/11-CONTEXT.md` — GSI-as-source-of-truth pattern (D-03/D-04), stats bar with gold/GPM/KDA (D-06), game clock in header (D-15)

### Existing Code
- `prismlab/frontend/src/hooks/useRecommendation.ts` — Current recommendation trigger (manual only via `recommend()`). Phase 12 adds auto-trigger calling same function.
- `prismlab/frontend/src/components/game/ReEvaluateButton.tsx` — Manual re-evaluate button. Phase 12 adds cooldown timer text below it.
- `prismlab/frontend/src/components/game/LaneResultSelector.tsx` — Manual won/even/lost toggle. Phase 12 adds auto-detection at 10 min.
- `prismlab/frontend/src/components/game/GameStatePanel.tsx` — Contains LaneResultSelector and ReEvaluateButton. Integration point for cooldown UI.
- `prismlab/frontend/src/stores/gsiStore.ts` — GsiLiveState with gold, gpm, net_worth, kills, deaths, game_clock. Source data for trigger detection.
- `prismlab/frontend/src/stores/gameStore.ts` — `laneResult` field and `setLaneResult` action. Phase 12 auto-calls this at 10 min.

### Backend
- `prismlab/backend/engine/recommender.py` — Recommendation engine called by `/api/recommend`. No backend changes needed — auto-refresh is frontend-driven.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useRecommendation.ts` — Already has `recommend()` function that reads gameStore, builds request, calls API, and updates recommendationStore. Auto-refresh calls this same function.
- `ReEvaluateButton.tsx` — Simple button component. Phase 12 adds cooldown timer text and wraps the auto-refresh logic around it.
- `LaneResultSelector.tsx` — 3-button radio group for won/even/lost. Phase 12 adds programmatic selection at 10:00.
- `gsiStore.ts` — All trigger-relevant fields already available: deaths, gold, gpm, net_worth, game_clock, game_state.

### Established Patterns
- Zustand stores with direct `getState()` access for non-reactive reads
- Functional components with hooks
- Tailwind v4 dark theme styling

### Integration Points
- New `useAutoRefresh` hook (or similar) subscribes to gsiStore changes, detects events, manages cooldown, calls `recommend()`
- `GameStatePanel.tsx` — Wraps LaneResultSelector with auto-detection logic
- `ReEvaluateButton.tsx` — Receives cooldown state as props or reads from a refresh store
- Toast component renders at app root level (bottom-right positioned)

</code_context>

<specifics>
## Specific Ideas

- User explicitly excluded item purchase as a trigger — buying items doesn't change what to buy next
- User wants explicit tower/Roshan detection rather than relying solely on gold swing to catch them
- Toast messages should be Dota-contextual ("Death — reassessing priorities" not generic "Data updated")

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-auto-refresh-lane-detection*
*Context gathered: 2026-03-26*
