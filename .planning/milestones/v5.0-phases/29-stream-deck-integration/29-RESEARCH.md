# Phase 29: Stream Deck Integration - Research

**Researched:** 2026-03-29
**Domain:** Elgato Stream Deck SDK v2 (Node.js), WebSocket consumer, Canvas image rendering
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — discuss phase was skipped per workflow.skip_discuss setting.

### Claude's Discretion
All implementation choices are at Claude's discretion. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

### Deferred Ideas (OUT OF SCOPE)
None — discuss phase skipped.
</user_constraints>

---

## Summary

Phase 29 is a standalone Elgato Stream Deck plugin (Node.js, SDK v2) that connects to the Prismlab backend's existing WebSocket endpoint (`ws://<host>:8420/ws`) as a pure display consumer. The backend already broadcasts a `{"type": "game_state", "data": {...}}` message at 1 Hz whenever game state changes. The plugin requires zero backend changes — it just subscribes to that feed and renders the live Dota 2 data onto Stream Deck XL buttons.

The Stream Deck SDK v2 uses TypeScript, a `SingletonAction` class pattern, and communicates with the Stream Deck software via a local WebSocket managed entirely by the SDK. Plugin authors connect to external services using standard Node.js mechanisms (`ws` package or native `WebSocket`). Dynamic button faces are rendered as base64-encoded PNG or SVG data URLs passed to `ev.action.setImage()`. The `this.actions.forEach()` method on a `SingletonAction` lets one code path update all visible instances of a button type simultaneously.

The plugin lives in `prismlab/stream-deck-plugin/` with its own `package.json`, TypeScript source, and compiled `.sdPlugin` output directory. The Stream Deck CLI (`@elgato/cli`) scaffolds, hot-reloads during development (`npm run watch`), and packages for distribution (`streamdeck pack`). The Stream Deck app must be installed locally on the Windows machine for development and testing; the Stream Deck app is **not** installed in this environment, so testing requires manual installation of the app before first run.

**Primary recommendation:** Scaffold the plugin with `streamdeck create` (or manually mirror the scaffolded structure), implement a module-level WebSocket connection manager that connects to the Prismlab backend, use `this.actions.forEach()` in a polling loop to push state to all visible button instances, and render button faces as inline SVG strings encoded as data URLs (no native module dependency, unlike `canvas`).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@elgato/streamdeck` | 2.0.4 | Stream Deck SDK v2 — action lifecycle, `setImage`, `setTitle`, settings | Official Elgato SDK; required for Marketplace distribution |
| `@elgato/cli` | 1.7.3 | Scaffold, watch (hot-reload), pack (distribute) | Official companion CLI |
| TypeScript | project default (~5.x) | Type-safe plugin source | SDK ships types; `streamdeck create` scaffolds tsconfig |
| `ws` | 8.20.0 | Node.js WebSocket client to connect to Prismlab backend | De facto standard Node.js WebSocket library; pure JS, no native modules |
| `rollup` | scaffold default | Bundles `src/` to `*.sdPlugin/bin/plugin.js` | Stream Deck CLI scaffold generates this config |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@types/ws` | latest | TypeScript types for the `ws` package | Needed with `ws` in TypeScript projects |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ws` (reconnect manual) | `reconnecting-websocket` | `reconnecting-websocket` works in both browser and Node; simpler retry logic. However `ws` is lighter and manual exponential backoff (already proven in `useWebSocket.ts`) is straightforward |
| SVG data URL for images | `canvas` npm package | `canvas` requires native C++ bindings (Cairo) — adds build complexity, needs `node-gyp`, likely breaks on some environments. SVG strings are pure JS, same visual quality, easier to maintain |
| Single monolithic action | Separate action per data type | One action per data type (gold, KDA, clock, rosh, towers, items) is cleaner — user drags only the buttons they want onto their XL layout |

**Installation:**
```bash
npm install -g @elgato/cli
# Inside prismlab/stream-deck-plugin/:
npm install @elgato/streamdeck ws @types/ws
```

**Version verification (confirmed 2026-03-29):**
- `@elgato/streamdeck`: 2.0.4 (via `npm view @elgato/streamdeck version`)
- `@elgato/cli`: 1.7.3 (via `npm view @elgato/cli version`)
- `ws`: 8.20.0 (via `npm view ws version`)

---

## Architecture Patterns

### Recommended Project Structure

```
prismlab/stream-deck-plugin/        ← new top-level directory in monorepo
├── package.json                    ← own Node project, no shared workspace
├── tsconfig.json
├── rollup.config.mjs
├── src/
│   ├── plugin.ts                   ← entry point: register actions, connect()
│   ├── connection.ts               ← singleton WS manager (connect to backend)
│   └── actions/
│       ├── gold-action.ts
│       ├── kda-action.ts
│       ├── clock-action.ts
│       ├── items-action.ts
│       ├── rosh-action.ts
│       └── towers-action.ts
└── com.prismlab.dota2.sdPlugin/    ← compiled output (git-ignored bin/)
    ├── manifest.json
    ├── bin/
    │   └── plugin.js               ← built from src/ via rollup
    ├── imgs/
    │   ├── plugin.png              ← 256×256 plugin icon
    │   ├── plugin@2x.png           ← 512×512
    │   └── actions/
    │       ├── gold/key.png        ← 20×20 (and @2x) per action
    │       └── ...
    ├── ui/
    │   └── pi.html                 ← property inspector: backend URL config
    └── logs/                       ← runtime logs (git-ignored)
