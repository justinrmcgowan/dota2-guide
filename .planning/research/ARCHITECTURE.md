# Architecture Research: v2.0 Live Game Intelligence Integration

**Domain:** Real-time game state integration for existing Dota 2 item advisor
**Researched:** 2026-03-23
**Confidence:** HIGH (existing codebase fully audited, GSI protocol well-documented, all integration points verified against current code)

## System Overview

### Current Architecture (v1.1)

```
                     CURRENT STATE
  +------------------------------------------------------+
  |  Frontend (React 19, port 8421)                      |
  |  +------------+  +---------------------+             |
  |  | gameStore   |  | recommendationStore  |            |
  |  +------+-----+  +----------+----------+             |
  |         |                    |                        |
  |  +------+--------------------+----------+             |
  |  |        useRecommendation()           |             |
  |  |    (manual trigger via REST POST)    |             |
  |  +-------------------+-----------------+              |
  +----------------------|-------------------------------|+
  |  Nginx (proxy /api/ and /admin/)                      |
  +----------------------|--------------------------------+
  |  Backend (FastAPI, port 8420)                         |
  |  +-------------------+-------------------+            |
  |  |  POST /api/recommend                  |            |
  |  |  HybridRecommender                    |            |
  |  |   +- RulesEngine (instant)            |            |
  |  |   +- ContextBuilder                   |            |
  |  |   +- LLMEngine (Claude, 10s timeout)  |            |
  |  +---------------------------------------+            |
  |  +-----------+  +------------+                        |
  |  |  SQLite   |  | APScheduler|                        |
  |  |  (heroes, |  | (daily     |                        |
  |  |   items)  |  |  refresh)  |                        |
  |  +-----------+  +------------+                        |
  +-------------------------------------------------------+
```

### Target Architecture (v2.0)

```
  Dota 2 Client                     Frontend (React 19, port 8421)
  +-----------+                +------------------------------------+
  | GSI POST  |                |  +------------+ +--------------+   |
  | (player's |                |  | gameStore   | | recStore     |   |
  |  gaming   |                |  | +gsi fields | | (unchanged)  |   |
  |  PC)      |                |  +------+-----+ +------+-------+   |
  +-----+-----+               |         |              |            |
        | HTTP POST            |  +------+--------------+-------+   |
        | every 0.5s           |  | NEW: useGSI() hook          |   |
        |                      |  |  - WebSocket connection      |   |
        |                      |  |  - Auto-update gameStore     |   |
        |                      |  |  - Trigger auto-refresh      |   |
        |                      |  +------+----------------------+   |
        |                      |         | ws://host/ws/gsi         |
  +-----+----------------------+----+--------------------------+    |
  |  Nginx (proxy /api/, /admin/, /ws/, /gsi/)                 |    |
  +-----+------+---------------+------+------------------------+    |
  |  Backend (FastAPI, port 8420)      |                        |   |
  |  +---+------------------+   +------+------------------+     |   |
  |  | NEW: POST /gsi       |   | NEW: WS /ws/gsi        |     |   |
  |  |  GSIListener         |   |  ConnectionManager      |     |   |
  |  |  - Parse GSI JSON    +-->+  - Push to frontends    |     |   |
  |  |  - Extract fields    |   |  - JSON messages        |     |   |
  |  |  - Detect events     |   +-------------------------+     |   |
  |  +----------------------+                                   |   |
  |  +----------------------+   +-------------------------+     |   |
  |  | NEW: POST /api/      |   | EXISTING: POST /api/    |     |   |
  |  |   parse-screenshot   |   |   recommend             |     |   |
  |  |  - Accept base64 img |   |  (unchanged)            |     |   |
  |  |  - Claude Vision API |   +-------------------------+     |   |
  |  |  - Return enemy items|                                   |   |
  |  +----------------------+                                   |   |
  |  +----------------------+                                   |   |
  |  | NEW: AutoRefreshMgr  |                                   |   |
  |  |  - Track game events |                                   |   |
  |  |  - 2min rate limit   |                                   |   |
  |  |  - Trigger recommend |                                   |   |
  |  +----------------------+                                   |   |
  +-------------------------------------------------------------+   |
  +------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | New vs Modified | Implementation |
|-----------|----------------|-----------------|----------------|
| GSIListener | Receive Dota 2 client POST, parse JSON, extract relevant fields, detect state changes | **NEW** | FastAPI route + service class |
| ConnectionManager | Manage WebSocket connections, broadcast GSI state to all connected frontends | **NEW** | FastAPI WebSocket endpoint + manager class |
| ScreenshotParser | Accept base64 screenshot, call Claude Vision API, extract enemy items from scoreboard | **NEW** | FastAPI route + vision engine class |
| AutoRefreshManager | Track game events from GSI, rate-limit to 1 per 2min, trigger HybridRecommender | **NEW** | Backend service class, asyncio-based |
| useGSI hook | Connect to WebSocket, dispatch GSI updates to gameStore, trigger auto-refresh | **NEW** | React hook |
| ScreenshotUpload | UI for paste/drop scoreboard image, call parse-screenshot endpoint | **NEW** | React component |
| gameStore | Hold game state -- extended with GSI-sourced fields (gold, net worth, game time, own items) | **MODIFIED** | Add fields + setter methods |
| nginx.conf | Proxy WebSocket connections and new routes | **MODIFIED** | Add /ws/ and /gsi/ locations |
| docker-compose.yml | No changes needed -- GSI uses same backend port (8420), different path | **UNCHANGED** | GSI traffic proxied via Nginx |
| HybridRecommender | Unchanged -- already accepts RecommendRequest | **UNCHANGED** | No changes needed |
| LLMEngine | Unchanged for recommendations -- new VisionEngine is separate | **UNCHANGED** | No changes |
| recommendationStore | Unchanged -- still holds recommendation data | **UNCHANGED** | No changes |

## Recommended Project Structure

### New Backend Files

```
prismlab/backend/
+-- api/routes/
|   +-- gsi.py              # NEW: POST /gsi endpoint (receives Dota 2 GSI data)
|   +-- screenshot.py       # NEW: POST /api/parse-screenshot endpoint
|   +-- ws.py               # NEW: WebSocket /ws/gsi endpoint
+-- gsi/
|   +-- __init__.py
|   +-- listener.py         # NEW: GSI payload parser + state extraction
|   +-- models.py           # NEW: Pydantic models for GSI JSON structure
|   +-- events.py           # NEW: Event detection (phase change, item purchase, death)
|   +-- auto_refresh.py     # NEW: Rate-limited auto-refresh manager
+-- engine/
|   +-- vision.py           # NEW: Claude Vision API wrapper for screenshot parsing
+-- ws/
    +-- __init__.py
    +-- manager.py           # NEW: WebSocket ConnectionManager
