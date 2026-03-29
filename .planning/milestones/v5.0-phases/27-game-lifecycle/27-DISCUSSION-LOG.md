# Phase 27: Game Lifecycle Management - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 27-game-lifecycle
**Areas discussed:** State persistence, New game detection, Reset behavior, Abandon handling

---

## State Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| localStorage | Browser storage, survives refreshes. Simple. | |
| Backend session DB | SQLite via API. Survives browser changes. | |
| localStorage + backend sync | Both for speed + durability | ✓ |

**User's choice:** localStorage primary with backend sync for durability.

---

## New Game Detection

| Option | Description | Selected |
|--------|-------------|----------|
| Match ID change | GSI map.matchid changes. Most reliable. | |
| Hero ID change | Different hero_id. Fails on same hero picks. | |
| Game state transition | POST_GAME → HERO_SELECTION sequence. | |
| Match ID + game state combo | Both signals for reliability. | ✓ |

**User's choice:** Match ID primary + game state secondary. Belt and suspenders.

---

## Reset Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Full match reset | Clear all match state, keep settings. | ✓ |
| Selective reset | Keep hero/role, clear opponents/purchased. | |
| Full wipe | Clear everything including settings. | |

**User's choice:** Full match reset — clear hero, role, opponents, purchased, recommendations. Keep settings.

---

## Abandon Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Preserve + 10min timeout | Keep state, auto-clear after 10min disconnect. | ✓ |
| Preserve indefinitely | Never auto-clear. Risk stale state. | |
| Immediate clear | Disconnect = clear immediately. Risk losing state on blips. | |

**User's choice:** Preserve for 10 minutes with "Reconnecting..." indicator, then auto-clear.

---

## Claude's Discretion

- localStorage serialization format
- Backend sync endpoint design
- Match ID tracking implementation
- Reconnection indicator UI
- Multi-tab edge cases

## Deferred Ideas

None