```

### Pattern 1: Module-Level WebSocket Connection Manager

The plugin has a single WebSocket connection to the Prismlab backend. Multiple action instances share this connection. The connection lives in `src/connection.ts` as a module-level singleton, started from `plugin.ts` before `streamDeck.connect()` is called.

**What:** A module-level object that opens `ws://host:8420/ws`, applies exponential-backoff reconnect on close, stores the latest `ParsedGsiState` payload in memory, and exposes it for actions to read.

**When to use:** Any time multiple action types need the same upstream data source — avoids N separate WebSocket connections, one per action class.

**Example:**
```typescript
// Source: ws package docs + official Stream Deck SDK docs pattern
import WebSocket from "ws";

interface GsiState {
  hero_name: string;
  hero_level: number;
  gold: number;
  gpm: number;
  net_worth: number;
  kills: number;
  deaths: number;
  assists: number;
  items_inventory: string[];
  items_backpack: string[];
  items_neutral: string;
  game_clock: number;
  game_state: string;
  match_id: string;
  team_side: string;
  is_alive: boolean;
  roshan_state: string;
  radiant_tower_count: number;
  dire_tower_count: number;
  timestamp: number;
}

class BackendConnection {
  private ws: WebSocket | null = null;
  private retryDelay = 1000;
  public state: GsiState | null = null;
  private listeners: Array<(state: GsiState) => void> = [];

  connect(url: string): void {
    this.ws = new WebSocket(url);
    this.ws.on("message", (raw) => {
      try {
        const msg = JSON.parse(raw.toString());
        if (msg.type === "game_state") {
          this.state = msg.data as GsiState;
          this.listeners.forEach((fn) => fn(this.state!));
        }
      } catch { /* ignore malformed */ }
    });
    this.ws.on("close", () => {
      setTimeout(() => {
        this.retryDelay = Math.min(this.retryDelay * 2, 30000);
        this.connect(url);
      }, this.retryDelay);
    });
    this.ws.on("open", () => { this.retryDelay = 1000; });
  }

  onState(fn: (state: GsiState) => void): void {
    this.listeners.push(fn);
  }
}

export const backendConnection = new BackendConnection();
```

### Pattern 2: SingletonAction with `this.actions.forEach()`

Each button type is a `SingletonAction`. When the backend emits a state update, the connection manager calls each action's registered listener. The listener uses `this.actions.forEach()` to push the update to all visible instances of that button simultaneously.

```typescript
// Source: docs.elgato.com/streamdeck/sdk/guides/actions/
import { action, SingletonAction, WillAppearEvent } from "@elgato/streamdeck";
import { backendConnection } from "../connection";

@action({ UUID: "com.prismlab.dota2.gold" })
export class GoldAction extends SingletonAction {
  override onWillAppear(ev: WillAppearEvent): void {
    // Show last known state immediately when button becomes visible
    if (backendConnection.state) {
      this.renderState(backendConnection.state);
    }
  }

  private renderState(state: GsiState): void {
    this.actions.forEach((action) => {
      const svg = buildGoldSvg(state.gold, state.gpm);
      action.setImage(`data:image/svg+xml,${encodeURIComponent(svg)}`);
      action.setTitle(""); // image-only; title cleared
    });
  }
}

// Register in plugin.ts constructor:
const goldAction = new GoldAction();
backendConnection.onState((s) => goldAction["renderState"](s));
```

