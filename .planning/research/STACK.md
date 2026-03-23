# Stack Research: v2.0 Live Game Intelligence

**Domain:** Real-time game data integration (GSI, WebSocket, vision-based screenshot parsing)
**Researched:** 2026-03-23
**Confidence:** HIGH

**Scope:** This document covers ONLY the new stack additions for v2.0. The existing validated stack (React 19 + Vite 8 + Tailwind v4 + Zustand, Python 3.13 + FastAPI + SQLAlchemy + SQLite, Claude Sonnet 4.6, anthropic SDK v0.86) is documented in the v1.0/v1.1 research and is NOT re-researched here.

---

## New Stack Additions

### 1. Dota 2 Game State Integration (GSI) -- Backend Receiver

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI POST endpoint (custom) | N/A | Receive GSI HTTP POST payloads from Dota 2 client | GSI is protocol-level simple: Dota 2 sends JSON via HTTP POST to a configured URI. No third-party library needed -- a single FastAPI endpoint handles it. The existing Python GSI libraries (dota2gsipy, dota2gsi on PyPI) are unmaintained (last commit Jan 2023) and add zero value over raw JSON parsing with Pydantic. Roll our own with Pydantic models for type safety. |
| Pydantic models (custom) | (existing 2.12.x) | Parse and validate GSI JSON payloads | GSI sends deeply nested JSON with known structure (map, player, hero, items, abilities sections). Pydantic v2 models give typed access, validation, and automatic OpenAPI docs. No new dependency. |

**No new backend dependency required for GSI.**

**Architecture note:** Dota 2 GSI is a push model. The game client sends HTTP POST requests at a configurable interval (throttle setting in the .cfg file) to a URI you specify. The backend simply needs an endpoint that accepts POST with JSON body. FastAPI already does this.

