---
gsd_state_version: 1.0
milestone: v5.0
milestone_name: Supreme Companion
status: v5.0 milestone complete
stopped_at: Completed 29-02-PLAN.md
last_updated: "2026-03-29T12:14:33.280Z"
progress:
  total_phases: 30
  completed_phases: 30
  total_plans: 73
  completed_plans: 73
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-27)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 29 — stream-deck-integration

## Current Position

Phase: 33
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 45 (v1.0: 14, v1.1: 6, v2.0: 15, v3.0: 10)
- Average duration: ~6 min (v3.0 trend)
- Total execution time: ~11.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1-6 (v1.0) | 14 | ~5.8h | ~25 min |
| 7-9 (v1.1) | 6 | ~2.5h | ~25 min |
| 10-14 (v2.0) | 15 | ~2.5h | ~5 min |
| 15-18 (v3.0) | 10 | ~0.8h | ~5 min |
| Phase 19 P01 | 5min | 2 tasks | 4 files |
| Phase 19 P02 | 6min | 2 tasks | 5 files |
| Phase 19 P03 | 4min | 2 tasks | 2 files |
| Phase 20 P03 | 5min | 1 tasks | 2 files |
| Phase 21 P01 | 6min | 2 tasks | 6 files |
| Phase 21 P02 | 4min | 2 tasks | 6 files |
| Phase 22 P01 | 3 | 3 tasks | 3 files |
| Phase 22 P02 | 5 | 2 tasks | 4 files |
| Phase 23-win-condition-framing P01 | 4 | 2 tasks | 5 files |
| Phase 23-win-condition-framing P02 | 6min | 2 tasks | 4 files |
| Phase 25-api-draft-input P01 | 4min | 2 tasks | 6 files |
| Phase 25-api-draft-input P02 | 5min | 2 tasks | 6 files |
| Phase 26-engine-optimization P01 | 11min | 2 tasks | 10 files |
| Phase 26-engine-optimization P03 | 3min | 1 tasks | 2 files |
| Phase 26-engine-optimization P02 | 3min | 2 tasks | 3 files |
| Phase 27-game-lifecycle P01 | 6min | 2 tasks | 6 files |
| Phase 27-game-lifecycle P02 | 5min | 2 tasks | 6 files |
| Phase 28-patch-data-refresh P01 | 4min | 2 tasks | 3 files |
| Phase 28-patch-data-refresh P02 | 4min | 2 tasks | 3 files |
| Phase 33-game-analytics P01 | 4min | 2 tasks | 3 files |
| Phase 33-game-analytics P02 | 2min | 2 tasks | 3 files |
| Phase 33-game-analytics P03 | 4min | 2 tasks | 5 files |
| Phase 24-audio-prompts P01 | 2min | 2 tasks | 3 files |
| Phase 24-audio-prompts P02 | 3 | 2 tasks | 2 files |
| Phase 29-stream-deck-integration P01 | 5min | 2 tasks | 20 files |
| Phase 29-stream-deck-integration P02 | 5min | 2 tasks | 8 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 16]: Frozen dataclasses for cache immutability; atomic swap refresh; RulesEngine consumes DataCache via constructor injection
- [Phase 18]: Threat annotations: fed if kills>=5 and K/D>=2, behind if deaths>=3 and D/K>=2
- [Roadmap]: Prompt architecture split (DATA-04) established as Phase 19 prerequisite -- all four feature phases depend on system-vs-user message data boundary
- [Roadmap]: Phase ordering mirrors data dependency: abilities + timing first, then counter rules, then timing UI, then build path, then win condition last
- [Phase 19]: One row per hero for timing data (JSON blob) matching one API call = one DB write pattern
- [Phase 19]: Nyquist test scaffolds: tests import types that don't exist yet, fail with ImportError until implementation plan
- [Phase 19]: AbilityCached.bkbpierce is bool not string -- simpler downstream checks
- [Phase 19]: set_hero_timings does NOT clear ResponseCache -- timing data changes slowly
- [Phase 19]: Ability refresh is non-fatal try/except -- heroes/items always commit
- [Phase 19]: v4.0 directives use conditional If guards for optional context sections
- [Phase 19]: System prompt data boundary enforced: directives only, no dynamic data (token budget <5000, no percentages)
- [Phase 20]: Counter-relevant ability properties limited to 4: channeled, passive, BKB-pierce, undispellable
- [Phase 21]: 10pp urgency threshold for timing-critical items (good-zone minus late-zone WR > 10pp)
- [Phase 21]: Post-LLM enrichment pattern: timing data appended after _validate_item_ids, never sent to Claude for generation
- [Phase 21]: Zone classification uses 2% peak threshold for good zone, weighted average for ontrack/late boundary
- [Phase 21]: Proportional zone widths use bucket count ratio, not time span -- consistent with equal-interval bucket emission
- [Phase 21]: timingDataMap built with useMemo in ItemTimeline keyed by item_name for O(1) per-item lookup
- [Phase 22]: Component ordering uses Claude's component_order when valid; heuristic _sort_defensive_first activates on lost lane
- [Phase 22]: Build paths only generated for items with >= 2 components to avoid noise for base items
- [Phase 22]: ComponentStep.reason defaults to empty string; build_path_notes is the primary ordering justification
- [Phase 22]: buildPathMap useMemo mirrors timingDataMap pattern — O(1) per-item lookup keyed by item_name
- [Phase 22]: BuildPathSteps returns null for empty steps arrays — base items with no components show reasoning only
- [Phase 23-win-condition-framing]: win_condition is post-LLM enrichment only -- never in LLM_OUTPUT_SCHEMA, never Claude-generated
- [Phase 23-win-condition-framing]: all_opponents (max 5) separate from lane_opponents (max 2) -- draft classification vs matchup rules
- [Phase 23-win-condition-framing]: MIN_HEROES=3 threshold prevents noisy low-signal context injection into system prompt
- [Phase 23-win-condition-framing]: WinConditionBadge uses triangle glyphs (HTML entities) for allied/enemy directionality -- zero-dependency, no emojis
- [Phase 23-win-condition-framing]: Confidence expressed via opacity-100/75/50 only -- show-dont-tell per DESIGN.md, no text labels
- [Phase 23-win-condition-framing]: all_opponents uses game.opponents (full 5 filtered for nulls); lane_opponents uses game.laneOpponents -- distinct concerns maintained
- [Phase 25-api-draft-input]: Raw httpx POST for Stratz GraphQL -- no gql library needed for simple queries
- [Phase 25-api-draft-input]: Dual-source live match: Stratz primary with OpenDota fallback, independent error handling per source
- [Phase 25-api-draft-input]: useLiveDraft is standalone hook at App.tsx level, not nested inside useGameIntelligence -- independent GSI subscriptions for decoupled concerns
- [Phase 26-engine-optimization]: 3-mode engine routing (fast/auto/deep) with Ollama primary + Claude fallback in Auto mode; budget_ok defaults True when no cost_tracker
- [Phase 26-engine-optimization]: Training data script uses conservative manual hero role map (~100 heroes) with DB-role fallback; ChatML JSONL output; line-level flush for resume safety
- [Phase 26-engine-optimization]: DRY mode injection: api.recommend() wrapper auto-reads localStorage, not each callsite
- [Phase 27-game-lifecycle]: match_id change is primary new-game trigger; hero_selection state is logged but not gated on
- [Phase 27-game-lifecycle]: Custom storage adapter for Set<string> serialization in recommendationStore persist middleware
- [Phase 27-game-lifecycle]: gsiStatus 'reconnecting' replaces immediate 'lost' on WS disconnect; 'lost' reserved for post-timeout expiry
- [Phase 27-game-lifecycle]: In-memory dict session store for V1 single-user; frontend sync wiring deferred
- [Phase 28-patch-data-refresh]: session.merge() for HeroAbilityData upserts -- matches refresh.py pattern, fixes IntegrityError on container restart
- [Phase 28-patch-data-refresh]: Bloodstone hint uses descriptive text without percentage to satisfy DATA-04 no-percentages test
- [Phase 28-patch-data-refresh]: No new rules for 7.41 items -- Claude handles via LLM path until meta settles
- [Phase 33-game-analytics]: follow_rate computed at ingest time for O(1) reads; None when no recommendations (not 0.0)
- [Phase 33-game-analytics]: Batch IN-clause subqueries for match-history to avoid N+1 on items/recommendations
- [Phase 33-game-analytics]: Synchronous getState() snapshot before clear() on match_id change; fire-and-forget POST never blocks new game flow
- [Phase 33-game-analytics]: useState view routing ('advisor' | 'match-history') instead of React Router for simplicity
- [Phase 33-game-analytics]: Client-side hero name text filter + server-side result/mode filters for hybrid UX
- [Phase 24-audio-prompts]: useAudioStore uses standard Zustand persist (no custom storage adapter) — only primitive types (bool, number) so no Set serialization needed
- [Phase 24-audio-prompts]: speak() does not set utterance.voice — avoids getVoices() async race condition on Chrome
- [Phase 24-audio-prompts]: Volume slider hidden when audio disabled — clean SettingsPanel UI with no redundant controls
- [Phase 24-audio-prompts]: useAudioStore.getState() inside subscribe callbacks avoids stale closure issue; prevDataRef plain object inside useEffect closure for double-fire guard
- [Phase 29-stream-deck-integration]: ws package for BackendConnection (not reconnecting-websocket) — lighter, manual exponential backoff mirrors useWebSocket.ts pattern
- [Phase 29-stream-deck-integration]: Module-level BackendConnection singleton shared across all 6 action types — avoids 6 separate WebSocket connections
- [Phase 29-stream-deck-integration]: Stub action files allow TypeScript compilation in Plan 01; Plan 02 replaces with full SingletonAction implementations
- [Phase 29-stream-deck-integration]: TC39 stage-3 decorators: removed experimentalDecorators from tsconfig to match @elgato/streamdeck SDK ClassDecoratorContext signature
- [Phase 29-stream-deck-integration]: SVG data URL pattern for Stream Deck buttons: buildXxxSvg() returns inline SVG string, setImage() uses data:image/svg+xml with encodeURIComponent

### Pending Todos

None yet.

### Blockers/Concerns

- Three-cache coherence must extend to new ability + timing data (carried from Phase 16, addressed in Phase 19)
- WCON-04 requires full enemy team data -- current schema only sends lane_opponents, needs expansion (addressed in Phase 23)

## Session Continuity

Last session: 2026-03-29T11:34:54.556Z
Stopped at: Completed 29-02-PLAN.md
Resume file: None
