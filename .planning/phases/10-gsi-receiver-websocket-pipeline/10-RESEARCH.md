# Phase 10: GSI Receiver & WebSocket Pipeline - Research

**Researched:** 2026-03-25
**Domain:** Dota 2 Game State Integration, FastAPI WebSocket, Nginx proxying, React real-time state
**Confidence:** HIGH

## Summary

Phase 10 establishes the real-time data pipeline: Dota 2's Game State Integration (GSI) sends HTTP POST requests containing JSON game state data to the backend, which parses and holds the latest state in memory, then pushes throttled updates to the frontend via WebSocket. The infrastructure also includes Nginx configuration for routing GSI and WebSocket traffic, a settings panel for generating the GSI config file, and a connection status indicator.

The entire pipeline requires zero new backend Python dependencies -- FastAPI already includes WebSocket support via Starlette, and `uvicorn[standard]` already bundles the `websockets` package. The frontend also needs no new dependencies -- a custom `useWebSocket` hook is straightforward and avoids adding a library for a single WebSocket connection. The primary complexity lies in correctly understanding the GSI JSON payload structure (which differs between player mode and spectator mode), implementing throttled broadcasting, and configuring Nginx WebSocket proxying with correct upgrade headers.

**Primary recommendation:** Build a minimal GSI receiver as a plain FastAPI POST endpoint at `/gsi`, a Python dataclass-based state manager singleton, and a FastAPI WebSocket endpoint at `/ws` with a ConnectionManager that broadcasts throttled JSON updates. No new dependencies needed.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Settings page accessible via gear icon in the header bar (top-right, next to data freshness indicator)
- **D-02:** Gear icon opens a slide-over panel from the right side, overlaying main content with dimmed backdrop
- **D-03:** Settings panel contains IP input field (pre-filled if possible), port display, and a "Download .cfg file" button
- **D-04:** Step-by-step instructions below the download button showing exact file placement path
- **D-05:** Generated .cfg file named `gamestate_integration_prismlab.cfg` with user's IP and port 8421
- **D-06:** Colored dot + "GSI" label in the header bar, between the logo and data freshness indicator
- **D-07:** Three states: green (Connected -- receiving live data), gray (Idle -- no game or not configured), red (Lost -- was connected, dropped)
- **D-08:** Tooltip on hover shows details: connection status label, last update timestamp, game time if in-game, WebSocket connection state
- **D-09:** All traffic routes through Nginx on port 8421 -- single entry point for frontend, API, GSI, and WebSocket
- **D-10:** Nginx `/gsi` location block proxies to backend `/gsi` endpoint
- **D-11:** Nginx `/ws` location block proxies to backend `/ws` endpoint with WebSocket upgrade headers
- **D-12:** GSI config file points to `http://<user-ip>:8421/gsi` -- same port as everything else
- **D-13:** Parse all v2.0 fields upfront in Phase 10: hero_name, gold, GPM, net_worth, items (inventory + backpack), game_clock, kills, deaths, assists, team_side, map.game_state
- **D-14:** In-memory only -- no DB persistence for GSI data. Ephemeral state in a Python dataclass/manager singleton
- **D-15:** Backend throttles WebSocket pushes to 1 per second (GSI sends at ~2Hz, we aggregate and push at 1Hz)
- **D-16:** Only push when parsed fields have actually changed within the throttle window

### Claude's Discretion
- Exact GSI JSON field paths for parsing (provider, map, player, hero, items sections)
- WebSocket message format (JSON structure for frontend consumption)
- GSI auth token handling (Dota 2 GSI supports auth tokens in config)
- Slide-over panel animation and dismiss behavior
- Throttle implementation approach (asyncio task, timer, etc.)
- WebSocket auto-reconnect strategy on frontend side

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GSI-01 | Backend receives Dota 2 GSI HTTP POST data at `/gsi` endpoint and parses game state | GSI protocol research: POST with JSON body, auth token in payload, must return HTTP 2XX for delta tracking; field path mapping for player-mode data |
| WS-01 | WebSocket endpoint pushes GSI state updates from backend to frontend in real-time | FastAPI WebSocket ConnectionManager pattern, throttled broadcasting via asyncio, JSON message format |
| INFRA-01 | Nginx config updated with WebSocket upgrade headers and file upload support | Nginx WebSocket proxying requires `proxy_http_version 1.1`, `Upgrade $http_upgrade`, `Connection "upgrade"`, plus `proxy_read_timeout` for keepalive |
| INFRA-02 | GSI config file generator (`gamestate_integration_prismlab.cfg`) with correct server IP for user's setup | GSI config format: VDF-style key-value pairs with data section toggles, auth token, URI, throttle/buffer settings |