### Pattern 3: SVG Data URL Button Rendering

Stream Deck XL buttons are 72×72 pixels. SVG is the recommended format (no size constraints, crisp at any DPI, no native dependencies). Encode SVG as a data URL with `encodeURIComponent()`.

```typescript
// Source: docs.elgato.com/streamdeck/sdk/guides/keys/
function buildGoldSvg(gold: number, gpm: number): string {
  const goldStr = gold >= 1000 ? `${(gold / 1000).toFixed(1)}k` : `${gold}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">
    <rect width="72" height="72" fill="#1a1a2e"/>
    <text x="36" y="28" text-anchor="middle" fill="#FFD700"
          font-family="Arial" font-size="22" font-weight="bold">${goldStr}</text>
    <text x="36" y="48" text-anchor="middle" fill="#aaa"
          font-family="Arial" font-size="12">${gpm} GPM</text>
    <text x="36" y="64" text-anchor="middle" fill="#666"
          font-family="Arial" font-size="10">GOLD</text>
  </svg>`;
}
```

### Pattern 4: Property Inspector for Backend URL Configuration

The property inspector (`ui/pi.html`) lets users configure the Prismlab backend WebSocket URL. This handles cases where the backend runs on a different host (Unraid at `ws://100.78.161.13:8420/ws`). Settings are stored as Stream Deck global settings so they persist across plugin restarts.

```typescript
// Plugin side: read global settings at startup
const settings = await streamDeck.settings.getGlobalSettings<{ backendUrl: string }>();
const url = settings.backendUrl ?? "ws://localhost:8420/ws";
backendConnection.connect(url);

// Re-connect when user changes URL in PI:
streamDeck.settings.onDidReceiveGlobalSettings(({ payload }) => {
  backendConnection.reconnect(payload.settings.backendUrl);
});
```

### Pattern 5: manifest.json Structure

```json
{
  "$schema": "https://schemas.elgato.com/streamdeck/plugins/manifest.json",
  "UUID": "com.prismlab.dota2",
  "Name": "Prismlab Dota 2",
  "Author": "Prismlab",
  "Version": "1.0.0.0",
  "Description": "Live Dota 2 game state on your Stream Deck via Prismlab",
  "Category": "Prismlab Dota 2",
  "Icon": "imgs/plugin",
  "SDKVersion": 2,
  "CodePath": "bin/plugin.js",
  "Nodejs": { "version": "20", "debugPort": 9999 },
  "Software": { "MinimumVersion": "6.9" },
  "OS": [{ "Platform": "windows", "MinimumVersion": "10" }],
  "Actions": [
    {
      "UUID": "com.prismlab.dota2.gold",
      "Name": "Gold & GPM",
      "Icon": "imgs/actions/gold/key",
      "Tooltip": "Shows current gold and GPM",
      "Controllers": ["Keypad"],
      "DisableAutomaticStates": true,
      "States": [{ "Image": "imgs/actions/gold/key" }]
    },
    {
      "UUID": "com.prismlab.dota2.kda",
      "Name": "KDA",
      "Icon": "imgs/actions/kda/key",
      "States": [{ "Image": "imgs/actions/kda/key" }]
    },
    {
      "UUID": "com.prismlab.dota2.clock",
      "Name": "Game Clock",
      "Icon": "imgs/actions/clock/key",
      "States": [{ "Image": "imgs/actions/clock/key" }]
    },
    {
      "UUID": "com.prismlab.dota2.items",
      "Name": "Items",
      "Icon": "imgs/actions/items/key",
      "States": [{ "Image": "imgs/actions/items/key" }]
    },
    {
      "UUID": "com.prismlab.dota2.rosh",
      "Name": "Roshan Status",
      "Icon": "imgs/actions/rosh/key",
      "States": [{ "Image": "imgs/actions/rosh/key" }]
    },
    {
      "UUID": "com.prismlab.dota2.towers",
      "Name": "Tower Count",
      "Icon": "imgs/actions/towers/key",
      "States": [{ "Image": "imgs/actions/towers/key" }]
    }
  ]
}
```

### Pattern 6: plugin.ts Entry Point

