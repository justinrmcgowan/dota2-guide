# Project Research Summary

**Project:** Prismlab v2.0 - Live Game Intelligence
**Domain:** Real-time Dota 2 game state integration (GSI, WebSocket, Claude Vision, auto-recommendation)
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

Prismlab v2.0 adds live game intelligence to the existing hybrid recommendation engine. The core mechanism is Dota 2's Game State Integration (GSI) -- a first-party Valve feature where the game client sends HTTP POST requests with structured JSON to a configured URI at configurable intervals. This is VAC-safe, well-documented, and used by every major Dota 2 companion tool (Dotabuff App, Overwolf, Dota Plus). The stack additions are minimal: only 2 new Python packages (pillow, python-multipart) and zero new frontend packages, built entirely on top of the existing FastAPI + React 19 + Zustand + anthropic SDK stack. The recommended build order is: GSI receiver + WebSocket pipeline first (proves the real-time data flow end-to-end), then frontend integration, then auto-refresh logic, then screenshot parsing for enemy items.

The single most important architectural constraint in this research: GSI in player mode (non-spectator) exposes ONLY your own hero data -- gold, items, level, KDA, game clock. Enemy items, enemy heroes, and allied hero data are explicitly blocked by Valve to prevent cheating. This drives the entire v2.0 architecture. Two separate data pipelines must exist: GSI for player data (automated), and Claude Vision screenshot parsing for enemy items (manual trigger). Any architecture that conflates these two sources will produce state management conflicts that cannot be fixed without a full refactor. This constraint must be understood before any code is written.

The differentiator for Prismlab v2.0 over competitors is the combination of automated GSI state feeding into the existing hybrid reasoning engine, plus Claude Vision enemy item parsing from scoreboard screenshots. Dotabuff App provides data-driven suggestions but no natural language reasoning and no enemy item parsing. Dota Plus provides in-client suggestions but no adaptive reasoning engine. Neither competitor explains the reasoning behind their recommendations. Prismlab's unique position -- real-time game data plus AI reasoning that sounds like an 8K+ MMR coach -- is preserved and strengthened in v2.0.

## Key Findings

### Recommended Stack

The existing validated stack (React 19 + Vite 8 + Tailwind v4 + Zustand 5, Python 3.13 + FastAPI + SQLAlchemy + SQLite, Claude Sonnet 4.6, anthropic SDK v0.86) requires minimal additions for v2.0. FastAPI's built-in WebSocket support is already available via uvicorn[standard] which is already installed. The anthropic SDK v0.86 already supports Claude Vision image content blocks with no upgrade needed. Only two new Python packages are required. The research explicitly rejects all third-party GSI libraries (dota2gsipy, dota2gsi -- both abandoned, conflict with FastAPI), react-use-websocket (uncertain React 19 compatibility, unmaintained since 2023), and python-socketio/socket.io-client (unnecessary abstraction). All WebSocket work uses a custom ~60-line useGSI hook with the browser native WebSocket API.

**Core technologies (new additions only):**
- FastAPI POST endpoint (custom): Receives Dota 2 GSI HTTP POST payloads -- no new dependency
- Pydantic GSIPayload models (custom): Validates and types the deeply nested GSI JSON -- no new dependency
- FastAPI WebSocket (built-in): Pushes GSI state to frontend in real-time -- already included via uvicorn[standard]
- Custom useGSI hook: Browser native WebSocket API wrapped in a React hook -- zero new npm packages
- pillow>=12.1.0: Resizes screenshots before Vision API calls, reduces token cost ~40% -- NEW package
- python-multipart>=0.0.20: Required by FastAPI for UploadFile endpoints -- NEW package
- Claude Vision (existing SDK): Extracts enemy item data from scoreboard screenshots -- no upgrade needed

**Total new dependencies: 2 Python packages. Zero frontend packages.**
### Expected Features