</phase_requirements>

## Standard Stack

### Core (Already Installed -- No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.1 | GSI POST endpoint + WebSocket endpoint | Already installed; WebSocket support built-in via Starlette |
| uvicorn[standard] | 0.42.0 | ASGI server with WebSocket protocol | Already installed; `[standard]` extra includes `websockets` package |
| Pydantic | 2.12.5 | GSI payload validation models | Already installed; validates incoming GSI JSON |
| Zustand | 5.0.12 | Frontend GSI state store | Already installed; extend with `gsiStore.ts` |

### Supporting (No New Installs Needed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio (stdlib) | Python 3.12 | Throttle timer, background tasks | Throttled WebSocket push loop |
| React hooks (built-in) | React 19 | Custom `useWebSocket` hook | WebSocket connection with auto-reconnect |
| Tailwind CSS | 4.2.2 | Settings panel, status indicator styling | Already in use project-wide |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom useWebSocket hook | react-use-websocket npm package | Adds a dependency for a single WebSocket connection; custom hook is ~60 lines and gives full control over reconnect behavior |
| In-memory state manager | Redis pub/sub | Overkill for single-user, single-process app; Redis would only matter at scale with multiple workers |
| Raw asyncio throttle | APScheduler job | APScheduler is already in requirements.txt but interval jobs are wrong pattern for "push when changed within window" |

**Installation:** No new packages needed. All dependencies already exist in `requirements.txt` and `package.json`.

## Architecture Patterns

### Recommended Backend Structure

```
prismlab/backend/
├── main.py                     # Add GSI route + WS endpoint registration, GSI manager to lifespan
├── config.py                   # Add GSI_AUTH_TOKEN setting (optional)
├── gsi/
│   ├── __init__.py
│   ├── models.py               # Pydantic models for GSI payload parsing
│   ├── receiver.py             # POST /gsi endpoint handler
│   ├── state_manager.py        # In-memory singleton holding parsed game state
│   └── ws_manager.py           # WebSocket ConnectionManager + throttled broadcast
└── api/routes/
    └── settings.py             # GET /api/gsi-config endpoint (generates .cfg file content)
```

### Recommended Frontend Structure

```
prismlab/frontend/src/
├── hooks/
│   └── useWebSocket.ts         # Custom WebSocket hook with auto-reconnect
├── stores/
│   └── gsiStore.ts             # Zustand store for live GSI state + connection status
├── components/
│   ├── layout/
│   │   └── Header.tsx          # Modified: add GSI status indicator + gear icon
│   └── settings/
│       └── SettingsPanel.tsx    # Slide-over panel with GSI config generator
```

### Pattern 1: GSI Receiver (HTTP POST Endpoint)

**What:** Dota 2 sends HTTP POST requests with JSON body to `/gsi` at ~2Hz. The endpoint parses the JSON, extracts relevant fields, updates the in-memory state manager, and returns HTTP 200.

**When to use:** Every incoming GSI POST.

**Example:**
```python
# Source: Dota 2 GSI protocol documentation + FastAPI patterns
from fastapi import APIRouter, Request, Response

router = APIRouter()

@router.post("/gsi")
async def receive_gsi(request: Request) -> Response:
    """Receive Dota 2 Game State Integration data.

    The Dota 2 client sends HTTP POST with JSON body.
    Must return HTTP 2XX for the client to track deltas
    via 'previously' and 'added' fields.
    """
    body = await request.json()

    # Validate auth token if configured
    auth = body.get("auth", {})
    if GSI_AUTH_TOKEN and auth.get("token") != GSI_AUTH_TOKEN:
        return Response(status_code=401)

    # Parse and update state
    parsed = parse_gsi_payload(body)
    state_manager.update(parsed)

    return Response(status_code=200)
```

### Pattern 2: WebSocket ConnectionManager with Throttled Broadcast

**What:** Manages WebSocket connections and broadcasts state changes at max 1Hz, only when data has changed.

**When to use:** Frontend connects via `ws://host/ws`, receives throttled game state updates.

**Example:**
```python
# Source: FastAPI official WebSocket docs + asyncio patterns
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

class WSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
        self._broadcast_task: asyncio.Task | None = None
        self._last_sent_hash: int = 0

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def start_broadcast_loop(self, state_manager):
        """Run in background: check for state changes every 1s, broadcast if changed."""
        while True:
            await asyncio.sleep(1.0)
            state = state_manager.get_state()
            if state is None:
                continue
            state_hash = hash(state.json())
            if state_hash == self._last_sent_hash:
                continue
            self._last_sent_hash = state_hash
            await self._broadcast(state.model_dump_json())

    async def _broadcast(self, message: str):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)
```

