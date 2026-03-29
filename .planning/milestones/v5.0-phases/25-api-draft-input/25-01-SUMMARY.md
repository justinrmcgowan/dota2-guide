---
phase: 25-api-draft-input
plan: 01
subsystem: api
tags: [stratz, graphql, opendota, live-match, httpx, fastapi]

requires:
  - phase: none
    provides: "Standalone -- extends existing OpenDota client and config"
provides:
  - "StratzClient with two-step live match lookup (player.matches -> live.match)"
  - "OpenDotaClient.fetch_live_match_for_player fallback method"
  - "GET /api/live-match/{account_id} unified endpoint"
  - "GET /api/settings/defaults returning steam_id from .env"
  - "config.Settings.steam_id field"
affects: [25-02, frontend-draft-auto-population, settings-panel]

tech-stack:
  added: []
  patterns: ["Stratz GraphQL via raw httpx POST (no gql library)", "Two-step API lookup: player ID -> live match", "Dual-source fallback: Stratz primary, OpenDota secondary", "Position enum string-to-int normalization"]

key-files:
  created:
    - prismlab/backend/data/stratz_client.py
    - prismlab/backend/api/routes/live_match.py
  modified:
    - prismlab/backend/data/opendota_client.py
    - prismlab/backend/config.py
    - prismlab/backend/api/routes/settings.py
    - prismlab/backend/main.py

key-decisions:
  - "Raw httpx POST for GraphQL -- no gql/graphql-core dependency needed for 2-3 simple queries"
  - "Stratz position enum (POSITION_1..5) mapped to int 1-5, UNKNOWN/FILTERED -> None"
  - "OpenDota game_state hardcoded to GAME_IN_PROGRESS since /live doesn't provide it"
  - "Error handling wraps each source independently -- Stratz failure never blocks OpenDota attempt"

patterns-established:
  - "Stratz GraphQL client: headers-based auth, JSON POST, nested data extraction"
  - "Dual-source live match: try primary, catch all, try fallback, return None if both fail"
  - "Response normalization: separate _normalize_stratz/_normalize_opendota functions"

requirements-completed: [DRAFT-01, DRAFT-02, DRAFT-03]

duration: 4min
completed: 2026-03-28
---

# Phase 25 Plan 01: API-Driven Draft Input - Backend Summary

**Stratz GraphQL client (primary) and OpenDota fallback for live match draft fetching, unified behind GET /api/live-match/{account_id} endpoint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T16:53:23Z
- **Completed:** 2026-03-28T16:57:09Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created StratzClient with three async methods implementing the two-step live match lookup: fetch_player_last_match_id -> fetch_live_match -> fetch_live_match_for_player
- Extended OpenDotaClient with fetch_live_match_for_player that scans /live endpoint for a specific player's game
- Built GET /api/live-match/{account_id} endpoint with Pydantic response models and Stratz-first, OpenDota-fallback architecture
- Added GET /api/settings/defaults endpoint returning configured steam_id from .env for frontend pre-fill
- Added steam_id field to config.Settings for default Steam ID configuration

## Task Commits

Each task was committed atomically:

1. **Task 1: Stratz GraphQL client and OpenDota live match extension** - `063c7c4` (feat)
2. **Task 2: Live match API endpoint and settings defaults endpoint** - `7671dcf` (feat)

## Files Created/Modified

- `prismlab/backend/data/stratz_client.py` - New Stratz GraphQL client with two-step live match lookup
- `prismlab/backend/data/opendota_client.py` - Extended with fetch_live_match_for_player fallback method
- `prismlab/backend/config.py` - Added steam_id: str | None = None setting
- `prismlab/backend/api/routes/live_match.py` - New GET /live-match/{account_id} endpoint with normalization
- `prismlab/backend/api/routes/settings.py` - Added GET /settings/defaults endpoint
- `prismlab/backend/main.py` - Registered live_match_router

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all endpoints return real data from external APIs or configured settings.

## Self-Check: PASSED

- All 7 files verified present on disk
- Both task commits (063c7c4, 7671dcf) verified in git log
- All 3 verification commands from plan passed (route registration, StratzClient methods, OpenDota extension)
