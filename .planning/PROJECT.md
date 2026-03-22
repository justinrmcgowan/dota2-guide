# Prismlab

## What This Is

Prismlab is a Dota 2 adaptive item advisor that helps players make better itemization decisions by analyzing the full 10-hero draft, their personal playstyle, lane matchup, and evolving game state. It generates phased item timelines with analytical reasoning — not just what to buy, but why, backed by data and matchup logic. Built as a web app with React 19 frontend and FastAPI backend, deployed via Docker Compose.

## Core Value

At any point in any game, the player knows exactly what to buy next and why — they never feel lost on itemization.

## Requirements

### Validated

- ✓ Searchable hero picker for all 10 draft positions — v1.0
- ✓ Role/position selection (Pos 1-5) with role-dependent playstyle options — v1.0
- ✓ Radiant/Dire side and lane assignment selection — v1.0
- ✓ Hybrid recommendation engine (12 deterministic rules + Claude Sonnet 4.6) — v1.0
- ✓ Structured JSON output from Claude API, validated against Pydantic schema — v1.0
- ✓ Fallback to rules-only mode with visible notice on Claude API failure/timeout — v1.0
- ✓ Phased item timeline (starting → laning → core → late game) with per-item reasoning — v1.0
- ✓ Situational decision tree cards for conditional item choices — v1.0
- ✓ Click-to-mark purchased items with green checkmark overlay — v1.0
- ✓ Mid-game adaptation: lane result, damage profile, enemy items spotted — v1.0
- ✓ Re-evaluate regenerates only unpurchased remaining items — v1.0
- ✓ Docker Compose deployment (backend 8420, frontend 8421) with Nginx reverse proxy — v1.0
- ✓ Daily data refresh pipeline via APScheduler with freshness indicator — v1.0
- ✓ Dark theme with spectral cyan accent, Radiant teal, Dire red — v1.0

### Active

## Current Milestone: v1.1 Allied Synergy & Neutral Items

**Goal:** Leverage the full 10-hero draft by wiring allied heroes into Claude reasoning, add neutral item recommendations, and clean up v1.0 tech debt.

**Target features:**
- Allied team synergy in recommendations (duplication avoidance, combo awareness, role gap filling)
- Neutral item tier priorities with dedicated section and inline build-path callouts
- Dead code removal, admin proxy fix, test coverage gaps, general UI polish

### Out of Scope

- Allied team hero deep synergy analysis — V1 accepts allies in draft but doesn't factor them into Claude reasoning (V2)
- Neutral item recommendations — V2
- GSI/live game data auto-integration — V2
- Screenshot/scoreboard parsing — V2
- Mobile optimization — desktop-first
- Auto gold/net worth tracking — V2

## Context

- **Shipped:** v1.0 MVP on 2026-03-21
- **Codebase:** ~1000 source files, React 19 + Vite 8 + Tailwind v4 frontend, Python 3.13 + FastAPI backend
- **Test suite:** 82 tests (56 backend pytest + 26 frontend vitest), zero failures
- **Player profile:** Aggressive playstyle — seeks fights, wants items enabling that tendency
- **Core problem:** Player knows Dota itemization theory but loses track of matchup nuances during live games
- **Data sources:** OpenDota API for hero stats, win rates, item popularity. Steam CDN for images
- **Known tech debt:** allies field accepted but unused in context builder (by V1 design), admin endpoint not proxied, unused frontend item API methods

## Constraints

- **Tech stack:** React 19 + Vite 8 + TypeScript + Tailwind v4 + Zustand (frontend), Python 3.13 + FastAPI + SQLAlchemy + SQLite (backend), Claude Sonnet 4.6 (reasoning engine)
- **Deployment:** Docker Compose on Unraid — backend port 8420, frontend port 8421
- **API dependency:** Claude API with 10s hard timeout and rules-only fallback
- **Image hosting:** Hero/item images from Steam CDN, never self-hosted
- **Theme:** Dark theme (#0f1419 bg) with spectral cyan (#00d4ff), Radiant teal (#6aff97), Dire red (#ff5555)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full 10-hero draft in V1 | User says team composition affects itemization significantly | ✓ Good — draft inputs all wired, allies accepted for future use |
| Analytical voice over coach voice | User prefers data-driven reasoning (stats, percentages) | ✓ Good — system prompt tuned for analytical output |
| Toggles + manual entry for mid-game input | Quick enough to use during a live game | ✓ Good — preset toggles + fine-tune sliders working |
| Click-to-mark purchased items | Simplest interaction during live gameplay | ✓ Good — green checkmark overlay, dimmed, stays in position |
| Progressive information layers | Matches how information naturally reveals during a Dota game | ✓ Good — GameStatePanel appears after first recommendation |
| Hybrid search (substring + initials + Fuse.js) | Pure Fuse.js too strict for abbreviations like "am" → "Anti-Mage" | ✓ Good — all fuzzy patterns match correctly |
| Separate recommendationStore from gameStore | Decouple draft state from recommendation state | ✓ Good — clean separation, clearResults preserves purchased |
| APScheduler for daily refresh | Native async job support in FastAPI event loop | ✓ Good — 24h interval, clean shutdown |

---
*Last updated: 2026-03-22 after v1.1 milestone start*