### Pattern 3: Custom React WebSocket Hook with Auto-Reconnect

**What:** A React hook that manages WebSocket connection lifecycle with exponential backoff reconnection.

**When to use:** Frontend connects to `/ws` on mount, auto-reconnects on disconnection.

**Example:**
```typescript
// Custom hook pattern -- no external dependency needed
function useWebSocket(url: string) {
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [lastMessage, setLastMessage] = useState<GsiState | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);

  const connect = useCallback(() => {
    setStatus('connecting');
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttemptRef.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
    };

    ws.onclose = () => {
      setStatus('disconnected');
      // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
      const delay = Math.min(1000 * 2 ** reconnectAttemptRef.current, 10000);
      reconnectAttemptRef.current += 1;
      setTimeout(connect, delay);
    };

    wsRef.current = ws;
  }, [url]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { status, lastMessage };
}
```

### Pattern 4: GSI Config File Generator

**What:** Backend endpoint that generates the `.cfg` file content with user's IP pre-filled.

**When to use:** User clicks "Download .cfg file" in settings panel.

**Example:**
```python
# GSI config uses Valve's VDF (KeyValues) format, not JSON
GSI_CONFIG_TEMPLATE = '''"gamestate_integration_prismlab"
{{
    "uri"               "http://{host}:{port}/gsi"
    "timeout"           "5.0"
    "buffer"            "0.1"
    "throttle"          "0.5"
    "heartbeat"         "30.0"
    "data"
    {{
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
    }}
    "auth"
    {{
        "token"         "{token}"
    }}
}}
'''
```

### Anti-Patterns to Avoid

- **Storing GSI data in the database:** GSI sends updates every 0.5s. Writing to SQLite at that rate would create I/O bottleneck and the data is ephemeral anyway. Use in-memory dataclass only.
- **Parsing the full GSI payload:** The raw JSON can be very large with buildings, wearables, abilities, etc. Parse only the fields needed (D-13). Ignore the rest.
- **Broadcasting every GSI update to WebSocket:** GSI sends at ~2Hz. Broadcasting every update wastes bandwidth and causes unnecessary React re-renders. Throttle to 1Hz and only when data changed (D-15, D-16).
- **Using `ws.receive_text()` in a blocking loop for push-only WebSocket:** The frontend only receives, never sends meaningful data. The WebSocket endpoint should accept the connection, then the broadcast loop pushes data. The receive loop only needs to detect disconnection.
- **Forgetting to return HTTP 200 from GSI endpoint:** If the endpoint returns non-2XX, Dota 2 stops sending `previously` and `added` delta fields and treats every request as fresh. Always return 200 even if parsing fails.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket protocol handling | Raw socket implementation | FastAPI `WebSocket` (from Starlette) | Handles upgrade handshake, ping/pong, frame encoding |
| GSI config file format | Custom string builder | Template string with `.format()` | VDF format is simple key-value, template is sufficient |
| WebSocket reconnection | Complex retry state machine | Simple `setTimeout` with exponential backoff in `onclose` | Browser WebSocket API handles all protocol details; just reconnect |
| JSON change detection | Deep equality comparison | Hash the serialized JSON string | Fast, O(1) comparison instead of recursive field-by-field |

**Key insight:** The entire pipeline is a composition of simple, well-understood patterns (HTTP POST receiver, in-memory state, WebSocket broadcast, timer-based throttle). No middleware, no message queues, no pub/sub -- just direct function calls in a single-process Python app.

## Dota 2 GSI Protocol Reference

### Configuration File Format

The config file uses Valve's VDF (Valve Data Format) -- NOT JSON. It goes in:
```
<Steam>/steamapps/common/dota 2 beta/game/dota/cfg/gamestate_integration/gamestate_integration_prismlab.cfg
```

Key configuration parameters:

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `uri` | `http://<ip>:8421/gsi` | Where Dota sends POST requests |
| `timeout` | `5.0` | Seconds before request is considered timed out |
| `buffer` | `0.1` | Seconds to buffer/combine events before sending |
| `throttle` | `0.5` | Minimum seconds between requests (~2Hz) |
| `heartbeat` | `30.0` | Seconds between pings when no data changes |
| `data` section | `"1"` per field | Which data categories to include |
| `auth.token` | string | Auth token included in every POST payload |

### GSI JSON Payload Structure (Player Mode)

When the player is PLAYING (not spectating), the JSON is flat -- not nested with team/player indices. This is the structure Prismlab will receive:

```json
{
  "provider": {
    "name": "Dota 2",
    "appid": 570,
    "version": 47,
    "timestamp": 1234567890
  },
  "map": {
    "name": "start",
    "matchid": "1234567890",
    "game_time": 653,
    "clock_time": 600,
    "daytime": true,
    "nightstalker_night": false,
    "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    "paused": false,
    "win_team": "none",
    "customgamename": "",
    "ward_purchase_cooldown": 0
  },
  "player": {
    "steamid": "76561198012345678",
    "accountid": "12345678",
    "name": "PlayerName",
    "activity": "playing",
    "kills": 3,
    "deaths": 1,
    "assists": 7,
    "last_hits": 145,
    "denies": 12,
    "kill_streak": 2,
    "commands_issued": 4521,
    "team_name": "radiant",
    "gold": 1523,
    "gold_reliable": 500,
    "gold_unreliable": 1023,
    "gold_from_hero_kills": 800,
    "gold_from_creep_kills": 4200,
    "gold_from_income": 2000,
    "gold_from_shared": 300,
    "gpm": 456,
    "xpm": 512,
    "net_worth": 12500
  },
  "hero": {
    "id": 1,
    "name": "npc_dota_hero_antimage",
    "level": 12,
    "xpos": -1234,
    "ypos": 567,
    "alive": true,
    "respawn_seconds": 0,
    "buyback_cost": 876,
    "buyback_cooldown": 0,
    "health": 1200,
    "max_health": 1400,
    "health_percent": 85,
    "mana": 400,
    "max_mana": 600,
    "mana_percent": 66,
    "silenced": false,
    "stunned": false,
    "disarmed": false,
    "magicimmune": false,
    "hexed": false,
    "muted": false,
    "break": false,
    "has_debuff": false,
    "aghanims_scepter": false,
    "aghanims_shard": false
  },
  "items": {
    "slot0": { "name": "item_power_treads", "purchaser": 0, "can_cast": false, "cooldown": 0, "passive": true, "charges": 0 },
    "slot1": { "name": "item_bfury", "purchaser": 0, "can_cast": false, "cooldown": 0, "passive": true, "charges": 0 },
    "slot2": { "name": "item_manta", "purchaser": 0, "can_cast": true, "cooldown": 0, "passive": false, "charges": 0 },
    "slot3": { "name": "empty" },
    "slot4": { "name": "empty" },
    "slot5": { "name": "empty" },
    "slot6": { "name": "item_tpscroll", "purchaser": 0, "can_cast": true, "cooldown": 0, "passive": false, "charges": 1 },
    "slot7": { "name": "empty" },
    "slot8": { "name": "empty" },
    "stash0": { "name": "empty" },
    "stash1": { "name": "empty" },
    "stash2": { "name": "empty" },
    "stash3": { "name": "empty" },
    "stash4": { "name": "empty" },
    "stash5": { "name": "empty" },
    "teleport0": { "name": "item_tpscroll", "purchaser": 0, "can_cast": true, "cooldown": 0, "passive": false, "charges": 1 },
    "neutral0": { "name": "item_mysterious_hat", "purchaser": 0, "can_cast": false, "cooldown": 0, "passive": true, "charges": 0 }
  },
  "auth": {
    "token": "prismlab_token_123"
  },
  "previously": {
    "player": { "gold": 1480 },
    "map": { "clock_time": 599 }
  },
  "added": {}
}
```

**Critical notes on the payload:**
- **Player mode is FLAT:** `player`, `hero`, `items` are direct objects, NOT nested under `team#:player#`
- **Spectator mode is NESTED:** Would be `player.team2.player0.kills` etc. -- we do NOT need this
- **Items use slot0-slot8** for inventory (6 main + 3 backpack), **stash0-stash5** for stash, **teleport0** for TP slot, **neutral0** for neutral item slot
- **`"name": "empty"`** indicates an empty slot
- **Item names use `item_` prefix:** e.g., `item_power_treads`, `item_bfury`. Strip the `item_` prefix to match our internal_name in the database
- **`previously` and `added` sections** only appear when the server returns HTTP 2XX. They show what changed since last successful delivery. Useful for efficient change detection but not required -- we can just compare full state
- **`map.game_state` values:** `DOTA_GAMERULES_STATE_WAIT_FOR_PLAYERS_TO_LOAD`, `DOTA_GAMERULES_STATE_HERO_SELECTION`, `DOTA_GAMERULES_STATE_PRE_GAME`, `DOTA_GAMERULES_STATE_GAME_IN_PROGRESS`, `DOTA_GAMERULES_STATE_POST_GAME`, `DOTA_GAMERULES_STATE_DISCONNECT`
- **`player.team_name`** is `"radiant"` or `"dire"` -- maps directly to our `side` field
- **Heartbeat pings** are sent every 30s when no game data changes -- these are valid POSTs with minimal/unchanged data