```

### New Frontend Files

```
prismlab/frontend/src/
+-- hooks/
|   +-- useGSI.ts            # NEW: WebSocket connection + gameStore sync
|   +-- useAutoRefresh.ts    # NEW: Client-side auto-refresh trigger logic
+-- components/game/
|   +-- ScreenshotUpload.tsx # NEW: Paste/drop scoreboard image component
|   +-- GSIStatus.tsx        # NEW: Connection status indicator
|   +-- GoldTracker.tsx      # NEW: Real-time gold/net worth display
+-- stores/
|   +-- gameStore.ts         # MODIFIED: Add GSI fields + auto-populated state
+-- types/
    +-- gsi.ts               # NEW: TypeScript types for GSI WebSocket messages
```

### Structure Rationale

- **gsi/ as a separate module:** GSI parsing is complex enough to warrant its own module. The GSI module handles inbound data (from Dota 2 client), while engine/ handles outbound reasoning (to Claude API). Clean separation.
- **ws/ as a separate module:** WebSocket management is infrastructure, not business logic. Reusable and testable.
- **vision.py inside engine/:** Screenshot parsing uses Claude API like the recommender. Belongs in engine but as a distinct file (vision/multimodal vs text-only).
- **useGSI as a hook, not a store:** WebSocket connection is a side effect, not state. Hook dispatches to existing gameStore. No new Zustand store needed.

## Architectural Patterns

### Pattern 1: GSI Receiver as HTTP POST Endpoint

**What:** Dota 2 client sends HTTP POST to a configured URI with JSON game state. Backend exposes a POST endpoint to receive and parse it. This is plain HTTP POST, NOT WebSocket.

**When to use:** Always -- this is how Dota 2 GSI works. Non-negotiable protocol.

**Critical deployment detail:** Dota 2 runs on the player's Windows gaming PC. FastAPI runs in Docker on Unraid. Different machines, same LAN. GSI cfg must point to Unraid server IP, not localhost. GSI supports any reachable URI.

**GSI config file** (steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/gamestate_integration_prismlab.cfg):
```
"Prismlab GSI"
{
    "uri"           "http://UNRAID_IP:8421/gsi"
    "timeout"       "5.0"
    "buffer"        "0.5"
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
    }
    "auth"
    {
        "token"         "prismlab_gsi_token"
    }
}
```

Buffer and throttle at 0.5s limit traffic to ~2 POSTs/second. Auth token validated server-side.

### Pattern 2: Server-Push via WebSocket

**What:** Backend WebSocket at /ws/gsi. Frontend connects on page load. GSI data arrives via POST, GSIListener processes it, ConnectionManager broadcasts compact state to all WebSocket clients.

**Trade-offs:**
- Pro: True real-time, no polling. Server controls data flow (debounce, filter, diff).
- Pro: FastAPI native WebSocket support (websockets lib already in uvicorn[standard])
- Con: Nginx WebSocket proxy config needed (3 directives). Connection lifecycle management.

**Backend ConnectionManager:**
```python
# ws/manager.py
import asyncio
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast_json(self, data: dict):
        async with self._lock:
            dead = []
            for conn in self.active_connections:
                try:
                    await conn.send_json(data)
                except Exception:
                    dead.append(conn)
            for conn in dead:
                self.active_connections.remove(conn)