**Must have (table stakes -- every GSI tool does these):**
- GSI endpoint receiving and parsing Dota 2 game state -- foundational for all v2.0 features
- Auto-detect own hero from GSI during pre-game -- eliminates first manual step
- Auto-detect own items and auto-mark purchased -- biggest friction reduction in live games
- Auto-track gold and net worth in real-time -- enables gold progress bar toward next item
- Game clock sync and automatic phase progression -- removes manual phase management
- WebSocket push to frontend with reconnection logic -- required for sub-second updates
- GSI connection status indicator -- users must know if the game client is connected
- Manual controls remain as fallbacks and overrides -- progressive enhancement, not replacement

**Should have (Prismlab differentiators):**
- Screenshot parsing for enemy items via Claude Vision -- leverages existing API, no competitor does this
- Auto-determine lane result from gold data at the 10-minute mark with confirmation prompt
- Gold progress bar toward next recommended item with component cost breakdown
- Auto-refresh recommendations on key game events with hard 2-minute rate limit
- Draft auto-detection from GSI draft data during hero selection (partial -- player mode limits visibility)

**Defer (v2.x or v3+):**
- Auto-refresh recommendations in v2.x after validation and threshold tuning
- Multiple simultaneous game tracking (party/coaching mode)
- Voice coaching and TTS callouts
- Hotkey-triggered screenshot capture requiring OS-level hooks
- Clipboard monitoring for auto-capture (VAC risk concern)
- Docker networking optimization for remote Dota clients

### Architecture Approach

The v2.0 architecture extends the existing system with four new backend components (GSIListener, ConnectionManager, VisionEngine, AutoRefreshManager) and three new frontend components (useGSI hook, ScreenshotUpload, GSIStatus) while leaving the existing HybridRecommender, LLMEngine, recommendationStore, and all existing routes completely unchanged. The design principle is progressive enhancement: if GSI is not connected, the app functions exactly as v1.1 with manual inputs. The Zustand gameStore is extended with GSI-sourced fields; every auto-detectable field gets a source property (gsi | manual | screenshot) to prevent conflicts between input modes. This source-tracking requirement is architectural -- it must be built in Phase 1, not retrofitted.

Nginx must be updated with WebSocket proxy headers (proxy_http_version 1.1, Upgrade, Connection, proxy_read_timeout 3600s) and a new /gsi location. No changes to docker-compose.yml are needed since GSI traffic uses the existing backend port (8420). The GSI config file pointing to the Unraid server LAN IP (not localhost) must be generated and downloadable from the setup UI.

**Major components:**
1. GSIListener -- Receives Dota 2 HTTP POST every 0.5s, parses with Pydantic, detects state change events, returns HTTP 200 immediately before any async processing
2. ConnectionManager -- In-memory WebSocket manager, broadcasts compact ~200-byte GSI state to all connected frontends; no Redis needed for single-user deployment
3. VisionEngine -- Accepts base64 screenshot, preprocesses with Pillow (crop + resize), calls Claude Vision API with structured output, returns validated enemy item list; separate from LLMEngine
4. AutoRefreshManager -- Hard 2-minute cooldown between Claude API calls, event-based triggers only (phase_change, death, major_purchase, lane_result_detected)
5. useGSI hook -- Browser native WebSocket with exponential backoff reconnection, dispatches typed messages to gameStore; replaces manual input for all GSI-available fields
6. ScreenshotUpload -- Single paste action (Ctrl+V), immediate preprocessing, calls /api/parse-screenshot, shows parsed results for user confirmation before affecting recommendations

### Critical Pitfalls

1. **GSI cannot see enemy items -- the core data gap** -- Design two separate data flows from the start: GSI for player data (automated), screenshot parsing or manual input for enemy data. Never put enemy item fields in GSI Pydantic models. This is an architectural constraint that must be understood before any code is written in Phase 1.