### GSI Data Field Mapping (D-13 Fields)

| v2.0 Field | GSI JSON Path | Notes |
|------------|---------------|-------|
| hero_name | `hero.name` | Internal name like `npc_dota_hero_antimage` -- need to strip `npc_dota_hero_` prefix to match our DB |
| gold | `player.gold` | Current unreliable + reliable total |
| GPM | `player.gpm` | Gold per minute |
| net_worth | `player.net_worth` | Total net worth |
| items (inventory) | `items.slot0` through `items.slot5` | 6 main inventory slots |
| items (backpack) | `items.slot6` through `items.slot8` | 3 backpack slots |
| items (neutral) | `items.neutral0` | Neutral item slot |
| items (TP) | `items.teleport0` | TP scroll slot |
| game_clock | `map.clock_time` | Game clock in seconds (what players see) |
| kills | `player.kills` | Player's kill count |
| deaths | `player.deaths` | Player's death count |
| assists | `player.assists` | Player's assist count |
| team_side | `player.team_name` | `"radiant"` or `"dire"` |
| map.game_state | `map.game_state` | Game phase string (see values above) |

## Common Pitfalls

### Pitfall 1: Not Returning HTTP 200 from GSI Endpoint
**What goes wrong:** Dota 2 stops sending `previously` and `added` delta fields. Every POST becomes a full state dump with no change tracking.
**Why it happens:** Endpoint throws an exception or returns 4XX/5XX on malformed data.
**How to avoid:** Always return `Response(status_code=200)` in a try/except. Log parsing errors but never fail the response.
**Warning signs:** `previously` and `added` keys never appear in incoming payloads.

### Pitfall 2: Nginx Drops WebSocket Connection After 60 Seconds
**What goes wrong:** WebSocket connection silently closes every 60 seconds.
**Why it happens:** Nginx default `proxy_read_timeout` is 60 seconds. If no data crosses the connection (e.g., no game running), Nginx closes it.
**How to avoid:** Set `proxy_read_timeout 86400s` (24 hours) in the `/ws` location block. Also implement ping/pong at the application level as a safety net.
**Warning signs:** WebSocket status flips between connected/disconnected on a ~60s cycle when no game is running.

### Pitfall 3: WebSocket Broadcast Blocking on Dead Connection
**What goes wrong:** A single disconnected client that hasn't triggered `WebSocketDisconnect` blocks the broadcast loop, delaying updates to all other clients.
**Why it happens:** `await ws.send_text()` hangs on a dead socket until timeout.
**How to avoid:** Wrap each `send_text()` in try/except, collect dead connections, remove them after the broadcast loop iteration.
**Warning signs:** All clients experience delayed updates when one client has a flaky connection.

### Pitfall 4: Spectator vs Player Mode JSON Confusion
**What goes wrong:** Parser expects `player.team2.player0.kills` but receives `player.kills`.
**Why it happens:** GSI JSON structure differs between player mode (flat) and spectator mode (nested by team/player).
**How to avoid:** Prismlab only supports player mode. Parse flat `player.*`, `hero.*`, `items.*` paths. Ignore or reject spectator-mode payloads (detectable by checking if `player` contains `team2` key).
**Warning signs:** Null/missing fields despite game being active.

### Pitfall 5: Item Name Prefix Mismatch
**What goes wrong:** GSI item names like `item_power_treads` don't match the database `internal_name` field `power_treads`.
**Why it happens:** GSI prefixes all item names with `item_`. The Prismlab database stores them without the prefix.
**How to avoid:** Strip `item_` prefix during parsing. Also handle `"empty"` as a null/missing item.
**Warning signs:** Items never match, inventory always appears empty in the UI.

### Pitfall 6: Hero Name Format Mismatch
**What goes wrong:** GSI sends `npc_dota_hero_antimage` but the database stores `npc_dota_hero_antimage` in `internal_name`.
**Why it happens:** The `hero.name` GSI field uses the full internal name.
**How to avoid:** Match against the `internal_name` column in the Hero table, or strip `npc_dota_hero_` to get the short name used for CDN image URLs.
**Warning signs:** Hero auto-detection fails even when GSI data is flowing correctly.

### Pitfall 7: WebSocket Through Cloudflare Tunnel
**What goes wrong:** WebSocket connections fail or drop frequently when accessed via Cloudflare Tunnel.
**Why it happens:** Cloudflare has specific WebSocket support requirements and may impose timeouts.
**How to avoid:** Ensure Cloudflare Tunnel is configured to allow WebSocket connections (it does by default for paid plans, and for free plans with the `wss://` scheme). Test end-to-end through the tunnel during this phase. The STATE.md explicitly flags this as needing validation.
**Warning signs:** WebSocket works on LAN but fails through the tunnel.

