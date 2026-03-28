# Phase 25: API-Driven Draft Input - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 25-api-draft-input
**Areas discussed:** Data source, Trigger & timing, UI behavior, Steam ID config

---

## Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| OpenDota API | Free, already integrated. Has /players/{id}/recentMatches and /live endpoint. 1-2 min delay. | |
| Stratz GraphQL | Real-time live match data via GraphQL subscriptions. Faster. Requires token. | |
| Both with fallback | Try Stratz first, fall back to OpenDota. More resilient. | ✓ |
| GSI + OpenDota hybrid | Use GSI for your hero, OpenDota to look up rest. | |

**User's choice:** Both with fallback — Stratz primary for speed, OpenDota fallback for resilience.

---

## Trigger & Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Auto on GSI connect | As soon as GSI detects a game, auto-fetch. Poll during pick phase. | |
| Manual button press | User clicks "Fetch Draft" when ready. | |
| Auto + manual override | Auto-fetch on GSI connect, plus refresh button for corrections. | ✓ |

**User's choice:** Auto + manual override — auto-fetch on game detection, manual refresh available.

---

## UI Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-fill silently | Heroes populate automatically. No confirmation. | |
| Auto-fill with toast | Populate + toast notification. | |
| Confirmation dialog | Modal asking user to confirm before applying. | |

**User's choice:** Auto-fill with manual override ability. No confirmation needed, but existing pickers remain functional for corrections.

---

## Steam ID Config

| Option | Description | Selected |
|--------|-------------|----------|
| Settings panel | Steam ID field in Settings. Saves to localStorage. | ✓ |
| .env only | Backend environment variable. Single user only. | |
| Auto-detect from GSI | Extract steamid from GSI payload automatically. | |

**User's choice:** Settings panel — UI-configurable, pre-filled from .env default.

---

## Claude's Discretion

- Error handling and retry logic
- Stratz GraphQL query structure
- Polling intervals
- Lane assignment inference

## Deferred Ideas

None