2. **Docker container cannot receive GSI localhost POSTs** -- The GSI .cfg file URI must point to the Unraid server LAN IP (e.g., http://192.168.X.X:8420/api/gsi), not localhost. Generate the .cfg file dynamically from the setup UI with the detected server IP. Validate end-to-end against actual Docker-on-Unraid deployment in Phase 1.

3. **Claude API call flood from uncontrolled auto-refresh** -- Build a three-layer rate control: (1) hard 2-minute backend cooldown in AutoRefreshManager that cannot be bypassed, (2) significance filter accepting only phase_change/death/major_purchase/lane_result events, (3) per-session API call counter in logs. GSI sends 2 updates/second; a single 30-minute game with naive triggers could cost /usr/bin/bash.50+ in API calls.

4. **WebSocket silent disconnection showing stale data** -- Build heartbeat (backend ping every 10s, frontend shows disconnected after 30s silence) and exponential backoff reconnection into the initial WebSocket implementation. On reconnect, send full current state so the frontend replaces rather than merges stale state. Nginx config update is a prerequisite.

5. **Manual and GSI inputs conflicting in state** -- Add source tracking (gsi | manual | screenshot) to every auto-detectable field in gameStore. Manual override wins and persists; GSI does not overwrite explicit user input. Retrofitting this is expensive -- must be built in Phase 1.

6. **Screenshot parsing cost and reliability** -- Crop screenshots to the scoreboard item grid region (~400x200px) before sending to Vision API for a 25x cost reduction. Always show parsed results to the user for confirmation before applying to recommendations. Include the full valid item list in the prompt to prevent hallucination. Rate-limit to 1 parse per 3 minutes.

## Implications for Roadmap

V2.0 divides into 4 sequential phases driven by data flow dependencies. Everything downstream of GSI depends on the receiver working, so the pipeline must be built in order. The existing recommendation engine is never modified -- all new code is purely additive.
### Phase 1: GSI Receiver and WebSocket Foundation

**Rationale:** All other v2.0 features depend on live data flowing from Dota 2 through the backend to the frontend. The architecture decisions made here (two-data-flow model, source tracking in Zustand, Nginx config) are the hardest to change later. This phase has no new pip dependencies.

**Delivers:** Working real-time data pipeline. Dota 2 game state appears in the frontend in real-time. GSI connection status indicator. Nginx updated for WebSocket proxying. GSI .cfg file generation in setup UI. Zustand gameStore extended with source-tracked fields.

**Addresses:**
- Table stakes: GSI endpoint, WebSocket push, connection status indicator, game clock sync
- Manual controls preserved as fallbacks

**Avoids:**
- Docker GSI networking pitfall (validated against actual Unraid deployment, not local dev)
- WebSocket silent disconnect pitfall (heartbeat and reconnection built in from the start)
- Manual/GSI state conflict pitfall (source tracking added to gameStore before any GSI data flows)
- GSI enemy data pitfall (architecture explicitly separates player data from enemy data channels)

**Research flag:** Standard patterns. GSI POST receiver, FastAPI WebSocket, ConnectionManager are all well-documented with official sources. Low unknown surface area.

### Phase 2: Frontend GSI Integration

**Rationale:** Proves the full end-to-end pipeline visible to the user. No Claude API calls involved -- pure data display. Validates Phase 1 work before building on it.

**Delivers:** Auto-detected hero populates hero selector. Real-time gold display. Own items auto-marked as purchased. Game phase transitions automatically. GSIStatus indicator in header. GoldTracker component with progress toward next recommended item.

**Addresses:**
- Table stakes: auto-detect own hero, auto-detect own items, auto-track gold/net worth, auto-phase progression
- Extends gameStore with GSI fields: gsi_connected, gold, net_worth, game_time, own_items, hero_level, is_alive

**Avoids:**
- Frontend re-render jank: separate GSI display state from recommendation state using Zustand selectors to prevent cross-store re-renders

**Research flag:** Standard patterns. Zustand store extension, custom React hook, TypeScript discriminated union for WebSocket message types are all well-documented.

### Phase 3: Auto-Refresh Pipeline

**Rationale:** The core hands-free value of v2.0. Must be built after Phase 2 proves the data flows correctly end-to-end. The rate limiter must be built FIRST within this phase before any trigger logic.

**Delivers:** AutoRefreshManager with hard 2-minute cooldown. Event detection (phase_change, death, major_purchase, lane_result_detected). Auto-determine lane result from GPM data at 10-minute mark with user confirmation prompt. Countdown timer in UI. Per-session Claude API call counter in logs.

**Addresses:**
- Differentiators: auto-determine lane result, auto-refresh on key events
- P2 features from feature research: lane result auto-detection, auto-refresh

**Avoids:**
- Claude API call flood pitfall (hard rate limiter built before any trigger logic)
- Auto-updating recommendations without user consent (notification pattern, user confirms)

**Research flag:** Needs attention during planning. Lane result GPM thresholds require validation against current patch OpenDota averages. The definition of major purchase (recommended: >2000g item) needs explicit decision before implementation.

### Phase 4: Screenshot Parsing for Enemy Items

**Rationale:** Independent of the GSI pipeline -- uses the existing Claude API SDK via a different endpoint pattern. Scheduled last to allow Phases 1-3 to stabilize. This is the highest-impact differentiator feature and the only automated source of enemy item data.

**Delivers:** VisionEngine class (separate from LLMEngine). POST /api/parse-screenshot endpoint with file upload support. ScreenshotUpload React component with Ctrl+V paste. Image preprocessing (crop + resize to max 1200px wide) to control token costs. Parsed result shown for user confirmation before affecting recommendations. Rate limit: 1 parse per 3 minutes.

**Addresses:**
- Differentiators: screenshot parsing for enemy items (Claude Vision), feeds enemyItemsSpotted into existing recommendation context

**Avoids:**
- Screenshot parsing reliability pitfall (user confirmation before applying, item name validation against DB)
- Screenshot cost explosion pitfall (aggressive cropping reduces cost ~25x, rate limit enforced)

**Research flag:** Needs iteration during execution. Claude Vision accuracy for small item icons (~30x30px on a 1080p scoreboard) is MEDIUM confidence per research. Plan for a prompt-tuning cycle based on real Dota 2 scoreboard screenshots. Target >85% per-item identification accuracy.

### Phase Ordering Rationale

- Phase 1 before Phase 2: Cannot display data that is not being received. The backend pipeline must work before building frontend components that consume it.
- Phase 1 before Phase 3: AutoRefreshManager triggers HybridRecommender after detecting GSI events. GSI events do not exist until Phase 1 is built.
- Phase 2 before Phase 3: Auto-refresh shows users that recommendations changed. The frontend integration must prove the recommendation display pipeline before auto-refresh can deliver visible value.
- Phase 4 is independent: Uses the existing Claude API SDK with a different endpoint. Scheduled last to allow the GSI pipeline to stabilize, but can overlap with Phase 3 if bandwidth allows.
- Existing /api/recommend endpoint and HybridRecommender are never touched -- all new code is additive.

### Research Flags

Phases needing deeper attention during planning or execution:
- **Phase 3 (Auto-Refresh):** Lane result GPM thresholds need validation against current patch OpenDota averages before hardcoding. The exact major purchase gold threshold needs explicit decision. Consider making thresholds configurable in the admin panel for patch resilience.
- **Phase 4 (Screenshot Parsing):** Claude Vision accuracy with 30x30px Dota 2 item icons is an open empirical question. Build with user confirmation gate from day one. Plan for a tuning iteration cycle after initial implementation.

Phases with standard patterns (can skip deeper research):
- **Phase 1 (GSI + WebSocket):** FastAPI WebSocket ConnectionManager pattern is extensively documented. GSI JSON structure is fully documented via Dota2GSI C# reference. The exact Nginx WebSocket config block is provided in ARCHITECTURE.md.
- **Phase 2 (Frontend Integration):** Zustand store extension, TypeScript discriminated union message protocol, and custom React hook patterns are all standard and well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing stack fully validated in v1.1. New additions (pillow, python-multipart) are mature packages. All alternatives explicitly evaluated and rejected with clear rationale. Official sources for all recommendations. |
| Features | HIGH | GSI data availability verified against multiple independent GSI library implementations (C#, Node.js, Python). Player-mode data restriction confirmed by multiple sources. Feature scope is realistic given the data constraints. |
| Architecture | HIGH | Existing codebase fully audited against research. All integration points identified. WebSocket + ConnectionManager pattern from official FastAPI documentation. Code examples provided for all major components in ARCHITECTURE.md. |
| Pitfalls | HIGH | Sourced from official Valve GSI docs, Claude Vision API docs, FastAPI WebSocket docs, and community issue reports. Enemy data restriction confirmed by multiple GSI library maintainers. Docker networking constraint verified against deployment topology. |

**Overall confidence:** HIGH

### Gaps to Address

- **Claude Vision accuracy for small item icons:** Rated MEDIUM confidence. Dota 2 item icons at ~30x30px on a 1080p scoreboard are at the edge of reliable Vision recognition per the official API docs. Validate with 10+ real scoreboard screenshots before Phase 4 is marked complete.

- **Lane result GPM thresholds:** The research provides role-specific GPM benchmarks based on OpenDota/Stratz historical data. These shift with patch changes. Verify thresholds against current patch averages before hardcoding. Consider storing in the DB with the hero data refresh pipeline so they update automatically.

- **GSI draft data availability in player mode:** Draft fields exist in the GSI spec but their availability in player mode is inconsistent across community sources. The draft auto-detection feature (deferred to v2.x) should be prototyped against real match data before being committed to any phase plan.

- **WebSocket through Cloudflare Tunnel or Nginx Proxy Manager:** The Unraid deployment uses an external reverse proxy layer. WebSocket proxying through Cloudflare Tunnel has specific requirements (connection timeout handling, HTTP upgrade passthrough). Validate the full proxy chain in Phase 1 end-to-end testing, not just the Docker-internal Nginx layer.

## Sources

### Primary (HIGH confidence)
- [Anthropic Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) -- Image content block format, base64 encoding, token costs, size limits, known limitations for small icons
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/) -- Built-in WebSocket support, ConnectionManager pattern, dependency injection
- [Dota2GSI C# Library](https://github.com/antonpup/Dota2GSI) -- Most comprehensive GSI data structure reference, confirms player-mode restriction on enemy data
- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/) -- Python 3.13 support confirmed in v12.1.1
- [uvicorn PyPI](https://pypi.org/project/uvicorn/) -- v0.42.0 standard extras include websockets package
- [Claude API Rate Limits](https://platform.claude.com/docs/en/api/rate-limits) -- Token bucket algorithm, per-minute and daily limits
- [Nginx WebSocket Proxying](https://nginx.org/en/docs/http/websocket.html) -- Required proxy headers for WebSocket passthrough
- [FastAPI WebSocket Scaling Techniques](https://hexshift.medium.com/top-ten-advanced-techniques-for-scaling-websocket-applications-with-fastapi-a5af1e5e901f) -- Task cleanup on disconnect, background task leak prevention

### Secondary (MEDIUM confidence)
- [GSI Configuration Guide](https://auo.nu/posts/game-state-integration-intro/) -- Config file format, URI setup, data sections -- corroborated by multiple community sources
- [STRATZ Lane Outcomes](https://stratz.com/knowledge-base) -- GPM thresholds for lane result detection algorithm
- [Dotabuff Adaptive Items](https://www.dotabuff.com/blog/2021-06-23-announcing-the-dotabuff-apps-new-adaptive-items-module) -- Competitor feature analysis, confirms gap in natural language reasoning
- [react-use-websocket GitHub](https://github.com/robtaussig/react-use-websocket) -- Confirmed last activity Sept 2023, React 19 compatibility unverified
- [dota2gsipy Python Library](https://github.com/Daniel-EST/dota2gsipy) -- Confirmed abandoned (last commit Jan 2023, 11 total commits)

### Tertiary (LOW confidence -- needs validation)
- GSI draft data availability in player mode -- referenced in GSI spec but community reports are inconsistent; needs real-match testing before committing to draft auto-detection feature
- Cloudflare Tunnel WebSocket passthrough behavior -- limited documentation on timeout and upgrade header handling for persistent WebSocket connections

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*