```typescript
// Source: docs.elgato.com/streamdeck/sdk/introduction/getting-started/
import streamDeck from "@elgato/streamdeck";
import { backendConnection } from "./connection";
import { GoldAction } from "./actions/gold-action";
import { KdaAction } from "./actions/kda-action";
import { ClockAction } from "./actions/clock-action";
import { ItemsAction } from "./actions/items-action";
import { RoshAction } from "./actions/rosh-action";
import { TowersAction } from "./actions/towers-action";

// Instantiate actions BEFORE connect()
const goldAction = new GoldAction();
const kdaAction = new KdaAction();
const clockAction = new ClockAction();
const itemsAction = new ItemsAction();
const roshAction = new RoshAction();
const towersAction = new TowersAction();

// Wire up backend state updates to all actions
backendConnection.onState((state) => {
  goldAction.handleState(state);
  kdaAction.handleState(state);
  clockAction.handleState(state);
  itemsAction.handleState(state);
  roshAction.handleState(state);
  towersAction.handleState(state);
});

// Register actions with SDK
streamDeck.actions.registerAction(goldAction);
streamDeck.actions.registerAction(kdaAction);
streamDeck.actions.registerAction(clockAction);
streamDeck.actions.registerAction(itemsAction);
streamDeck.actions.registerAction(roshAction);
streamDeck.actions.registerAction(towersAction);

// Read backend URL from global settings, then connect
streamDeck.settings.getGlobalSettings<{ backendUrl: string }>().then(({ backendUrl }) => {
  backendConnection.connect(backendUrl ?? "ws://localhost:8420/ws");
});

// Connect plugin to Stream Deck (must be AFTER registerAction calls)
streamDeck.connect();
```

### Anti-Patterns to Avoid

- **Opening one WebSocket per action class:** Each action type opening its own connection to the backend creates 6 parallel connections. Use the module-level singleton instead.
- **Using `canvas` npm package for rendering:** `canvas` requires native C++ bindings (Cairo), adding `node-gyp` build complexity and potential failures on Windows. SVG data URLs are simpler and equivalent for text-heavy HUD data.
- **Calling `streamDeck.connect()` before `registerAction()`:** The SDK requires all actions registered before connecting — incorrect order causes actions to not receive events.
- **Hardcoding `ws://localhost:8420/ws`:** The production backend runs on the Unraid server at `ws://100.78.161.13:8420/ws`. The URL must be user-configurable via global settings.
- **Using `setTitle()` for all content:** For data-dense buttons (items, tower counts), SVG images give much better control over layout. `setTitle()` is fine for single-value buttons (clock) but not multi-field displays.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Plugin-to-Stream Deck IPC | Custom IPC layer | `@elgato/streamdeck` SDK | SDK handles all communication with Stream Deck app via its own internal WebSocket; plugin authors never touch this layer |
| Button image codec | Manual PNG encoding | SVG data URL via `encodeURIComponent` | Native to browsers and Stream Deck's Chromium renderer; zero dependencies; no encoding step needed |
| Plugin scaffolding | Manual file creation | `streamdeck create` CLI | Generates correct `rollup.config.mjs`, `tsconfig.json`, manifest skeleton, and `npm run watch` hot-reload wiring |
| Local dev install | Copy files manually | `streamdeck link com.prismlab.dota2.sdPlugin` | CLI command symlinks the `.sdPlugin` folder into `%APPDATA%\Elgato\StreamDeck\Plugins\` for live testing |
| Plugin packaging | ZIP manually | `streamdeck pack com.prismlab.dota2.sdPlugin` | CLI validates, bundles, and produces `.streamDeckPlugin` installer |

**Key insight:** The Stream Deck SDK abstracts all hardware communication. Plugin authors only implement the logic layer — what to show on buttons and how to respond to presses. The SDK and Stream Deck app handle everything else.

---

## Existing WebSocket Broadcast — What the Plugin Receives

The backend broadcasts at `ws://<host>:8420/ws` (production: `ws://100.78.161.13:8420/ws`).

**Message envelope format:**
```json
{ "type": "game_state", "data": { ...ParsedGsiState fields... } }
```

**All available fields in `data` payload (from `ParsedGsiState`):**

