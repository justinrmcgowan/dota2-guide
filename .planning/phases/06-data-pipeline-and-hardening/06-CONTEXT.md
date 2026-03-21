# Phase 6: Data Pipeline and Hardening - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 creates an automated daily data refresh pipeline that fetches updated hero/item matchup data from OpenDota/Stratz and writes to SQLite, plus a data freshness indicator in the UI. After this phase, matchup data stays current automatically without manual intervention.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — near-infrastructure phase with minimal user-facing decisions:
- Daily pipeline scheduling mechanism (cron script, FastAPI background task, or APScheduler)
- Data freshness display location and format (small text in header or footer)
- Error handling for failed refreshes
- Refresh script invocation pattern (Docker cron, host cron, or startup-based scheduling)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data/opendota_client.py` — Already has fetch_heroes, fetch_items, fetch_matchups
- `data/seed.py` — Has seed_if_empty logic, pattern for data population
- `data/matchup_service.py` — Has get_or_fetch_matchup with staleness checks (24h threshold)
- `data/models.py` — Hero, Item, MatchupData models with updated_at timestamps
- `data/database.py` — Async SQLAlchemy session management

### Established Patterns
- Async FastAPI with SQLAlchemy
- OpenDota API client with rate limiting
- Docker Compose deployment

### Integration Points
- `docker-compose.yml` — May need cron or scheduler service
- `main.py` — May add admin endpoint for manual refresh trigger
- Frontend Header or footer — Small data freshness text

</code_context>

<specifics>
## Specific Ideas

- The existing matchup_service already checks staleness (>24h) per matchup pair. The pipeline should refresh ALL hero/item data, not just individual matchups on demand
- Consider a POST /admin/refresh-data endpoint (from blueprint) for manual triggers
- scripts/refresh_data.sh from blueprint for cron-friendly invocation
- Data freshness date should show when hero/item data was last fully refreshed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
