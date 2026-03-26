---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Live Game Intelligence
status: Ready to execute
stopped_at: Completed 14-01-PLAN.md
last_updated: "2026-03-26T21:16:11.528Z"
progress:
  total_phases: 5
  completed_phases: 4
  total_plans: 15
  completed_plans: 14
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 14 — recommendation-quality-system-hardening

## Current Position

Phase: 14 (recommendation-quality-system-hardening) — EXECUTING
Plan: 3 of 3

## Performance Metrics

**Velocity:**

- Total plans completed: 20 (v1.0: 14, v1.1: 6)
- Average duration: ~25 min
- Total execution time: ~8.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1-6 (v1.0) | 14 | ~5.8h | ~25 min |
| 7-9 (v1.1) | 6 | ~2.5h | ~25 min |

**Recent Trend:**

- v1.1 phases: consistent ~25 min/plan
- Trend: Stable

*Updated after each plan completion*
| Phase 10 P02 | 3min | 2 tasks | 4 files |
| Phase 10 P03 | 15min | 4 tasks | 10 files |
| Phase 11 P01 | 3min | 2 tasks | 6 files |
| Phase 11 P03 | 4min | 2 tasks | 5 files |
| Phase 11 P02 | 5min | 2 tasks | 6 files |
| Phase 12 P02 | 3min | 2 tasks | 4 files |
| Phase 12 P01 | 5min | 2 tasks | 8 files |
| Phase 12 P03 | 5min | 2 tasks | 6 files |
| Phase 13 P02 | 2min | 2 tasks | 5 files |
| Phase 13 P01 | 3min | 2 tasks | 7 files |
| Phase 13 P03 | 5min | 3 tasks | 5 files |
| Phase 14 P02 | 6min | 2 tasks | 5 files |
| Phase 14 P01 | 11min | 2 tasks | 14 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.1]: Prompt-only ally coordination (aura dedup, combo awareness via system prompt)
- [v1.1]: Neutral items via system prompt reasoning, not rules engine
- [v2.0]: Two separate data pipelines -- GSI for player data (automated), screenshots for enemy data (manual)
- [v2.0]: Source tracking (gsi | manual | screenshot) on every auto-detectable field in gameStore
- [Phase 10]: Hash-based change detection for WebSocket broadcast (hash of JSON string, skip if unchanged)
- [Phase 10]: Nginx 24h proxy_read_timeout on /ws to prevent idle WebSocket disconnects
- [Phase 10]: WebSocket URL derived from window.location at runtime for http/https transparency
- [Phase 10]: Separate wsStatus/gsiStatus in gsiStore for precise three-state indicator control
- [Phase 11]: Used displayRef pattern alongside useState to avoid stale closure in rAF animation hook
- [Phase 11]: GameClock uses span for inline flow in header flex layout
- [Phase 11]: Subscribe to gsiStore outside render cycle via useGsiStore.subscribe() to avoid cascading re-renders
- [Phase 11]: Add-only item marking: GSI marks purchased but never unmarks to prevent flicker
- [Phase 12]: TriggerEvent defined locally in refreshStore for parallel wave execution -- Plan 03 reconciles
- [Phase 12]: Tower counting filters by 'tower' substring in building key names, excluding rax and fort entries
- [Phase 12]: Phase transition thresholds checked highest-first (2100>1200>600) for multi-threshold jump handling
- [Phase 12]: Replicate recommend() logic in useAutoRefresh via direct store access -- hooks can only be called in components
- [Phase 12]: Lane auto-detection via single boolean flag in refreshStore; fires once, no override tracking needed
- [Phase 12]: GSI reconnect syncs prev state to current on status transition to avoid false diff triggers
- [Phase 13]: initialState object extracted for DRY reset/closeModal in screenshotStore
- [Phase 13]: 6-item cap enforced in screenshotStore addItem to match Dota 2 inventory limit
- [Phase 13]: Base64 JSON body for screenshot upload -- no new dependencies, consistent with Anthropic API
- [Phase 13]: Temperature 0.1 for Vision extraction (vs 0.3 for recommendations) for deterministic structured output
- [Phase 13]: SequenceMatcher 0.7 threshold for fuzzy name matching; confidence = Vision certainty x match ratio
- [Phase 13]: parseAttempted ref prevents double-parse on modal open state transitions
- [Phase 13]: Items list for ItemEditPicker fetched lazily from /api/items; failure silently ignored
- [Phase 14]: Removed HERO_NAMES dict entirely in favor of DB-backed lookup helpers (_hero_id, _item_id, _hero_ids)
- [Phase 14]: Merged BKB timing rule into existing _bkb_rule by expanding hero set -- 6 new rules (not 7)
- [Phase 14]: FallbackReason str Enum for JSON-serializable error categories in LLM generate() tuple return
- [Phase 14]: ResponseCache uses SHA-256 of model_dump_json for deterministic request deduplication

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 14 added: Recommendation Quality & System Hardening

### Blockers/Concerns

- Claude Vision accuracy for small (~30x30px) Dota 2 item icons is MEDIUM confidence -- needs validation in Phase 13
- Lane result GPM thresholds need verification against current patch data before Phase 12
- WebSocket through Cloudflare Tunnel / Nginx Proxy Manager needs end-to-end validation in Phase 10

## Session Continuity

Last session: 2026-03-26T21:16:11.525Z
Stopped at: Completed 14-01-PLAN.md
Resume file: None