| Field | Type | Description |
|-------|------|-------------|
| `hero_name` | string | Normalized hero name (e.g. `"antimage"`, strips `npc_dota_hero_`) |
| `hero_id` | int | Numeric hero ID |
| `hero_level` | int | Current level (1-30) |
| `has_aghanims_shard` | bool | Aghanim's Shard active |
| `has_aghanims_scepter` | bool | Aghanim's Scepter active |
| `gold` | int | Current gold (reliable + unreliable) |
| `gpm` | int | Gold per minute |
| `net_worth` | int | Net worth |
| `kills` | int | Kill count |
| `deaths` | int | Death count |
| `assists` | int | Assist count |
| `items_inventory` | string[] | 6 slots (empty slots are `""`, names normalized e.g. `"power_treads"`) |
| `items_backpack` | string[] | 3 backpack slots |
| `items_neutral` | string | Neutral item slot (or `""`) |
| `game_clock` | int | Clock time in seconds (can be negative pre-game) |
| `game_state` | string | e.g. `"DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"` |
| `match_id` | string | Numeric match ID as string |
| `team_side` | string | `"radiant"` or `"dire"` |
| `is_alive` | bool | Hero alive status |
| `roshan_state` | string | `"alive"`, `"respawning"`, or `"undefined"` |
| `radiant_tower_count` | int | Alive Radiant towers (max 11) |
| `dire_tower_count` | int | Alive Dire towers (max 11) |
| `timestamp` | float | Unix timestamp of last state update |

**Broadcast characteristics:**
- Throttled at 1 Hz (only emits when state hash has changed from last send)
- No message sent when `is_connected` is false (no Dota 2 running)
- Connection is push-only — the backend never reads messages from clients (plugin can ignore the `receive_text()` keep-alive the backend does)

---

## Common Pitfalls

### Pitfall 1: Stream Deck App Not Running

**What goes wrong:** Plugin process exits immediately; Stream Deck software must be running for the plugin to receive the `-port`, `-pluginUUID`, `-registerEvent`, `-info` CLI arguments it needs to connect.

**Why it happens:** Stream Deck app launches and manages the plugin process. Without the app, the plugin has no target to connect to.

**How to avoid:** Plugin development requires Stream Deck software (v6.9+) installed. During development use `npm run watch` which the CLI hot-reloads through the app.

**Warning signs:** Plugin exits instantly with no log output; check that Stream Deck app is open before starting development.

### Pitfall 2: registerAction After connect()

**What goes wrong:** Actions registered after `streamDeck.connect()` do not receive events — they are silently ignored.

**Why it happens:** The SDK processes the action registry at connect time; late registrations miss the initialization window.

**How to avoid:** Always call `streamDeck.connect()` as the last line of `plugin.ts`, after all `streamDeck.actions.registerAction()` calls.

### Pitfall 3: Backend URL Hardcoded to localhost

**What goes wrong:** Plugin cannot connect to Prismlab running on the Unraid server (`100.78.161.13:8420`).

**Why it happens:** Plugin runs on the local gaming PC; the backend is on the Unraid server.

**How to avoid:** Use `streamDeck.settings.getGlobalSettings()` to read a user-configurable `backendUrl` with a default of `ws://localhost:8420/ws`. Expose this in the property inspector.

### Pitfall 4: canvas Native Module in Stream Deck Plugin

**What goes wrong:** Build fails or plugin crashes because `canvas` requires `node-gyp` and native C++ compilation. The Stream Deck app bundles a specific Node.js version; native addons compiled against the wrong ABI will fail to load.

**Why it happens:** `canvas` (and other native npm packages) link against Node.js internals and must be compiled for the exact Node.js ABI running in the Stream Deck app.

**How to avoid:** Use SVG data URLs exclusively. All button rendering can be accomplished with SVG strings. Avoid any npm package that requires native compilation.

### Pitfall 5: Large SVG Strings Causing Lag

**What goes wrong:** `setImage()` called every second with large SVG strings causes visible lag or dropped updates on the device.

**Why it happens:** The Stream Deck app must decode and render the image; complex SVGs with many elements are slower.

**How to avoid:** Keep SVGs minimal — plain rectangles, 2-3 text elements, no gradients, no filters. Budget target: < 500 bytes per SVG before encoding.

### Pitfall 6: WebSocket CORS Issues

**What goes wrong:** WebSocket connection refused when connecting to the backend.

