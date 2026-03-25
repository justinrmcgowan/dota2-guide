# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 10 - GSI Receiver & WebSocket Pipeline

## Current Position

Phase: 10 of 13 (GSI Receiver & WebSocket Pipeline)
Plan: 0 of 0 in current phase
Status: Ready to plan
Last activity: 2026-03-24 -- v2.0 roadmap created

Progress: [####################..........] 69% (9/13 phases)

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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.1]: Prompt-only ally coordination (aura dedup, combo awareness via system prompt)
- [v1.1]: Neutral items via system prompt reasoning, not rules engine
- [v2.0]: Two separate data pipelines -- GSI for player data (automated), screenshots for enemy data (manual)
- [v2.0]: Source tracking (gsi | manual | screenshot) on every auto-detectable field in gameStore

### Pending Todos

None yet.

### Blockers/Concerns

- Claude Vision accuracy for small (~30x30px) Dota 2 item icons is MEDIUM confidence -- needs validation in Phase 13
- Lane result GPM thresholds need verification against current patch data before Phase 12
- WebSocket through Cloudflare Tunnel / Nginx Proxy Manager needs end-to-end validation in Phase 10

## Session Continuity

Last session: 2026-03-24
Stopped at: v2.0 roadmap created, ready to plan Phase 10
Resume file: None