## Code Examples

### GSI Pydantic Models for Parsing

```python
# Source: Dota 2 GSI protocol + Pydantic v2 patterns
from pydantic import BaseModel, Field
from typing import Optional


class GsiItemSlot(BaseModel):
    name: str = "empty"
    purchaser: int = 0
    can_cast: bool = False
    cooldown: float = 0
    passive: bool = False
    charges: int = 0


class GsiMap(BaseModel):
    name: str = ""
    matchid: str = ""
    game_time: float = 0
    clock_time: float = 0
    daytime: bool = True
    game_state: str = ""
    paused: bool = False


class GsiPlayer(BaseModel):
    steamid: str = ""
    name: str = ""
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    gold: int = 0
    gold_reliable: int = 0
    gold_unreliable: int = 0
    gpm: int = 0
    xpm: int = 0
    net_worth: int = 0
    team_name: str = ""


class GsiHero(BaseModel):
    id: int = 0
    name: str = ""
    level: int = 0
    alive: bool = True
    health: int = 0
    max_health: int = 0
    mana: int = 0
    max_mana: int = 0


class GsiItems(BaseModel):
    slot0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot1: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot2: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot3: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot4: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot5: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot6: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    slot7: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    slot8: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    stash0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash1: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash2: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash3: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash4: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash5: GsiItemSlot = Field(default_factory=GsiItemSlot)
    teleport0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    neutral0: GsiItemSlot = Field(default_factory=GsiItemSlot)
```

### Parsed Game State Dataclass (In-Memory State Manager)

```python
# The state manager holds the latest parsed, normalized game state
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class ParsedGsiState:
    """Normalized game state from GSI, ready for WebSocket broadcast."""
    hero_name: str = ""                    # Short name, e.g., "antimage"
    hero_id: int = 0
    hero_level: int = 0
    gold: int = 0
    gpm: int = 0
    net_worth: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    items_inventory: list[str] = field(default_factory=list)   # 6 slots
    items_backpack: list[str] = field(default_factory=list)    # 3 slots
    items_neutral: str = ""
    game_clock: int = 0
    game_state: str = ""                   # e.g., "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
    team_side: str = ""                    # "radiant" or "dire"
    is_alive: bool = True
    timestamp: float = 0.0                 # time.time() when last updated


class GsiStateManager:
    """Singleton managing the latest parsed GSI state."""

    def __init__(self):
        self._state: Optional[ParsedGsiState] = None
        self._connected: bool = False
        self._last_update: float = 0.0

    @property
    def is_connected(self) -> bool:
        """True if we've received data recently (within 10s)."""
        return self._connected and (time.time() - self._last_update) < 10.0

    def update(self, raw: dict) -> None:
        """Parse raw GSI JSON and update state."""
        # ... parsing logic ...
        self._last_update = time.time()
        self._connected = True

    def get_state(self) -> Optional[ParsedGsiState]:
        return self._state

    def get_connection_info(self) -> dict:
        """Connection metadata for status indicator."""
        return {
            "connected": self.is_connected,
            "last_update": self._last_update,
            "game_clock": self._state.game_clock if self._state else None,
            "game_state": self._state.game_state if self._state else None,
        }
```

### Nginx WebSocket Configuration

```nginx
# Source: Nginx official WebSocket proxying docs
# Add to existing nginx.conf inside the server block

# GSI endpoint -- Dota 2 sends HTTP POST here
location /gsi {
    proxy_pass http://prismlab-backend:8000/gsi;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# WebSocket endpoint -- frontend connects here
location /ws {
    proxy_pass http://prismlab-backend:8000/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 86400s;  # 24 hours -- prevent Nginx from closing idle WS
    proxy_send_timeout 86400s;
}
```

### WebSocket Message Format (Frontend Consumption)

```typescript
// JSON structure pushed from backend to frontend via WebSocket
interface GsiWebSocketMessage {
  type: "game_state" | "connection_status";
  data: {
    hero_name: string;       // "antimage"
    hero_id: number;
    hero_level: number;
    gold: number;
    gpm: number;
    net_worth: number;
    kills: number;
    deaths: number;
    assists: number;
    items_inventory: string[];  // ["power_treads", "bfury", "manta", "", "", ""]
    items_backpack: string[];   // ["", "", ""]
    items_neutral: string;      // "mysterious_hat" or ""
    game_clock: number;         // seconds
    game_state: string;         // "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
    team_side: string;          // "radiant" | "dire"
    is_alive: boolean;
    timestamp: number;
  };
}
```

### GSI Zustand Store