```

**Frontend hook:**
```typescript
// hooks/useGSI.ts
function useGSI() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number>();

  useEffect(() => {
    function connect() {
      const protocol = location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${location.host}/ws/gsi`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data) as GSIMessage;
        if (msg.type === "gsi_state") {
          useGameStore.getState().setGSIState(msg.data);
        }
        if (msg.type === "recommendations") {
          useRecommendationStore.getState().setData(msg.data);
        }
      };

      ws.onclose = () => {
        reconnectTimer.current = window.setTimeout(connect, 3000);
      };
    }

    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, []);
}
```

### Pattern 3: Screenshot-to-Structured-Data via Claude Vision

**What:** User pastes Dota 2 scoreboard screenshot. Frontend sends base64 to /api/parse-screenshot. Backend calls Claude Vision API to extract enemy items. Returns structured JSON.

**When to use:** GSI does NOT provide enemy item data. Screenshot is the only source.

**Claude Vision specs (verified from official docs):**
- Formats: JPEG, PNG, GIF, WebP. Max: 5 MB, 8000x8000 px
- Token cost: (width x height) / 750
- Cost per screenshot: ~$0.005-0.01

**Backend:**
```python
# engine/vision.py
import json
from anthropic import AsyncAnthropic

class VisionEngine:
    SCREENSHOT_PROMPT = (
        "This is a Dota 2 scoreboard screenshot. "
        "Extract all visible enemy hero items. "
        "Return JSON with enemies array containing hero_name and items list. "
        "Use Dota 2 internal item names (bkb, blink, manta, heart). "
        "Only include items you can clearly identify. Omit empty slots."
    )

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def parse_scoreboard(self, image_base64: str, media_type: str) -> dict:
        response = await self.client.with_options(
            timeout=15.0, max_retries=0,
        ).messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": image_base64}},
                {"type": "text", "text": self.SCREENSHOT_PROMPT},
            ]}],
        )
        return json.loads(response.content[0].text)
```

### Pattern 4: Rate-Limited Auto-Refresh

**What:** GSI detects significant events. AutoRefreshManager ensures max 1 Claude API call per 2 minutes.

```python
# gsi/auto_refresh.py
import time

class AutoRefreshManager:
    MIN_INTERVAL_SECONDS = 120

    def __init__(self):
        self._last_refresh: float = 0
        self._pending_event: str | None = None

    def should_refresh(self, event_type: str) -> bool:
        TRIGGER_EVENTS = {"phase_change", "death", "major_purchase", "lane_result_detected"}
        if event_type not in TRIGGER_EVENTS:
            return False
        now = time.monotonic()
        if now - self._last_refresh >= self.MIN_INTERVAL_SECONDS:
            self._last_refresh = now
            self._pending_event = None
            return True
        self._pending_event = event_type
        return False
```

Trigger events: phase_change, death, major_purchase (>2000g), lane_result_detected (10min). Pending events fire when cooldown expires.

## Data Flow

### GSI Data Flow

```
Dota 2 Client -> HTTP POST /gsi (every 0.5s)
  -> Nginx proxy -> Backend POST /gsi endpoint
  -> GSIListener.process(): parse, extract, detect events
  -> ConnectionManager.broadcast_json(compact GSIState)
  -> WebSocket -> useGSI hook -> gameStore.setGSIState()
  -> AutoRefreshManager.should_refresh(event)
     -> if YES: HybridRecommender.recommend() -> broadcast recommendations
```

### Screenshot Parse Flow

```
User pastes screenshot -> ScreenshotUpload -> base64 -> POST /api/parse-screenshot
  -> VisionEngine.parse_scoreboard() -> Claude Vision API (~3-5s)
  -> Structured JSON -> gameStore.setEnemyItemsFromScreenshot()
  -> Optionally triggers re-evaluate via AutoRefresh
```

### State Management

GSI auto-populates fields that were manual in v1.1 (gold, items, lane result), but manual input is NEVER disabled. If GSI is not connected, app works exactly like v1.1. Progressive enhancement.

New gameStore fields: gold, net_worth, game_time, game_phase, own_items[], hero_level, is_alive, gsi_connected.

recommendationStore: UNCHANGED. Auto-mark purchased items from GSI own_items.

## Nginx Configuration Changes

```nginx
    # NEW: WebSocket proxy
    location /ws/ {
        proxy_pass http://prismlab-backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # NEW: GSI receiver
    location /gsi {
        proxy_pass http://prismlab-backend:8000/gsi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
```

proxy_http_version 1.1 mandatory for WebSocket. proxy_read_timeout 3600s prevents idle drops.

## GSI Pydantic Models

```python
class GSIAuth(BaseModel):
    token: str

class GSIHero(BaseModel):
    id: int = -1
    name: str = ""
    level: int = 0
    alive: bool = True
    respawn_seconds: int = 0
    health: int = 0
    max_health: int = 0

class GSIPlayerData(BaseModel):
    gold: int = 0
    gold_reliable: int = 0
    gold_unreliable: int = 0
    gpm: int = 0
    net_worth: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0

class GSIItemSlot(BaseModel):
    name: str = "empty"
    charges: int = 0
    cooldown: int = 0

class GSIItems(BaseModel):
    slot0: GSIItemSlot | None = None
    slot1: GSIItemSlot | None = None
    slot2: GSIItemSlot | None = None
    slot3: GSIItemSlot | None = None
    slot4: GSIItemSlot | None = None
    slot5: GSIItemSlot | None = None
    stash0: GSIItemSlot | None = None
    stash1: GSIItemSlot | None = None
    stash2: GSIItemSlot | None = None
    teleport0: GSIItemSlot | None = None
    neutral0: GSIItemSlot | None = None

class GSIMap(BaseModel):
    name: str = ""
    matchid: str = ""
    game_time: int = 0
    clock_time: int = 0
    daytime: bool = True
    game_state: str = ""
    paused: bool = False

class GSIPayload(BaseModel):
    auth: GSIAuth | None = None
    map: GSIMap | None = None
    player: GSIPlayerData | None = None
    hero: GSIHero | None = None
    items: GSIItems | None = None
```

All fields use permissive defaults -- GSI payload varies by game state.

## WebSocket Message Protocol

```typescript
type GSIMessage =
  | { type: "gsi_state"; data: GSIState }
  | { type: "recommendations"; data: RecommendResponse }
  | { type: "event"; event: GameEvent }
  | { type: "error"; message: string };

interface GSIState {
  game_time: number;
  clock_time: number;
  game_phase: "pregame" | "laning" | "midgame" | "lategame";
  gold: number;
  net_worth: number;
  hero_id: number;
  hero_level: number;
  is_alive: boolean;
  respawn_seconds: number;
  own_items: string[];
  kills: number;
  deaths: number;
  assists: number;
  last_hits: number;
  gpm: number;
}

interface GameEvent {
  event_type: "phase_change" | "death" | "major_purchase" | "lane_result";
  details: Record<string, unknown>;
  timestamp: number;
}
```

Discriminated union enables clean dispatch in useGSI hook.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Dota 2 GSI | HTTP POST from game client to /gsi | Player PC to Unraid LAN. Requires .cfg in Dota install. Auth token validated. |
| Claude Vision API | Async HTTP from VisionEngine | Same API key/SDK as recommender. Base64 image blocks. 15s timeout. |
| Claude Text API | Existing LLMEngine (unchanged) | Auto-refresh reuses HybridRecommender.recommend(). Zero changes. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| GSI endpoint to ConnectionManager | In-process call | GSIListener calls manager.broadcast_json() |
| GSI endpoint to AutoRefreshManager | In-process call | GSIListener calls auto_refresh.should_refresh() |
| AutoRefreshManager to HybridRecommender | Async call | Reuses existing recommend() |
| WebSocket to Frontend stores | JSON messages | Dispatched by type field in useGSI |
| ScreenshotUpload to parse-screenshot | REST POST | Same pattern as /api/recommend |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 player (target) | Perfect as-is. Single WebSocket, single GSI. In-memory. No Redis. |
| 2-5 users | Fine. Per-user isolation via auth token keying. |
| 10+ users | Per-user WS channels. Redis pub/sub if multi-worker. |

Not a concern for v2.0. Single-player tool on home server.

## Anti-Patterns

### Anti-Pattern 1: Using dota2gsipy Library
**What:** Import dota2gsipy which runs its own HTTP server.
**Why wrong:** Already have FastAPI. Second server = port conflicts, confusion. Unmaintained.
**Instead:** Parse GSI JSON directly with Pydantic in FastAPI endpoint.

### Anti-Pattern 2: Frontend Polling Instead of WebSocket
**What:** Poll GET /api/gsi-state every 500ms.
**Why wrong:** 2x traffic, 250-500ms latency, CPU waste, stale gaps.
**Instead:** WebSocket push. Subscribe once, instant updates.

### Anti-Pattern 3: Sending Full GSI Payload to Frontend
**What:** Broadcast entire raw GSI JSON (5-15 KB).
**Why wrong:** 10-30 KB/s useless data. Leaks auth token.
**Instead:** Extract needed fields (~200 bytes). Diff-detect before sending.

### Anti-Pattern 4: Auto-Refresh on Every GSI Update
**What:** Trigger Claude API on every field change.
**Why wrong:** ~2/sec at $0.003-0.01 = ~$1-2/min of stale recommendations.
**Instead:** Rate-limit 1 per 2 min on significant events only.

### Anti-Pattern 5: Storing GSI Data in SQLite
**What:** Persist every GSI update to DB.
**Why wrong:** 2 writes/sec = SQLite lock contention. GSI is ephemeral.
**Instead:** In-memory only. No DB writes.

## Build Order (Dependency-Aware)

### Phase 1: GSI Receiver + WebSocket Foundation
**Build:** GSI Pydantic models, POST /gsi, ConnectionManager, WS /ws/gsi, nginx.conf
**Why first:** Everything else depends on live data flowing.
**Dependencies:** None (all new code)
**Validates:** Can Dota 2 POST state and WebSocket client receive it?

### Phase 2: Frontend GSI Integration
**Build:** TS GSI types, useGSI hook, gameStore extensions, GSIStatus, GoldTracker
**Why second:** Proves full pipeline (Dota to Backend to WS to React to UI).
**Dependencies:** Phase 1

### Phase 3: Auto-Refresh Pipeline
**Build:** Event detection, AutoRefreshManager, auto lane result, auto-mark purchased
**Why third:** Core value -- hands-free recommendation updates.
**Dependencies:** Phase 1 + 2

### Phase 4: Screenshot Parsing
**Build:** VisionEngine, POST /api/parse-screenshot, ScreenshotUpload, merge logic
**Why fourth:** Independent feature. Can parallel Phase 3.
**Dependencies:** None strictly (uses existing Claude API)

## Sources

- [Dota2GSI C# reference](https://github.com/antonpup/Dota2GSI) -- GSI payload structure
- [dota2gsipy](https://github.com/Daniel-EST/dota2gsipy) -- GSI field reference (rejected as dependency)
- [FastAPI WebSockets docs](https://fastapi.tiangolo.com/advanced/websockets/) -- ConnectionManager pattern
- [Nginx WebSocket proxying](https://nginx.org/en/docs/http/websocket.html) -- Required proxy headers
- [Claude Vision API docs](https://platform.claude.com/docs/en/build-with-claude/vision) -- Image format, costs, SDK
- [GSI config intro](https://auo.nu/posts/game-state-integration-intro/) -- Config file format
- [Overwolf GSI setup](https://support.overwolf.com/support/solutions/articles/9000212745-how-to-enable-game-state-integration-for-dota-2) -- User enablement
- [FastAPI WS broadcast discussion](https://github.com/fastapi/fastapi/issues/4783) -- Community patterns

---
*Architecture research for: Prismlab v2.0 Live Game Intelligence*
*Researched: 2026-03-23*
