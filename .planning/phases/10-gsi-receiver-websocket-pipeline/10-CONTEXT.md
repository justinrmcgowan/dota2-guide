# Phase 10: GSI Receiver & WebSocket Pipeline - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 delivers the real-time data pipeline: a GSI receiver endpoint that accepts Dota 2 game state HTTP POSTs, an in-memory state manager that parses and holds the latest game state, a WebSocket endpoint that pushes throttled updates to the frontend, Nginx configuration for routing GSI/WebSocket traffic, a settings UI for GSI config file generation, and a connection status indicator in the header. After this phase, live game data flows from Dota 2 through the backend to the frontend in real-time, with infrastructure ready for all downstream features (Phases 11-13).

</domain>

<decisions>
## Implementation Decisions

### GSI Config Setup
- **D-01:** Settings page accessible via gear icon in the header bar (top-right, next to data freshness indicator)
- **D-02:** Gear icon opens a slide-over panel from the right side, overlaying main content with dimmed backdrop
- **D-03:** Settings panel contains IP input field (pre-filled if possible), port display, and a "Download .cfg file" button
- **D-04:** Step-by-step instructions below the download button showing exact file placement path
- **D-05:** Generated .cfg file named `gamestate_integration_prismlab.cfg` with user's IP and port 8421

### Connection Status Indicator
- **D-06:** Colored dot + "GSI" label in the header bar, between the logo and data freshness indicator
- **D-07:** Three states: green (Connected — receiving live data), gray (Idle — no game or not configured), red (Lost — was connected, dropped)
- **D-08:** Tooltip on hover shows details: connection status label, last update timestamp, game time if in-game, WebSocket connection state

### GSI & WebSocket Routing
- **D-09:** All traffic routes through Nginx on port 8421 — single entry point for frontend, API, GSI, and WebSocket
- **D-10:** Nginx `/gsi` location block proxies to backend `/gsi` endpoint
- **D-11:** Nginx `/ws` location block proxies to backend `/ws` endpoint with WebSocket upgrade headers (`proxy_http_version 1.1`, `Upgrade`, `Connection "upgrade"`)
- **D-12:** GSI config file points to `http://<user-ip>:8421/gsi` — same port as everything else

### Data Scope & Storage
- **D-13:** Parse all v2.0 fields upfront in Phase 10: hero_name, gold, GPM, net_worth, items (inventory + backpack), game_clock, kills, deaths, assists, team_side, map.game_state
- **D-14:** In-memory only — no DB persistence for GSI data. Ephemeral state in a Python dataclass/manager singleton
- **D-15:** Backend throttles WebSocket pushes to 1 per second (GSI sends at ~2Hz, we aggregate and push at 1Hz)
- **D-16:** Only push when parsed fields have actually changed within the throttle window

### Claude's Discretion
- Exact GSI JSON field paths for parsing (provider, map, player, hero, items sections)
- WebSocket message format (JSON structure for frontend consumption)
- GSI auth token handling (Dota 2 GSI supports auth tokens in config)
- Slide-over panel animation and dismiss behavior
- Throttle implementation approach (asyncio task, timer, etc.)
- WebSocket auto-reconnect strategy on frontend side

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/REQUIREMENTS.md` — GSI-01, WS-01, INFRA-01, INFRA-02 requirement definitions
- `.planning/ROADMAP.md` — Phase 10 success criteria (5 criteria that must be TRUE)
- `PRISMLAB_BLUEPRINT.md` — Original project spec with data models and API patterns

### Existing Infrastructure
- `prismlab/frontend/nginx.conf` — Current Nginx config that needs /gsi and /ws location blocks added
- `prismlab/docker-compose.yml` — Container networking (prismlab-net bridge)
- `prismlab/backend/main.py` — FastAPI app with lifespan pattern (startup/shutdown hooks)
- `prismlab/backend/config.py` — Settings via pydantic-settings (may need GSI-related config)

### Existing State Management
- `prismlab/frontend/src/stores/gameStore.ts` — Current manual game state (hero, role, lane, etc.) — GSI state needs to coexist with manual inputs
- `prismlab/frontend/src/stores/recommendationStore.ts` — Recommendation state with purchased item tracking
- `prismlab/frontend/src/components/layout/Header.tsx` — Header component where GSI status indicator and gear icon will be added

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Header.tsx` — Already has data freshness indicator; add GSI status dot and gear icon alongside it
- `main.py` lifespan pattern — Use same pattern for WebSocket manager startup/shutdown
- `config.py` Settings class — Extend with GSI-related settings if needed
- Zustand store pattern — Follow `gameStore.ts` pattern for a new `gsiStore.ts` or extend existing store

### Established Patterns
- FastAPI async endpoints with Pydantic validation
- Zustand flat stores with typed actions
- Nginx reverse proxy with proxy_pass to backend container
- Tailwind v4 CSS-first theming with OKLCH colors
- Docker Compose bridge networking between containers

### Integration Points
- `nginx.conf` — Add /gsi and /ws location blocks
- `main.py` — Register GSI route and WebSocket endpoint, add GSI manager to lifespan
- `Header.tsx` — Add GSI status indicator and settings gear icon
- `App.tsx` — May need to add settings slide-over panel component
- `docker-compose.yml` — No changes expected (GSI comes through Nginx on existing port)

</code_context>

<specifics>
## Specific Ideas

- The settings panel is a one-time setup experience — user enters IP, downloads .cfg, places it in Dota 2's cfg folder, restarts Dota 2
- GSI status indicator should feel like the data freshness indicator already in the header — small, informational, not attention-grabbing when idle
- The tooltip on the GSI indicator provides debugging info without cluttering the header
- Source tracking fields in gameStore (gsi | manual | screenshot) are for Phase 11 — Phase 10 just establishes the pipeline

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-gsi-receiver-websocket-pipeline*
*Context gathered: 2026-03-25*
