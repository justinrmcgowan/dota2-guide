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
- ✓ Hybrid recommendation engine (18 deterministic rules + Claude Haiku 4.5) — v1.0, expanded v2.0
- ✓ Structured JSON output from Claude API, validated against Pydantic schema — v1.0
- ✓ Fallback to rules-only mode with visible notice and reason-specific messages — v1.0, enhanced v2.0
- ✓ Phased item timeline (starting → laning → core → late game) with per-item reasoning — v1.0
- ✓ Situational decision tree cards for conditional item choices — v1.0
- ✓ Click-to-mark purchased items with green checkmark overlay — v1.0
- ✓ Mid-game adaptation: lane result, damage profile, enemy items spotted — v1.0
- ✓ Re-evaluate regenerates only unpurchased remaining items — v1.0
- ✓ Docker Compose deployment (backend 8420, frontend 8421) with Nginx reverse proxy — v1.0
- ✓ Daily data refresh pipeline via APScheduler with freshness indicator — v1.0
- ✓ Dark theme with spectral cyan accent, Radiant teal, Dire red — v1.0
- ✓ GSI integration with real-time game state via WebSocket — v2.0
- ✓ Auto-detect hero, role, gold, items, game clock from GSI — v2.0
- ✓ Auto-refresh recommendations on game events (death, tower, Roshan, gold swing, phase transitions) — v2.0
- ✓ Lane result auto-detected from GPM at 10 min — v2.0
- ✓ Screenshot parsing via Claude Vision with confirmation UI — v2.0
- ✓ Per-IP rate limiter, response cache, damage profile validation, playstyle-role validation — v2.0

### Active

## Current Milestone: v4.0 Coaching Intelligence

**Goal:** Transform Prismlab from an item list generator into a strategic coach — with data-backed timing windows, ability-aware counter-itemization, build path ordering, and win condition framing.

**Target features:**
- Timing benchmarks — mine OpenDota purchase-timing data, surface urgency signals, integrate into rules + prompt
- Counter-item depth — ability-specific counters beyond current rules (Eul's vs channeled ults, Spirit Vessel vs regen heroes), driven by hero ability data
- Build path intelligence — component-level ordering, not just final item recommendations
- Win condition framing — classify team compositions into macro strategies, frame item builds around how the game is won

### Out of Scope

- Mobile optimization — desktop-first
- Voice coaching / audio callouts — text-only
- Hotkey screen capture / clipboard monitoring — manual paste only
- Ability build suggestions — item-focused only

## Context

- **Shipped:** v1.0 MVP (2026-03-21), v1.1 Allied Synergy & Neutral Items (2026-03-23), v2.0 Live Game Intelligence (2026-03-26), v3.0 Design Overhaul & Performance (2026-03-27)
- **Codebase:** React 19 + Vite 8 + Tailwind v4 frontend, Python 3.13 + FastAPI backend
- **Test suite:** 160+ tests (backend pytest + frontend vitest), zero failures
- **Player profile:** Aggressive playstyle — seeks fights, wants items enabling that tendency
- **Core problem:** Player knows Dota itemization theory but loses track of matchup nuances during live games
- **Data sources:** OpenDota API for hero stats, win rates, item popularity. Steam CDN for images. Dota 2 GSI for live game state.
- **Design system:** "Tactical Relic Editorial" — obsidian surfaces, Newsreader + Manrope typography, crimson/gold palette (see DESIGN.md)

## Constraints

- **Tech stack:** React 19 + Vite 8 + TypeScript + Tailwind v4 + Zustand (frontend), Python 3.13 + FastAPI + SQLAlchemy + SQLite (backend), Claude Sonnet 4.6 (reasoning engine)
- **Deployment:** Docker Compose on Unraid — backend port 8420, frontend port 8421
- **API dependency:** Claude API with 10s hard timeout and rules-only fallback
- **Image hosting:** Hero/item images from Steam CDN, never self-hosted
- **Theme:** Transitioning to "Tactical Relic Editorial" design system (see DESIGN.md) — obsidian (#131313), crimson (#B22222), gold (#FFDB3C)
- **Design spec:** `DESIGN.md` at repo root is canonical for all frontend work in v3.0+

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
*Last updated: 2026-03-27 — v4.0 Coaching Intelligence milestone started*
