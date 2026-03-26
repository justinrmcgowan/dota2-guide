# Phase 11: Live Game Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 11-live-game-dashboard
**Areas discussed:** Auto-detect & store sync, Live gold & stats display, Auto-mark purchased items, Game clock & neutral tiers

---

## Auto-detect & Store Sync

### Hero Detection Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-fill silently | GSI hero auto-populates picker without prompting. User can override. | ✓ |
| Auto-fill with toast | Same auto-fill but shows notification "GSI detected: Anti-Mage (Pos 1)" | |
| Confirm before filling | Prompt user to confirm detected hero before applying | |

**User's choice:** Auto-fill silently
**Notes:** Least friction during a live game — no toast, no confirmation needed.

### Manual Control Conflict Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| GSI wins, manual stays editable | GSI overwrites auto-detected fields. User can edit but next update overwrites. | ✓ |
| GSI fills empty, never overwrites | GSI only populates null/empty fields. Respects manual work. | |
| Dual-mode toggle | Explicit Manual/GSI toggle in sidebar | |

**User's choice:** GSI wins, manual stays editable
**Notes:** Simple mental model — GSI is source of truth while connected. Priority chain: GSI connected → GSI wins, disconnected → last values persist, no GSI → fully manual.

### Role Inference

| Option | Description | Selected |
|--------|-------------|----------|
| Most common role from OpenDota data | Look up hero's most-played position, pre-select that role | ✓ |
| Don't auto-suggest role | GSI fills hero only, user always picks role manually | |

**User's choice:** Most common role from OpenDota data
**Notes:** Fallback if no data: leave role unselected.

---

## Live Gold & Stats Display

### Stats Placement

| Option | Description | Selected |
|--------|-------------|----------|
| New stats bar above GameStatePanel | Compact bar with Gold, GPM, Net Worth + KDA above existing controls | ✓ |
| Replace lane result section | Hide lane result selector, replace with gold/GPM display | |
| Overlay on existing sidebar | Small badges on hero section | |

**User's choice:** New stats bar above GameStatePanel
**Notes:** Groups live data together. Existing manual controls remain below.

### KDA Display

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, alongside gold stats | Show K/D/A in the stats bar for game state context | ✓ |
| No, keep it minimal | Only gold/GPM/net worth | |

**User's choice:** Yes, alongside gold stats

### Animation Style

| Option | Description | Selected |
|--------|-------------|----------|
| Counting animation | Smooth interpolation over ~300ms, color flash on big changes | ✓ |
| Instant update | Numbers snap to new values immediately | |
| You decide | Claude picks the approach | |

**User's choice:** Counting animation
**Notes:** Green pulse on large gold gains (+300g), red pulse on death.

---

## Auto-mark Purchased Items

### Visual Treatment

| Option | Description | Selected |
|--------|-------------|----------|
| Same green checkmark, auto-applied | Reuse existing click-to-mark visual, applied automatically from GSI | ✓ |
| Different visual for auto-detected | Distinct indicator (cyan checkmark or GSI badge) | |
| You decide | Claude determines best visual | |

**User's choice:** Same green checkmark, auto-applied
**Notes:** Consistent visual — no need to differentiate manual vs auto-detected.

### Manual Unmark Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, click toggles always | Manual click toggles; GSI re-marks on next update if item still in inventory | ✓ |
| GSI marks are locked | Auto-detected purchases can't be manually toggled | |

**User's choice:** Yes, click toggles always
**Notes:** GSI effectively overrides since it sends updates every 1s.

### Component Item Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Only mark completed items | No partial progress. Item marked only when full item in inventory. | ✓ |
| Show component progress | Progress indicator (2/3 components) on partial builds | |
| You decide | Claude determines during implementation | |

**User's choice:** Only mark completed items
**Notes:** Simple and unambiguous — you either have the item or you don't.

---

## Game Clock & Neutral Tiers

### Clock Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Header bar, next to GSI indicator | Between GSI dot and data freshness. MM:SS format. Hidden when not in-game. | ✓ |
| Top of stats bar in sidebar | Groups with other live game data | |
| You decide | Claude picks best placement | |

**User's choice:** Header bar, next to GSI indicator

### Neutral Tier Connection

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-highlight current tier | NeutralItemSection highlights active tier, shows countdown to next | ✓ |
| Static display, no clock tie-in | Clock shown independently, no programmatic tier connection | |

**User's choice:** Auto-highlight current tier
**Notes:** Standard Dota 2 tier timings: 7:00, 17:00, 27:00, 37:00, 60:00.

---

## Claude's Discretion

- Counting animation implementation approach
- GSI item name → DB item name matching strategy
- Stats bar layout/spacing details
- Game clock formatting for edge cases (pre-horn, paused)
- gsiStore → gameStore sync mechanism
- WebSocket message parsing/validation

## Deferred Ideas

None — discussion stayed within phase scope.
