# Phase 12: Auto-Refresh & Lane Detection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 12-auto-refresh-lane-detection
**Areas discussed:** Auto-refresh triggers & detection, Rate limiting & cooldown, Lane result auto-detection, Notification toasts

---

## Auto-refresh Triggers & Detection

### Event Types

| Option | Description | Selected |
|--------|-------------|----------|
| Item purchase | New completed item appears in GSI inventory | |
| Player death | Deaths counter increases | ✓ |
| Major gold swing (>2000g) | Net worth changes by >2000g since last recommendation | ✓ |
| Game phase transition | Clock crosses 10/20/35 min thresholds | ✓ |

**User's choice:** Player death, Major gold swing, Game phase transition — but NOT item purchase
**Notes:** Buying items doesn't change what to buy next — recommendation already knew the plan.

### Tower/Roshan Detection

| Option | Description | Selected |
|--------|-------------|----------|
| No — gold swing covers it | Economic impact shows up in gold swing trigger | |
| Yes, detect explicitly | Track tower/Roshan state from GSI map data | ✓ |

**User's choice:** Yes, detect explicitly

### Tower Kill Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Any tower kill | Both teams' towers are meaningful for itemization | ✓ |
| Only your team's tower kills | Only when your team takes an enemy tower | |

**User's choice:** Any tower kill
**Notes:** Losing towers = defensive urgency. Taking towers = aggressive opportunity.

### Gold Swing Threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed at 2000g | Matches REQUIREMENTS.md spec. No settings UI needed. | ✓ |
| Configurable via settings | Slider in settings panel for power users | |

**User's choice:** Fixed at 2000g

### Game Phase Thresholds

| Option | Description | Selected |
|--------|-------------|----------|
| 10 min + 20 min + 35 min | Three natural Dota breakpoints | ✓ |
| 10 min only | Minimal — gold swings cover the rest | |
| You decide | Claude picks thresholds | |

**User's choice:** 10 min + 20 min + 35 min

---

## Rate Limiting & Cooldown

### Cooldown Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Queue latest, fire when cooldown expires | Keep most recent trigger queued, fire when cooldown expires | ✓ |
| Drop events during cooldown | Silently ignore events during cooldown | |
| Accumulate all events | Collect all events, fire combined when cooldown expires | |

**User's choice:** Queue latest, fire when cooldown expires
**Notes:** Multiple events during cooldown → last one replaces previous (most recent context most relevant).

### Cooldown UI

| Option | Description | Selected |
|--------|-------------|----------|
| Subtle cooldown timer on Re-Evaluate button | Dim "auto in 1:23" text below button | ✓ |
| No cooldown indicator | Invisible cooldown | |
| You decide | Claude determines | |

**User's choice:** Subtle cooldown timer on Re-Evaluate button

### Manual vs Auto Cooldown

| Option | Description | Selected |
|--------|-------------|----------|
| Manual bypasses, resets cooldown | Manual click always fires, resets 2-min timer | ✓ |
| Separate timers | Manual and auto independent | |

**User's choice:** Manual bypasses, resets cooldown

---

## Lane Result Auto-Detection

### Benchmark Source

| Option | Description | Selected |
|--------|-------------|----------|
| Role-based static benchmarks | Hardcoded GPM targets per role. Won/Even/Lost from ±10% bands. | ✓ |
| Hero-specific from OpenDota | Per-hero average GPM lookup. More accurate but needs data pipeline. | |
| You decide | Claude determines during research | |

**User's choice:** Role-based static benchmarks
**Notes:** Pos 1: ~500, Pos 2: ~480, Pos 3: ~400, Pos 4: ~280, Pos 5: ~230.

### User Involvement

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-set with override | Auto-sets at 10:00, shows "auto-detected" label, user can override | ✓ |
| Show suggestion, require confirm | Prompt user to confirm before setting | |

**User's choice:** Auto-set with override
**Notes:** Override persists — GSI does not re-detect after user manually changes.

---

## Notification Toasts

### Toast Design

| Option | Description | Selected |
|--------|-------------|----------|
| Bottom-right, compact with icon | Lightning bolt icon, trigger reason, auto-dismiss 4s | ✓ |
| Top-center banner | Full-width banner below header | |
| Inline in item timeline | Subtle message at top of timeline | |

**User's choice:** Bottom-right, compact with icon

### Multi-Event Toast Content

| Option | Description | Selected |
|--------|-------------|----------|
| Only the final trigger | Show most recent event reason only | ✓ |
| Combined summary | List all accumulated events | |

**User's choice:** Only the final trigger

---

## Claude's Discretion

- Toast component implementation approach
- GSI state diff detection implementation
- Tower/Roshan detection from GSI map fields
- Cooldown timer implementation
- Edge cases (disconnects, game end, reconnect)

## Deferred Ideas

None — discussion stayed within phase scope.