**Why it happens:** The backend `main.py` CORS middleware allows `http://localhost:5173` and `http://localhost:8421` — but the Stream Deck plugin is a Node.js process, not a browser, so CORS does not apply to WebSocket connections from Node.js. The `ws` package does not send an `Origin` header by default.

**How to avoid:** No action needed — the `ws` package bypasses browser-level CORS. Connection will work directly. If the backend adds WebSocket origin validation in the future, the plugin's origin would need to be whitelisted.

### Pitfall 7: Negative game_clock Before Game Start

**What goes wrong:** Clock display shows `-90` or other negative values during the pre-game draft/loading phase.

**Why it happens:** Dota 2 GSI sends negative `clock_time` before the game officially starts (countdown from -90 to 0).

**How to avoid:** Display pre-game clock as `PRE` or `00:00` when `game_clock < 0`. Format helper:

```typescript
function formatClock(seconds: number): string {
  if (seconds < 0) return "PRE";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
```

---

## Code Examples

Verified patterns from official sources:

### Button Image Update from Background Connection
```typescript
// Source: docs.elgato.com/streamdeck/sdk/guides/keys/
// Inside a SingletonAction subclass
public handleState(state: GsiState): void {
  this.actions.forEach((action) => {
    action.setImage(`data:image/svg+xml,${encodeURIComponent(buildSvg(state))}`);
  });
}
```

### onWillAppear — Restore Current State When Button Becomes Visible
```typescript
// Source: docs.elgato.com/streamdeck/sdk/introduction/your-first-changes/
override onWillAppear(ev: WillAppearEvent): void {
  const current = backendConnection.state;
  if (current) {
    ev.action.setImage(`data:image/svg+xml,${encodeURIComponent(buildSvg(current))}`);
  }
}
```

### Global Settings Read at Startup
```typescript
// Source: docs.elgato.com/streamdeck/sdk/guides/settings/
const { backendUrl } = await streamDeck.settings.getGlobalSettings<{ backendUrl: string }>();
backendConnection.connect(backendUrl ?? "ws://localhost:8420/ws");
```

### Dev Workflow Commands
```bash
# One-time: install CLI globally
npm install -g @elgato/cli

# Scaffold new plugin (run once from prismlab/stream-deck-plugin/)
streamdeck create

# Link to Stream Deck app for testing (run from plugin root)
streamdeck link com.prismlab.dota2.sdPlugin

# Hot-reload dev mode
npm run watch

# Pack for distribution
streamdeck pack com.prismlab.dota2.sdPlugin
```

