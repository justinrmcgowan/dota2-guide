# Phase 9: Neutral Items - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 09-neutral-items
**Areas discussed:** Neutral item section placement, Tier presentation strategy, Build-path interaction callouts, Data scope and filtering

---

## Neutral Item Section Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Separate section below timeline | Dedicated card below main phases, clean separation of purchasable vs drop items | Y |
| Inline within phase cards | Add neutral picks inside each PhaseCard | |
| Both — section + inline callouts | Dedicated section AND one-liners in PhaseCards | |

**User's choice:** Separate section below timeline
**Notes:** Clean separation matches how Dota treats neutrals (drops, not purchases)

---

### Per-Tier Count

| Option | Description | Selected |
|--------|-------------|----------|
| Top 2-3 ranked picks per tier | Enough for prioritization with fallbacks | Y |
| Top 1 best pick per tier | Minimal and decisive | |
| All viable picks (3-5) per tier | Comprehensive but noisy | |

**User's choice:** Top 2-3 ranked picks per tier

---

## Tier Presentation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| All 5 tiers always visible | Full picture upfront, consistent with showing all phase cards | Y |
| Progressive reveal by game time | Show tiers as game advances | |
| Only current + next tier | Minimal display | |

**User's choice:** All 5 tiers always visible

---

### Reasoning Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Short reasoning per item | 1-sentence per neutral, tied to hero/matchup | Y |
| Reasoning per tier, not per item | One explanation for the whole tier | |
| Names only, no reasoning | Minimal token cost but breaks core promise | |

**User's choice:** Short reasoning per item

---

## Build-Path Interaction Callouts

| Option | Description | Selected |
|--------|-------------|----------|
| In neutral item's reasoning text | Build-path impact mentioned in the reasoning field | Y |
| Separate 'Build Impact' badge | Visual indicator on affected purchasable items | |
| Both — reasoning + badge | Maximum visibility, more complex | |

**User's choice:** In the neutral item's reasoning text

---

## Data Scope and Filtering

| Option | Description | Selected |
|--------|-------------|----------|
| All neutrals per tier, Claude picks | Send full ~60 items, Claude ranks best 2-3 | Y |
| Pre-filter by hero attribute/role | Backend filters before sending | |
| Send only item names, not effects | Rely on Claude's training knowledge | |

**User's choice:** All neutrals per tier, Claude picks

---

### Re-Evaluate Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, re-evaluate updates neutrals | Consistent — Re-Evaluate refreshes everything | Y |
| No, neutrals stay fixed | Simpler but less adaptive | |

**User's choice:** Yes, re-evaluate updates neutrals too

---

## Claude's Discretion

- Exact wording of neutral item reasoning
- Whether to mention tier timing in headers
- Handling tiers with no strong preference

## Deferred Ideas

None
