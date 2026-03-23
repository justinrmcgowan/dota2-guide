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

## Current Milestone: v2.0 Live Game Intelligence

**Goal:** Transform Prismlab from manual-input advisor to live-game-aware system using Dota 2 GSI, screenshot parsing, and auto gold tracking — recommendations evolve in real-time as the game progresses.

**Target features:**
- GSI integration — FastAPI endpoint receives live game state, pushes to frontend via WebSocket
- Auto-detect draft, lane, gold/net worth, purchased items from GSI data
- Auto-determine lane result from gold data at 10 min, adjust item timings
- Screenshot parsing — user pastes scoreboard screenshot, Claude vision extracts enemy items
- Auto-refresh recommendations on key game events (rate-limited, max 1 per 2 min)
- Full automation pipeline: GSI real-time data + screenshots for enemy builds

### Out of Scope

- Mobile optimization — desktop-first
- Voice coaching / audio callouts — text-only for v2.0
- Hotkey screen capture / clipboard monitoring — manual paste only for v2.0
- Ability build suggestions — item-focused only

## Context

- **Shipped:** v1.0 MVP (2026-03-21), v1.1 Allied Synergy & Neutral Items (2026-03-23)
- **Codebase:** ~1000 source files, React 19 + Vite 8 + Tailwind v4 frontend, Python 3.13 + FastAPI backend
- **Test suite:** 141 tests (96 backend pytest + 45 frontend vitest), zero failures
- **Player profile:** Aggressive playstyle — seeks fights, wants items enabling that tendency
- **Core problem:** Player knows Dota itemization theory but loses track of matchup nuances during live games
- **Data sources:** OpenDota API for hero stats, win rates, item popularity. Steam CDN for images
- **Known tech debt:** None critical — allies now wired through context builder and system prompt, admin proxy fixed, dead code removed in v1.1 Phase 7

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
| Prompt-only ally coordination | Aura dedup, combo awareness, gap filling via system prompt rules rather than deterministic rules engine | ✓ Good — keeps flexibility, system prompt grew to 13326 chars (well above caching threshold) |
| OpenDota item popularity for ally builds | Reuse existing data pipeline for ally item context | ✓ Good — no new API calls needed, same get_hero_item_popularity function |
| Neutral items via system prompt, not rules engine | Claude ranks neutrals per tier with per-item reasoning and build-path callouts | ✓ Good — dedicated section below timeline, all 5 tiers visible, 2-3 picks per tier |
| Send all neutrals to Claude, not pre-filtered | Claude catches non-obvious synergies that attribute-based filtering would miss | ✓ Good — ~500 tokens for full neutral catalog, manageable |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-23 — v2.0 Live Game Intelligence milestone started*