### Roshan State Rendering Example
```typescript
// roshan_state values: "alive" | "respawning" | "undefined"
function buildRoshSvg(state: GsiState): string {
  const icon = state.roshan_state === "alive" ? "ALIVE"
             : state.roshan_state === "respawning" ? "RESPAWN"
             : "?";
  const color = state.roshan_state === "alive" ? "#ff5555"
              : state.roshan_state === "respawning" ? "#FFD700"
              : "#666";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">
    <rect width="72" height="72" fill="#1a1a2e"/>
    <text x="36" y="38" text-anchor="middle" fill="${color}"
          font-family="Arial" font-size="14" font-weight="bold">${icon}</text>
    <text x="36" y="60" text-anchor="middle" fill="#666"
          font-family="Arial" font-size="10">ROSH</text>
  </svg>`;
}
```

### Tower Count Rendering with Team Context
```typescript
function buildTowersSvg(state: GsiState): string {
  const myTowers = state.team_side === "radiant"
    ? state.radiant_tower_count : state.dire_tower_count;
  const enemyTowers = state.team_side === "radiant"
    ? state.dire_tower_count : state.radiant_tower_count;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72">
    <rect width="72" height="72" fill="#1a1a2e"/>
    <text x="36" y="22" text-anchor="middle" fill="#888"
          font-family="Arial" font-size="10">TOWERS</text>
    <text x="20" y="46" text-anchor="middle" fill="#6aff97"
          font-family="Arial" font-size="22" font-weight="bold">${myTowers}</text>
    <text x="36" y="46" text-anchor="middle" fill="#666"
          font-family="Arial" font-size="16">:</text>
    <text x="52" y="46" text-anchor="middle" fill="#ff5555"
          font-family="Arial" font-size="22" font-weight="bold">${enemyTowers}</text>
    <text x="20" y="62" text-anchor="middle" fill="#6aff97"
          font-family="Arial" font-size="9">MINE</text>
    <text x="52" y="62" text-anchor="middle" fill="#ff5555"
          font-family="Arial" font-size="9">ENEMY</text>
  </svg>`;
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| C/C++ plugins (v1 SDK) | Node.js TypeScript with `@elgato/streamdeck` v2 | SDK v2 launched ~2023 | No more compiled binaries; npm workflow; hot-reload dev |
| Manual WebSocket registration protocol | SDK handles all IPC with Stream Deck app | SDK v2 | Plugin authors never touch Stream Deck's internal WebSocket |
| Per-button canvas rendering with PNG encoding | SVG data URL strings | SDK v2 era best practice | No native dependencies; simpler; lighter |
| One big action with switch-case for all data types | Multiple SingletonAction classes, one per data type | SDK v2 `SingletonAction` pattern | Cleaner; user can mix-and-match only the buttons they want |

**Deprecated/outdated:**
- SDK v1 (`@elgato/streamdeck` before 2.0): Uses different manifest format, different action registration, no `SingletonAction` pattern. All new plugins should use v2.
- `elgato-stream-deck` npm package (hardware-direct): This is a different library for directly controlling Stream Deck via USB without the Stream Deck software. Not applicable here.

---

## Open Questions

1. **Stream Deck app installation on the gaming PC**
   - What we know: The Stream Deck app is required for development and production use. It is not currently installed in this development environment.
   - What's unclear: Whether the user has the Stream Deck app installed on their gaming machine (where Dota 2 runs). The XL hardware presence is implied by the phase description but the app installation is not confirmed.
   - Recommendation: Plan should include a Wave 0 task verifying prerequisites: Stream Deck software installed, Node.js 20+ available, `@elgato/cli` installable. The plan should not assume a working Stream Deck dev environment exists.

2. **Items button — which items to show**
   - What we know: `items_inventory` is a 6-element array. A single 72×72 button cannot meaningfully display 6 items by name with the Dota item naming convention (e.g. `"ultimate_scepter"`, `"power_treads"`).
   - What's unclear: Whether items should show item slugs (abbreviated) or item count only, or if a single "items" button should become multiple buttons.
   - Recommendation: First iteration shows a compact list of non-empty inventory slots as short slugs (first 10 chars) stacked vertically in the SVG. User can expand to multiple buttons if desired.

3. **Item image rendering from Steam CDN**
   - What we know: CLAUDE.md says hero/item images come from Steam CDN. Fetching CDN images in a Stream Deck plugin would require HTTP requests, caching, and canvas/image decoding — significantly more complexity.
   - What's unclear: Whether the user wants item icons or just text names on the items button.
   - Recommendation: Start with text-only SVG labels for items. Item icon support (via HTTP fetch + base64 encode) can be a follow-up — it would require a fetch-and-cache layer and PNG encoding, adding meaningful complexity.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js 20+ | Stream Deck plugin build | Yes | v24.14.0 | — |
| npm | Package install | Yes | 11.9.0 | — |
| `@elgato/cli` (streamdeck) | Scaffold, link, pack | No | — | Manual scaffold from known structure |
| Stream Deck software | Plugin dev/testing | No (not installed on dev machine) | — | No fallback — must be installed on gaming PC to test |
| Prismlab backend WebSocket | Plugin at runtime | Yes (running on Unraid 100.78.161.13:8420) | — | Plugin shows "NO DATA" state when disconnected |
| Python backend (no changes) | — | N/A | — | No changes required |

**Missing dependencies with no fallback:**
- Stream Deck software (v6.9+) must be installed on the gaming PC before the plugin can be tested or linked. It cannot be installed on the dev/build machine unless it is the same machine.

**Missing dependencies with fallback:**
- `@elgato/cli` not globally installed in this dev environment. The plan should include `npm install -g @elgato/cli` as the first task. If the CLI is unavailable, the plugin directory can be structured manually (known structure from docs), but CLI is strongly preferred.

---

## Project Constraints (from CLAUDE.md)

These directives apply to the overall Prismlab project and inform the Stream Deck plugin:

| Directive | Impact on Phase 29 |
|-----------|-------------------|
| No backend changes required | Plugin is a pure WebSocket consumer. `main.py`, `ws_manager.py`, `gsi/` files are read-only for this phase. |
| Hero/item images from Steam CDN, not self-hosted | Plugin should use text labels for items in first iteration. CDN image fetch adds significant complexity. |
| Dark theme: spectral cyan `#00d4ff`, Radiant teal `#6aff97`, Dire red `#ff5555` | Apply these colors to SVG button renders for visual consistency with the web app. |
| TypeScript strict mode, functional style | Plugin TypeScript code should use strict mode and functional patterns where applicable. |
| All code under `prismlab/` subdirectory | Plugin goes in `prismlab/stream-deck-plugin/`, not at repo root. |

---

## Sources

### Primary (HIGH confidence)
- [docs.elgato.com/streamdeck/sdk/introduction/getting-started/](https://docs.elgato.com/streamdeck/sdk/introduction/getting-started/) — Prerequisites, project structure, CLI commands, plugin lifecycle
- [docs.elgato.com/streamdeck/sdk/introduction/plugin-environment/](https://docs.elgato.com/streamdeck/sdk/introduction/plugin-environment/) — Architecture, file structure, runtime versions (Node.js 20.20.0 and 24.13.1 as of Stream Deck 7.3), manifest location
- [docs.elgato.com/streamdeck/sdk/references/manifest/](https://docs.elgato.com/streamdeck/sdk/references/manifest/) — Complete manifest.json schema, all fields, Actions array
- [docs.elgato.com/streamdeck/sdk/guides/keys/](https://docs.elgato.com/streamdeck/sdk/guides/keys/) — setImage with base64/SVG, action methods, event handlers
- [docs.elgato.com/streamdeck/sdk/guides/actions/](https://docs.elgato.com/streamdeck/sdk/guides/actions/) — SingletonAction lifecycle, `this.actions.forEach()`
- [docs.elgato.com/streamdeck/sdk/guides/settings/](https://docs.elgato.com/streamdeck/sdk/guides/settings/) — getGlobalSettings, setGlobalSettings API
- [docs.elgato.com/streamdeck/sdk/introduction/distribution/](https://docs.elgato.com/streamdeck/sdk/introduction/distribution/) — Pack command, .streamDeckPlugin format
- `prismlab/backend/gsi/ws_manager.py` — Confirmed: broadcasts `{"type": "game_state", "data": {...}}` at 1 Hz
- `prismlab/backend/gsi/state_manager.py` — Confirmed: complete `ParsedGsiState` field list
- `prismlab/backend/main.py` — Confirmed: WebSocket endpoint at `/ws`; backend port 8420 in production
- `npm view @elgato/streamdeck version` → 2.0.4 (verified 2026-03-29)
- `npm view @elgato/cli version` → 1.7.3 (verified 2026-03-29)
- `npm view ws version` → 8.20.0 (verified 2026-03-29)

### Secondary (MEDIUM confidence)
- [docs.elgato.com/streamdeck/sdk/introduction/your-first-changes/](https://docs.elgato.com/streamdeck/sdk/introduction/your-first-changes/) — IncrementCounter action pattern with onWillAppear, onKeyDown, setTitle
- [docs.elgato.com/streamdeck/sdk/guides/system/](https://docs.elgato.com/streamdeck/sdk/guides/system/) — systemDidWakeUp event for restoring WebSocket connections
- [mauricebrg.com/2025/06/streamdeck-lambda-trigger.html](https://mauricebrg.com/2025/06/streamdeck-lambda-trigger.html) — Real 2025 plugin example showing project structure and action class patterns
- [github.com/dhd-audio/streamdeck-DHD](https://github.com/dhd-audio/streamdeck-DHD) — Real-world plugin connecting to external API via WebSocket, onWillAppear subscription pattern

### Tertiary (LOW confidence)
- WebSearch: Stream Deck XL 72×72 pixel button resolution — multiple product pages confirm this spec consistently, treating as HIGH confidence in practice

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — npm registry verified, official docs confirmed versions
- Architecture: HIGH — patterns confirmed from official SDK docs + real plugin examples
- Existing WebSocket contract: HIGH — read directly from source code
- Pitfalls: MEDIUM — pitfalls 1-4 from official docs; pitfalls 5-7 from reasoning and community patterns
- Environment availability: HIGH — probed directly with `command -v` and `ls`

**Research date:** 2026-03-29
**Valid until:** 2026-06-01 (SDK v2 is stable; Elgato typically doesn't break plugin contracts without major version bump)