```typescript
// Follows existing gameStore.ts Zustand flat-store pattern
interface GsiStore {
  // Connection state
  wsStatus: "connected" | "disconnected" | "connecting";
  gsiStatus: "connected" | "idle" | "lost";
  lastUpdate: number | null;

  // Live game data from GSI
  liveState: GsiWebSocketMessage["data"] | null;

  // Actions
  setWsStatus: (status: "connected" | "disconnected" | "connecting") => void;
  setGsiStatus: (status: "connected" | "idle" | "lost") => void;
  updateLiveState: (data: GsiWebSocketMessage["data"]) => void;
  clearLiveState: () => void;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Polling HTTP endpoint | WebSocket push | N/A (greenfield) | Sub-second latency for game state updates |
| External GSI library (dota2gsipy) | Direct FastAPI endpoint | N/A | Zero dependencies; GSI protocol is just HTTP POST + JSON |
| react-use-websocket library | Custom hook (~60 lines) | N/A | No dependency; full control over reconnect behavior |

**Deprecated/outdated:**
- The `dota2gsipy` Python library exists but is unmaintained and adds unnecessary abstraction. The GSI protocol is simply HTTP POST with JSON body -- a single FastAPI endpoint handler is all that's needed.

## Open Questions

1. **Exact item slot numbering for backpack**
   - What we know: slot0-slot5 are main inventory, slot6-slot8 appear to be backpack based on multiple GSI library implementations
   - What's unclear: Valve has changed inventory slot layout before (adding backpack, TP slot, neutral slot over time). The exact numbering may vary by Dota 2 version.
   - Recommendation: Log the first few raw GSI payloads during testing to confirm slot mappings. Build the parser to handle unknown slot names gracefully.

2. **WebSocket through Cloudflare Tunnel behavior**
   - What we know: Cloudflare Tunnel supports WebSocket, but STATE.md flags this as needing validation.
   - What's unclear: Whether idle WebSocket connections survive Cloudflare's timeout policies for the user's plan tier.
   - Recommendation: Test during Phase 10 implementation. If Cloudflare drops idle connections, implement application-level ping/pong (send a "heartbeat" JSON message every 30s from the server).

3. **GSI auth token management**
   - What we know: The `.cfg` file can include an auth token that appears in every POST payload.
   - What's unclear: Whether to make the token configurable or hardcode a default.
   - Recommendation: Generate a random token when creating the `.cfg` file, store it in localStorage on the frontend, and pass it to the backend via config. For simplicity in v2.0, a hardcoded default token (e.g., `"prismlab"`) is acceptable -- the app is single-user on a private network.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| FastAPI (WebSocket) | WS-01 | Yes | 0.135.1 | -- |
| uvicorn[standard] (websockets) | WS-01 | Yes | 0.42.0 | -- |
| Pydantic | GSI-01 | Yes | 2.12.5 | -- |
| Nginx | INFRA-01 | Yes | In Docker image | -- |
| Zustand | Frontend GSI store | Yes | 5.0.12 | -- |
| Dota 2 client (for testing) | GSI-01 end-to-end | External | -- | Use curl/httpie to simulate GSI POSTs |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:**
- Dota 2 client not available in dev environment -- simulate GSI POSTs with curl or a Python test script.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (backend) | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Framework (frontend) | vitest 4.1.0 + jsdom + @testing-library/react |
| Config file (backend) | pytest.ini or pyproject.toml (uses default discovery) |
| Config file (frontend) | `prismlab/frontend/vitest.config.ts` |
| Quick run command (backend) | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| Quick run command (frontend) | `cd prismlab/frontend && npx vitest run` |
| Full suite command | `cd prismlab/backend && python -m pytest tests/ -v && cd ../frontend && npx vitest run` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GSI-01 | POST /gsi receives and parses GSI JSON | unit + integration | `python -m pytest tests/test_gsi.py -x` | Wave 0 |
| GSI-01 | Auth token validation | unit | `python -m pytest tests/test_gsi.py::test_auth_token -x` | Wave 0 |
| GSI-01 | Parse all D-13 fields correctly | unit | `python -m pytest tests/test_gsi.py::test_parse_fields -x` | Wave 0 |
| WS-01 | WebSocket connection + message reception | integration | `python -m pytest tests/test_ws.py -x` | Wave 0 |
| WS-01 | Throttled broadcast (1Hz max) | unit | `python -m pytest tests/test_ws.py::test_throttle -x` | Wave 0 |
| WS-01 | Only broadcast on change (D-16) | unit | `python -m pytest tests/test_ws.py::test_change_detection -x` | Wave 0 |
| INFRA-01 | Nginx routes /gsi and /ws correctly | manual (Docker) | Manual: `docker compose up` + curl | N/A |
| INFRA-02 | GSI config file generation with user IP | unit | `python -m pytest tests/test_gsi.py::test_config_generation -x` | Wave 0 |
| Frontend | useWebSocket hook with auto-reconnect | unit | `npx vitest run src/hooks/useWebSocket.test.ts` | Wave 0 |
| Frontend | gsiStore state updates | unit | `npx vitest run src/stores/gsiStore.test.ts` | Wave 0 |
| Frontend | Settings panel renders and generates config | unit | `npx vitest run src/components/settings/SettingsPanel.test.tsx` | Wave 0 |
| Frontend | GSI status indicator states | unit | `npx vitest run src/components/layout/GsiStatusIndicator.test.tsx` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/backend && python -m pytest tests/test_gsi.py tests/test_ws.py -x -q`
- **Per wave merge:** Full suite (backend + frontend)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `prismlab/backend/tests/test_gsi.py` -- covers GSI-01, INFRA-02 (receiver, parser, config generator)
- [ ] `prismlab/backend/tests/test_ws.py` -- covers WS-01 (WebSocket connection, throttle, change detection)
- [ ] `prismlab/frontend/src/hooks/useWebSocket.test.ts` -- covers WebSocket hook behavior
- [ ] `prismlab/frontend/src/stores/gsiStore.test.ts` -- covers GSI store state management
- [ ] `prismlab/frontend/src/components/settings/SettingsPanel.test.tsx` -- covers settings panel UI
- [ ] `prismlab/frontend/src/components/layout/GsiStatusIndicator.test.tsx` -- covers status indicator