**Network topology:** The Dota 2 game runs on the user's Windows desktop. The backend runs in Docker on an Unraid server. The GSI config file URI must point to the Unraid server's LAN IP (e.g., http://192.168.x.x:8420/api/gsi), NOT localhost. The backend port 8420 is already exposed. The GSI endpoint does not need CORS -- GSI is a plain HTTP POST from the game engine, not a browser request, so no Origin header is sent.

**GSI config file** (gamestate_integration_prismlab.cfg, placed in steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/):

```
"Prismlab GSI"
{
    "uri"           "http://UNRAID_IP:8420/api/gsi"
    "timeout"       "5.0"
    "buffer"        "0.1"
    "throttle"      "0.5"
    "heartbeat"     "30.0"
    "data"
    {
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "draft"         "1"
    }
    "auth"
    {
        "token"         "PRISMLAB_SECRET_TOKEN"
    }
}
```

**Key GSI data fields available** (verified via Dota2GSI C# library docs and community implementations):

| Section | Key Fields | Use in Prismlab |
|---------|-----------|-----------------|
| map | game_time, clock_time, game_state (playing/paused/etc), win_team | Track game phase transitions, timing |
| player | gold, gold_reliable, gold_unreliable, gold_per_minute, net_worth, kills, deaths, assists, last_hits, denies | Auto gold tracking, net worth, KDA for lane result detection |
| hero | name, id, level, alive, respawn_seconds, health_percent, mana_percent | Auto-detect hero pick, level-based phase transitions |
| items | slot0-slot8 (inventory + backpack + stash), each with name, charges, cooldown | Auto-detect purchased items (remove from recommendations), track item timings |
| abilities | ability0-ability5 with name, level, can_cast, cooldown | Ability build context for recommendations |

**Limitation:** GSI only exposes YOUR hero/player data when playing a game. Enemy items, enemy heroes, and allied hero data are NOT available via GSI during active play (they are available in spectator mode, but not relevant here). This is why screenshot parsing is needed for enemy builds.

---

### 2. WebSocket Real-Time Updates -- Backend to Frontend Push

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI WebSocket (built-in) | (existing 0.135.x) | Push GSI state updates to frontend in real-time | FastAPI has native WebSocket support via Starlette. No additional framework needed. The websockets Python package is already installed via uvicorn[standard]. Single-process deployment (one Docker container) means no need for Redis pub/sub -- in-memory ConnectionManager is sufficient. |

**No new backend dependency required for WebSocket.**

The uvicorn[standard]==0.42.0 already in requirements.txt includes the websockets package as a transitive dependency. FastAPI's WebSocket class, WebSocketDisconnect exception, and the ConnectionManager pattern are all available without any additional install.

**Frontend WebSocket approach -- custom hook, NOT react-use-websocket:**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Custom useWebSocket hook | N/A | Connect to backend WebSocket, handle reconnection | react-use-websocket v4.0.0 targets React 18 and has not confirmed React 19 compatibility. Last meaningful GitHub activity was Sept 2023. Adding a 77K weekly downloads library with uncertain React 19 support for what is a ~60 line custom hook is unnecessary. The browser native WebSocket API is all we need, wrapped in a custom React hook with reconnection logic. |

**Custom hook requirements:**
- Connect to ws://BACKEND_HOST:8420/ws/gsi
- Exponential backoff reconnection (1s, 2s, 4s, 8s, capped at 10s)
- Parse incoming JSON messages into typed GSI state
- Feed parsed state into Zustand gameStore
- Connection status indicator (connected/disconnected/reconnecting)

This is a perfect fit for the existing Zustand store pattern -- WebSocket messages update the store, React components re-render via selectors.

---

### 3. Screenshot Parsing with Claude Vision -- Enemy Item Detection

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| anthropic SDK (existing) | 0.86.x | Send scoreboard screenshots to Claude for enemy item extraction | The existing anthropic v0.86.x SDK already supports vision via image content blocks. Vision has been supported since the Claude 3 launch (March 2024). No SDK upgrade needed. Use base64-encoded images in the messages API with type "image" content blocks. |
| Pillow | 12.1.x | Resize/optimize screenshots before sending to Claude API | Screenshots can be 1920x1080+ (2+ megapixels). Claude charges tokens based on image size (~width*height/750 tokens). Resizing to ~1200px wide before encoding saves ~40% tokens per image. Pillow 12.1.1 supports Python 3.13. |
| python-multipart | 0.0.20+ | Parse multipart/form-data file uploads in FastAPI | Required by FastAPI for UploadFile parameter in endpoints that accept file uploads. FastAPI will error at runtime without this when defining upload endpoints. |

**New backend dependencies:**

```
pillow>=12.1.0,<13.0
python-multipart>=0.0.20
```

**Vision API usage pattern** (extends existing LLMEngine):

```python
# Content block structure for vision
content = [
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64_encoded_screenshot,
        },
    },
    {
        "type": "text",
        "text": "Extract enemy hero items from this Dota 2 scoreboard...",
    },
]
```

**Supported image formats:** JPEG, PNG, GIF, WebP
**Max image size:** 5 MB per image (API limit)
**Token cost:** ~1,334 tokens for a 1000x1000 px image (~$0.004 at Sonnet pricing)
**Optimal size:** Resize to max 1568px on longest edge before sending (Claude auto-resizes larger images, adding latency with no quality benefit)

**Important:** Vision calls should use a SEPARATE Claude API call from recommendation generation. The screenshot parsing extracts structured data (enemy hero names + their items), which then feeds into the existing recommendation context builder as structured input. Do NOT combine vision + recommendation into a single API call -- it would break prompt caching on the system prompt and increase latency.

---

### 4. Auto Gold Tracking and Lane Result Detection

**No new dependencies.** This is pure application logic built on top of GSI data:

| Feature | Implementation | Stack Component |
|---------|---------------|-----------------|
| Gold tracking | Parse player.gold, player.net_worth, player.gold_per_minute from GSI payloads | Pydantic model + Zustand store |
| Lane result detection | Compare net worth / GPM at 10-min mark against expected thresholds for role | Python logic in backend, threshold-based |
| Auto item detection | Parse items.slot0 through items.slot8 from GSI, match name field against item database | SQLAlchemy query to match GSI item names to DB items |
| Game phase detection | Use map.clock_time thresholds (0-10 min = laning, 10-25 min = midgame, 25+ = late) | Python logic, configurable thresholds |

---

## Supporting Libraries (Already Installed, No Changes Needed)

These existing dependencies directly support v2.0 features without any updates:

| Library | Current Version | v2.0 Usage |
|---------|----------------|------------|
| fastapi | 0.135.1 | GSI POST endpoint, WebSocket endpoint, file upload endpoint |
| uvicorn[standard] | 0.42.0 | Already includes websockets package for WebSocket protocol support |
| anthropic | 0.86.0 | Already supports vision via image content blocks -- no upgrade needed |
| pydantic | 2.12.5 | GSI payload validation models, screenshot parsing response models |
| httpx | 0.28.1 | No new outbound calls needed for v2.0 features |
| zustand | 5.0.12 | Frontend store for real-time GSI state (gold, items, game phase) |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| GSI library | Custom Pydantic models | dota2gsipy (PyPI) | Last commit Jan 2023, only 11 total commits, no releases. Uses its own HTTP server which conflicts with FastAPI. Rolling our own with Pydantic is 100 lines of models and gives us type safety + FastAPI integration for free. |
| GSI library | Custom Pydantic models | dota2gsi (PyPI) | Different package, same problem -- abandoned, tiny, no value over Pydantic. |
| WebSocket (backend) | FastAPI built-in | Socket.IO (python-socketio) | Adds unnecessary abstraction. Socket.IO value is cross-browser fallback (long-polling) which is irrelevant in 2026 -- all target browsers support native WebSocket. Adds ~2 MB of dependencies for zero benefit. |
| WebSocket (frontend) | Custom hook | react-use-websocket | v4.0.0 targets React 18, uncertain React 19 compat, last GitHub activity Sept 2023. A custom hook is ~60 lines and gives us exact control over reconnection behavior and Zustand integration. |
| WebSocket (frontend) | Custom hook | socket.io-client | Same as Socket.IO backend concern -- unnecessary abstraction layer. Also 65KB min bundle size for no benefit over native WebSocket API. |
| Image processing | Pillow | No processing (raw upload) | Screenshots at native resolution (1920x1080+) waste tokens and add latency. Resizing to 1200px wide saves ~40% on token costs per parse. Pillow is 1 dependency, well-maintained, Python standard. |
| Image processing | Pillow | Sharp (Node.js) | Would require a Node.js process or service. Our backend is Python. Pillow is the Python equivalent. |
| Screenshot parsing | Claude Vision API | Tesseract OCR | Tesseract reads text but cannot understand game UI layout, item icons, or spatial relationships in a scoreboard. Claude Vision understands the full visual context and can extract structured data directly. |
| Screenshot parsing | Claude Vision API | Custom CV model | Training a custom model to recognize Dota 2 item icons requires labeled training data, maintenance on every UI update, and ML infrastructure. Claude Vision handles this zero-shot with a good prompt. |
| Real-time protocol | WebSocket | Server-Sent Events (SSE) | SSE is unidirectional (server to client only). We need bidirectional: client sends screenshot data, server pushes GSI updates. WebSocket handles both. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| dota2gsipy or dota2gsi Python packages | Abandoned, tiny, conflict with FastAPI server model | Custom Pydantic models + FastAPI endpoint |
| react-use-websocket | Uncertain React 19 compatibility, unmaintained since 2023 | Custom useWebSocket hook (~60 lines) |
| python-socketio / socket.io-client | Unnecessary abstraction, adds bundle size, all browsers support native WebSocket | FastAPI built-in WebSocket + browser native WebSocket API |
| Tesseract / pytesseract | Cannot understand game UI context, only reads text | Claude Vision API (already have SDK) |
| Redis for WebSocket pub/sub | Single-process deployment, one Docker container, one Uvicorn worker. In-memory ConnectionManager is sufficient. | In-memory ConnectionManager class |
| @tanstack/react-query for WebSocket state | React Query is for request-response HTTP patterns. WebSocket is a persistent connection pushing state. | Zustand store updated directly by WebSocket hook |
| OpenCV (cv2) | Heavy dependency (100+ MB), overkill for screenshot preprocessing. Only need resize + base64 encode. | Pillow (lightweight, does exactly what we need) |

---

## Installation

### Backend (new dependencies only)

```bash
pip install pillow python-multipart
```

**Updated requirements.txt additions:**

```
pillow>=12.1.0,<13.0
python-multipart>=0.0.20
```

### Frontend (no new dependencies)

No new npm packages needed. WebSocket uses the browser native API wrapped in a custom hook. GSI state flows into the existing Zustand store.

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|----------------|-------|
| pillow>=12.1.0 | Python 3.13 | Confirmed: Pillow 12.1.1 supports Python 3.10-3.14. |
| python-multipart>=0.0.20 | FastAPI 0.135.x | Required by FastAPI for UploadFile endpoints. May already be transitively installed. |
| anthropic==0.86.0 | Claude Vision (image content blocks) | Vision support has been in the SDK since v0.18.0 (March 2024). No upgrade needed. |
| uvicorn[standard]==0.42.0 | WebSocket protocol | Already includes websockets package. No additional install. |
| FastAPI WebSocket | Nginx reverse proxy | Nginx config needs proxy_set_header Upgrade and proxy_set_header Connection "upgrade" for WebSocket passthrough. Update nginx.conf in frontend container. |

---

## Docker / Deployment Considerations

### GSI Network Path

```
Dota 2 (Windows PC) --HTTP POST--> Unraid LAN IP:8420 --Docker port map--> Backend container:8000
```

The GSI config must use the Unraid server's LAN IP, not localhost (the game runs on a different machine). Port 8420 is already mapped in docker-compose.yml.

### WebSocket Through Nginx

The current nginx.conf proxies /api/* to the backend. WebSocket connections need additional headers:

```nginx
location /ws/ {
    proxy_pass http://prismlab-backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

proxy_read_timeout 86400 (24 hours) prevents Nginx from closing idle WebSocket connections. The heartbeat mechanism in the WebSocket handler will keep the connection alive.

### File Upload Size

Nginx default client_max_body_size is 1 MB. Scoreboard screenshots can be 1-3 MB. Add to nginx.conf:

```nginx
client_max_body_size 10m;
```

---

## Stack Patterns by Feature

**If implementing GSI first (recommended):**
- Add Pydantic GSI models + FastAPI POST endpoint
- Add WebSocket endpoint + ConnectionManager
- Add custom useWebSocket hook on frontend
- Add Zustand store slices for real-time game state
- No new pip dependencies at this stage

**If implementing screenshot parsing first:**
- Add pillow + python-multipart to requirements.txt
- Add file upload endpoint
- Add vision parsing module (extends LLMEngine)
- Add frontend paste/upload UI component

**If implementing both together:**
- Add both dependency sets in one requirements.txt update
- Build the GSI -> WebSocket -> Frontend pipeline first (pure data flow, testable)
- Add screenshot parsing second (requires Claude API calls, higher cost to test)

---

## Sources

- [Anthropic Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) -- Image content block format, base64 encoding, token costs, size limits (HIGH confidence, official docs)
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/) -- Built-in WebSocket support, ConnectionManager pattern, dependency injection (HIGH confidence, official docs)
- [Dota2GSI C# Library](https://github.com/antonpup/Dota2GSI) -- GSI data structure reference (hero, player, items, map fields) (HIGH confidence, most complete GSI reference)
- [dota2gsipy Python Library](https://github.com/Daniel-EST/dota2gsipy) -- Confirmed unmaintained (last commit Jan 2023, 11 total commits) (HIGH confidence, verified on GitHub)
- [Pillow Documentation](https://pillow.readthedocs.io/en/stable/) -- Image resize, Python 3.13 support confirmed in v12.1.1 (HIGH confidence, official docs)
- [uvicorn PyPI](https://pypi.org/project/uvicorn/) -- v0.42.0, standard extras include websockets package (HIGH confidence, official PyPI)
- [GSI Configuration Guide](https://auo.nu/posts/game-state-integration-intro/) -- Config file format, URI setup, data sections (MEDIUM confidence, community guide corroborated by multiple sources)
- [react-use-websocket GitHub](https://github.com/robtaussig/react-use-websocket) -- v4.0.0, targets React 18, last activity Sept 2023 (HIGH confidence, verified on GitHub)

---

## Summary of Changes from v1.1 Stack

| What | Change | Impact |
|------|--------|--------|
| Backend dependencies | Add pillow>=12.1.0, python-multipart>=0.0.20 | 2 new pip packages |
| Frontend dependencies | None | Zero new npm packages |
| Backend code | Add GSI endpoint, WebSocket endpoint, vision parsing module, ConnectionManager | New route files + engine extension |
| Frontend code | Add custom useWebSocket hook, GSI state display components | New hook + components, extends existing Zustand store |
| Nginx config | Add WebSocket proxy headers, increase client_max_body_size | Config file update |
| Docker | No changes to docker-compose.yml | Existing port mapping (8420) serves GSI + WebSocket + API |
| GSI config | New file on game client machine | User places .cfg file in Dota 2 directory |

**Total new dependencies: 2 Python packages (pillow, python-multipart). Zero frontend packages.**
