# Phase 13: Screenshot Parsing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 13-screenshot-parsing
**Areas discussed:** Input method & UX, Confirmation UI, Vision parsing scope, Data integration

---

## Input Method & UX

### How User Provides Screenshot

| Option | Description | Selected |
|--------|-------------|----------|
| Ctrl+V paste anywhere + upload button | Global paste listener + fallback upload/drag-drop | ✓ |
| Dedicated screenshot panel | Must open panel first, then paste inside | |
| Upload button only | No paste listener, file browse only | |

**User's choice:** Ctrl+V paste anywhere + upload button

### UI Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Modal overlay triggered from sidebar | Button near Enemy Items opens modal | ✓ |
| Inline in sidebar | No modal, parsing happens in sidebar | |
| Separate page/tab | Dedicated route for parsing | |

**User's choice:** Modal overlay triggered from sidebar

### Paste Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-open modal on paste | Ctrl+V with image auto-opens modal, starts parsing | ✓ |
| Paste only works inside modal | Must click button first to open modal | |

**User's choice:** Auto-open modal on paste

---

## Confirmation UI

### Display Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Hero rows with item icons | Hero portrait + name + KDA, item icons on right, Steam CDN images | ✓ |
| Simple text list | Plain text, no images | |
| Side-by-side with screenshot | Screenshot left, results right | |

**User's choice:** Hero rows with item icons

### Edit Capability

| Option | Description | Selected |
|--------|-------------|----------|
| Click to remove items, no adding | Can X items but can't add missing ones | |
| Full edit (add + remove) | Can remove wrong items AND add missing ones via search/picker | ✓ |
| No editing, accept or reject | Take all or cancel | |

**User's choice:** Full edit (add + remove)
**Notes:** User wants to correct Vision errors before applying. Both add and remove supported.

---

## Vision Parsing Scope

### Data Categories

| Option | Description | Selected |
|--------|-------------|----------|
| Enemy heroes (names) | Identify all 5 enemy heroes | ✓ |
| Enemy items | 6 inventory slots per hero | ✓ |
| KDA scores | Kill/death/assist counts | ✓ |
| Hero levels | Level per hero | ✓ |

**User's choice:** All four categories
**Notes:** Maximum information extraction from each screenshot.

### Confidence Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Show all, flag low confidence | Display all items, orange border on uncertain ones | ✓ |
| Only show high-confidence | Drop uncertain items entirely | |
| You decide | Claude determines | |

**User's choice:** Show all, flag low confidence
**Notes:** Backend returns confidence per item. Frontend flags low-confidence visually.

### Vision Model

| Option | Description | Selected |
|--------|-------------|----------|
| Same model as recommendation engine | Use Haiku 4.5, single client. Upgrade to Sonnet later if needed. | ✓ |
| Dedicated Sonnet for vision | More capable model for vision. Slower and more expensive. | |
| You decide | Claude picks during implementation | |

**User's choice:** Same model as recommendation engine

---

## Data Integration

### Integration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Replace enemy_items_spotted with full parsed data | Full inventory data replaces manual list. EnemyItemTracker auto-highlights. | ✓ |
| Separate parsed data channel | Keep parsed and manual data separate, merge in backend | |
| You decide | Claude determines | |

**User's choice:** Replace enemy_items_spotted with full parsed data

### Auto-refresh on Apply

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, immediately | Auto-fire recommendation refresh, bypass cooldown | ✓ |
| No, user clicks Re-Evaluate | Only update state, user triggers refresh | |

**User's choice:** Yes, immediately
**Notes:** Bypasses Phase 12 cooldown since it's user-initiated.

### Draft Sync

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, auto-fill opponent slots | Parsed enemy heroes fill all 5 opponent slots | ✓ |
| No, items only | Don't touch draft opponent slots | |

**User's choice:** Yes, auto-fill opponent slots
**Notes:** Gives recommendation engine full enemy team composition context.

---

## Claude's Discretion

- Vision prompt engineering approach
- Image preprocessing (resize, crop, format)
- Item/hero name matching strategy
- Error handling for unparseable screenshots
- Confidence scoring algorithm
- File size limits and image format handling
- Backend endpoint design (base64 vs multipart)

## Deferred Ideas

None — discussion stayed within phase scope.