## Project Constraints (from CLAUDE.md)

- **Tech stack:** React 18 (actually 19 in package.json) + Vite + TypeScript + Tailwind CSS + Zustand (frontend), Python 3.12 + FastAPI (backend)
- **Deployment:** Docker Compose on Unraid; backend port 8420, frontend/Nginx port 8421
- **Dark theme:** Spectral cyan (#00d4ff) primary, Radiant teal (#6aff97), Dire red (#ff5555) -- use these for connection status indicators
- **Code style:** TypeScript strict mode, functional components, hooks; Python type hints, async endpoints, Pydantic models
- **Project structure:** All code under `prismlab/` subdirectory
- **Hero/item images:** Steam CDN, not self-hosted
- **Desktop-first layout**

## Sources

### Primary (HIGH confidence)
- [FastAPI WebSocket docs](https://fastapi.tiangolo.com/advanced/websockets/) -- WebSocket endpoint patterns, ConnectionManager, dependency injection
- [Nginx WebSocket proxying docs](https://nginx.org/en/docs/http/websocket.html) -- Required headers, proxy_http_version, timeout configuration
- [Dota2GSI C# library](https://github.com/antonpup/Dota2GSI) -- Complete GSI data model with all sections and fields
- [dota2-gsi Node.js library](https://github.com/xzion/dota2-gsi) -- Player mode vs spectator mode differences, field paths, config format
- [osztenkurden/dota2gsi](https://github.com/osztenkurden/dota2gsi) -- Player stats fields (gold, gpm, net_worth, kills, etc.)

### Secondary (MEDIUM confidence)
- [Game State Integration Intro](https://auo.nu/posts/game-state-integration-intro/) -- Config file format, throttle/buffer/heartbeat parameters
- [Valve Developer Wiki CS:GO GSI](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Game_State_Integration) -- Shared GSI protocol: HTTP 2XX requirement, previously/added delta behavior, auth token format
- [react-use-websocket](https://github.com/robtaussig/react-use-websocket) -- Auto-reconnect patterns (used as reference for custom hook design)
- [FastAPI WebSocket broadcast guide](https://dev-faizan.medium.com/building-real-time-applications-with-fastapi-websockets-a-complete-guide-2025-40f29d327733) -- Connection cleanup, dead connection handling

### Tertiary (LOW confidence)
- [dota2gsipy Python library](https://github.com/Daniel-EST/dota2gsipy) -- Python GSI patterns (unmaintained, reference only)
- GSI item slot numbering (slot6-8 as backpack) -- consistent across libraries but no official Valve documentation found

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all dependencies already installed, zero new packages
- Architecture: HIGH -- well-established patterns (HTTP POST receiver, WebSocket broadcast, Nginx proxy)
- GSI protocol: HIGH -- cross-verified across 5 independent library implementations in different languages
- GSI field paths: MEDIUM -- consistent across libraries but player-mode structure has less documentation than spectator mode; recommend logging raw payloads during first integration test
- Pitfalls: HIGH -- common issues well-documented across FastAPI and Nginx communities

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain -- GSI protocol hasn't changed in years)
