# Phase 10: GSI Receiver & WebSocket Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 10-gsi-receiver-websocket-pipeline
**Areas discussed:** GSI config setup, Connection status, GSI port exposure, Data scope & storage

---

## GSI Config Setup

### Q1: How should the user get the GSI config file set up?

| Option | Description | Selected |
|--------|-------------|----------|
| Settings page | A settings/setup page where user enters server IP, app generates .cfg file, click Download. Step-by-step instructions included. | ✓ |
| Header gear icon | Gear icon in header opens small modal with IP input + download | |
| README only | Document .cfg format in docs, user creates manually | |

**User's choice:** Settings page
**Notes:** None

### Q2: Where should the settings/setup page live in the app navigation?

| Option | Description | Selected |
|--------|-------------|----------|
| Gear icon in header | Small gear icon top-right of header bar. Clicking opens settings page/panel. | ✓ |
| Bottom of sidebar | Small Settings link at bottom of sidebar | |
| Separate route | Full /settings page with its own route | |

**User's choice:** Gear icon in header
**Notes:** None

### Q3: What should clicking the gear icon open?

| Option | Description | Selected |
|--------|-------------|----------|
| Slide-over panel | Panel slides in from right, overlaying main content. Easily dismissed. | ✓ |
| Modal dialog | Centered modal with backdrop overlay | |
| Replace main panel | Settings content replaces main panel area | |

**User's choice:** Slide-over panel
**Notes:** None

---

## Connection Status

### Q1: Where should the connection status indicator live in the UI?

| Option | Description | Selected |
|--------|-------------|----------|
| Header bar | Next to data freshness indicator. Colored dot + label. Always visible. | ✓ |
| Top of sidebar | Small status bar above hero picker | |
| Floating corner | Small floating badge in bottom-right corner | |

**User's choice:** Header bar
**Notes:** Three states: green (Connected), gray (Idle), red (Lost)

### Q2: Should the indicator show a tooltip or expand on hover?

| Option | Description | Selected |
|--------|-------------|----------|
| Tooltip on hover | Small tooltip with: last GSI update, game clock, WebSocket status | ✓ |
| Dot only | Just colored dot, no label, no tooltip | |
| Always expanded | Always shows full 'GSI: Connected' label text | |

**User's choice:** Tooltip on hover
**Notes:** None

---

## GSI Port Exposure

### Q1: How should Dota 2's GSI HTTP POST reach the backend container?

| Option | Description | Selected |
|--------|-------------|----------|
| Through Nginx | Add /gsi location block in nginx.conf. GSI config points to port 8421. Single entry point. | ✓ |
| Direct to backend | GSI config points to backend port 8420. No Nginx for GSI. | |
| Separate GSI port | Third port specifically for GSI on backend container | |

**User's choice:** Through Nginx
**Notes:** None

### Q2: WebSocket routing — same approach?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, all through Nginx | Add /ws location with WebSocket upgrade headers. Everything on port 8421. | ✓ |
| WebSocket direct to backend | WebSocket connects to backend port 8420 directly | |

**User's choice:** Yes, all through Nginx
**Notes:** Single-port architecture: /api, /gsi, /ws, and frontend all on 8421

---

## Data Scope & Storage

### Q1: How much GSI data should the backend parse and forward?

| Option | Description | Selected |
|--------|-------------|----------|
| Parse all v2.0 fields now | Extract everything Phases 10-13 need upfront. Store typed model. | ✓ |
| Minimal for Phase 10 only | Only parse game_state and hero_name. Add more each phase. | |
| Forward raw GSI | Push raw JSON to frontend, let frontend parse | |

**User's choice:** Parse all v2.0 fields now
**Notes:** Fields: hero_name, gold, GPM, NW, items, clock, KDA, team_side, game_state

### Q2: How should the backend hold GSI state?

| Option | Description | Selected |
|--------|-------------|----------|
| In-memory only | Python dataclass/dict in memory. No DB. Ephemeral. | ✓ |
| SQLite persistence | Write snapshots to DB for history | |
| Redis/cache layer | Store in Redis with TTL | |

**User's choice:** In-memory only
**Notes:** None

### Q3: How often should the backend push state via WebSocket?

| Option | Description | Selected |
|--------|-------------|----------|
| Throttled to 1/sec | GSI at ~2Hz, push at 1Hz. Reduces re-renders. | ✓ |
| Every GSI update (~2Hz) | Forward every update immediately | |
| On change only | Only push when fields actually change | |

**User's choice:** Throttled to 1/sec
**Notes:** Also only push when parsed fields have changed within the throttle window

---

## Claude's Discretion

- GSI JSON field path mapping
- WebSocket message format
- GSI auth token handling
- Slide-over panel animation
- Throttle implementation
- Frontend WebSocket auto-reconnect strategy

## Deferred Ideas

None — discussion stayed within phase scope
