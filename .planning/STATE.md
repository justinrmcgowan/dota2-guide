---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Allied Synergy & Neutral Items
status: defining_requirements
stopped_at: null
last_updated: "2026-03-22T08:30:00.000Z"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-22)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Defining requirements for v1.1

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-03-22 — Milestone v1.1 started

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.0]: Allies already accepted in draft UI and sent to backend — context builder just doesn't use them yet
- [v1.0]: 12 deterministic rules covering spell-spammers, evasion, magic damage, passives, invisibility, regen, mana sustain, armor, and role-based boots
- [v1.0]: System prompt at 9610 chars with specificity constraints requiring enemy hero names and ability references
- [v1.0]: output_config.format with json_schema (GA path) for Claude structured output, max_retries=0 within 10s timeout
- [v1.0]: Role-based item budget filtering: 10000g for cores (Pos 1-3), 5500g for supports (Pos 4-5)
- [v1.0]: Purchased item filtering runs before item ID validation to avoid unnecessary DB lookups
- [v1.0]: Known tech debt: unused frontend item API methods, admin endpoint not proxied, allies field unused in context builder

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-22
Stopped at: Milestone v1.1 initialization
Resume file: None
