# Prismlab

## What This Is

Prismlab is a Dota 2 adaptive item advisor that helps players make better itemization decisions by analyzing the full 10-hero draft, their personal playstyle, lane matchup, and evolving game state. It generates phased item timelines with analytical reasoning — not just what to buy, but why, backed by data and matchup logic.

## Core Value

At any point in any game, the player knows exactly what to buy next and why — they never feel lost on itemization.

## Requirements

### Validated

- ✓ Searchable hero picker (your hero slot) — Phase 1
- ✓ Dark theme with spectral cyan accent, Radiant/Dire colors — Phase 1
- ✓ Docker Compose deployment (backend 8420, frontend 8421) — Phase 1
- ✓ Environment configuration via .env — Phase 1

### Active

- [ ] Searchable hero picker for all draft positions (4 allies, 5 opponents — your hero done)
- [ ] Role/position selection (Pos 1-5)
- [ ] Playstyle selection reflecting personal tendencies (aggressive/passive, fight-seeking, greedy, etc.)
- [ ] Radiant/Dire side selection
- [ ] Lane assignment selection
- [ ] Phased item timeline output (starting → laning → core → late game)
- [ ] Analytical reasoning per item recommendation (stats-driven, matchup-specific)
- [ ] Full 10-hero draft influences item recommendations
- [ ] Lane opponent selection once game begins (progressive info layer)
- [ ] Mid-game damage profile input via toggles and manual entry
- [ ] Click-to-mark items as purchased in the timeline
- [ ] Re-evaluate button regenerates only remaining (unpurchased) items
- [ ] Hybrid recommendation engine: rules for obvious decisions, Claude API for nuanced reasoning
- [ ] Structured JSON output from Claude API, validated before rendering
- [ ] Fallback behavior when Claude API fails or times out

### Out of Scope

- Allied team heroes influencing recommendations beyond draft awareness — V1 considers them for draft context but deep synergy analysis is V2
- Neutral item recommendations — V2
- GSI/live game data auto-integration — V2 (V1 uses manual click-to-mark and manual input)
- Screenshot/scoreboard parsing for mid-game data — V2 (V1 uses toggles and manual entry)
- Mobile optimization — desktop-first, don't break on mobile but don't optimize
- Auto gold/net worth tracking — V2

## Context

- **Player profile:** Aggressive playstyle — seeks fights, willing to take on multiple opponents, wants items that enable that tendency rather than "theoretically optimal" passive builds
- **Core problem:** Player knows Dota itemization theory but loses track of matchup nuances during live games. This is a memory/decision-support tool, not a learning tool
- **Success looks like:** Player internalizes reasoning over time but always has the tool as a reliable fallback
- **Data sources:** OpenDota API and Stratz API for hero stats, win rates, item popularity. Steam CDN for hero/item images
- **Progressive information flow:** Draft phase (all 10 heroes, role, playstyle, side, lane) → Laning phase (lane opponents confirmed) → Mid-game (damage profiles, items purchased, game state updates) → Late game (re-evaluations with full context)
- **Re-evaluation model:** Past purchases are locked. Re-evaluate only regenerates the remaining item timeline forward from current state
- **Item tracking:** Click on item in timeline to mark as purchased (V1). Future: auto-detect via GSI

## Constraints

- **Tech stack:** React 18 + Vite + TypeScript + Tailwind CSS + Zustand (frontend), Python 3.12 + FastAPI + SQLAlchemy + SQLite (backend), Claude API Sonnet (reasoning engine)
- **Deployment:** Docker Compose on Unraid — backend port 8420, frontend port 8421, reverse-proxied via Cloudflare Tunnel or Nginx Proxy Manager
- **API dependency:** Claude API required for reasoning — must have graceful fallback to rules-only mode
- **Image hosting:** Hero/item images from Steam CDN, never self-hosted
- **Theme:** Dark theme with spectral cyan (#00d4ff) primary, Radiant teal (#6aff97), Dire red (#ff5555)
- **Layout:** Desktop-first — left sidebar for inputs, right main panel for item timeline

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full 10-hero draft in V1 | User says team composition affects itemization significantly even for lane phase | — Pending |
| Analytical voice over coach voice | User prefers data-driven reasoning (stats, percentages) over personality-driven advice | — Pending |
| Toggles + manual entry for mid-game input | Quick enough to use during a live game; screenshot parsing deferred to V2 | — Pending |
| Click-to-mark purchased items | Simplest interaction during live gameplay; auto-detect via GSI is V2 | — Pending |
| Progressive information layers | Matches how information naturally reveals during a Dota game | — Pending |

---
*Last updated: 2026-03-21 after Phase 1 completion*
