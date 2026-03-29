# Phase 25: API-Driven Draft Input - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Auto-populate allies and opponents from live match API data using the player's Steam ID. Replaces manual hero selection during active games while preserving manual override capability.

</domain>

<decisions>
## Implementation Decisions

### Data Source
- **D-01:** Use Stratz GraphQL as primary data source for live match draft data (real-time, faster). Fall back to OpenDota API if Stratz is unavailable or times out.
- **D-02:** OpenDota client already exists (`opendota_client.py`). Add Stratz GraphQL client as a new module. Both API tokens already configured in `config.py`.

### Trigger & Timing
- **D-03:** Auto-fetch draft on GSI connect (game detection). No user action needed to start.
- **D-04:** During hero pick phase, poll every 10s until draft is complete.
- **D-05:** Provide a manual "Refresh Draft" button for re-fetching if auto-detection is wrong or draft changes (late swaps).

### UI Behavior
- **D-06:** Auto-fill allies and opponents silently — no confirmation dialog, no toast.
- **D-07:** Manual override preserved — existing AllyPicker/OpponentPicker allow clearing and re-selecting heroes. API-fetched heroes are treated the same as manually entered ones.
- **D-08:** If user manually entered heroes before API data arrives, API data overwrites them.

### Steam ID Configuration
- **D-09:** Add Steam ID field to the Settings panel in the frontend. Saves to localStorage.
- **D-10:** Pre-fill from backend .env (`STEAM_ID` or similar) as default value.
- **D-11:** Any user can enter their own Steam ID — supports multi-user deployments.

### Claude's Discretion
- Error handling strategy (retry logic, timeout thresholds)
- Stratz GraphQL query structure
- Polling interval optimization
- Lane assignment inference from API data (if available)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Integration Points
- `prismlab/backend/data/opendota_client.py` — Existing OpenDota API client (add live match methods here)
- `prismlab/backend/config.py` — Already has `opendota_api_key` and `stratz_api_token` settings
- `prismlab/frontend/src/hooks/useGameIntelligence.ts` — GSI → gameStore bridge (add auto-draft here)
- `prismlab/frontend/src/stores/gameStore.ts` — Stores allies/opponents (target for auto-fill)
- `prismlab/frontend/src/components/draft/AllyPicker.tsx` — Manual ally selection (preserved as override)
- `prismlab/frontend/src/components/draft/OpponentPicker.tsx` — Manual opponent selection (preserved as override)
- `prismlab/frontend/src/components/settings/SettingsPanel.tsx` — Add Steam ID field here

### API Documentation
- OpenDota API: `https://docs.opendota.com/` — `/players/{account_id}/recentMatches`, `/live` endpoint
- Stratz API: `https://docs.stratz.com/` — GraphQL live match subscriptions

### User Reference
- Steam ID3: `393530283` (from memory — user's account for testing)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `OpenDotaClient` class with async httpx patterns — extend with live match methods
- `config.py` Settings model — already has both API tokens
- `useGameIntelligence` hook — already bridges GSI to gameStore, natural place for auto-draft trigger
- `gameStore.selectHero()`, `gameStore.setAlly()`, `gameStore.setRole()` — existing state setters

### Established Patterns
- Async httpx for API calls (backend)
- Zustand stores for state management (frontend)
- GSI subscription-based reactivity via `useGsiStore.subscribe()`
- Settings stored in localStorage via Settings panel

### Integration Points
- Backend: New endpoint `/api/live-match/{steam_id}` or extend existing OpenDota client
- Frontend: `useGameIntelligence` detects GSI connect → triggers draft fetch
- Frontend: `SettingsPanel` gets new Steam ID input field
- Frontend: `gameStore` receives auto-populated allies/opponents

</code_context>

<specifics>
## Specific Ideas

- Stratz first for speed, OpenDota as fallback — dual-source resilience
- Auto-fetch should feel instant and invisible — just populate and go
- Manual pickers remain fully functional as override mechanism

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 25-api-draft-input*
*Context gathered: 2026-03-28*
