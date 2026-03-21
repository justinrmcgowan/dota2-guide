# Requirements: Prismlab

**Defined:** 2026-03-21
**Core Value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Draft Inputs

- [x] **DRFT-01**: User can search and select their hero from a searchable dropdown with hero portraits
- [x] **DRFT-02**: User can search and select 4 allied heroes from searchable dropdowns with portraits
- [x] **DRFT-03**: User can search and select 5 opponent heroes from searchable dropdowns with portraits
- [x] **DRFT-04**: User can select their role/position (Pos 1-5) via button selector
- [x] **DRFT-05**: User can select a playstyle from role-dependent options (e.g., aggressive, passive, farming, fighting)
- [x] **DRFT-06**: User can select Radiant or Dire side
- [x] **DRFT-07**: User can select their lane assignment (Safe/Off/Mid)
- [x] **DRFT-08**: User can select 1-2 lane opponents from the already-picked enemy heroes once the game begins

### Recommendation Engine

- [x] **ENGN-01**: Rules layer fires instantly for obvious item decisions (e.g., Magic Stick vs spell-spamming lane opponents)
- [x] **ENGN-02**: Claude API generates item recommendations with analytical reasoning referencing specific hero abilities and matchup dynamics
- [x] **ENGN-03**: Hybrid orchestrator routes decisions: rules for known patterns, Claude for nuanced reasoning
- [x] **ENGN-04**: System falls back to rules-only mode with a visible notice when Claude API fails or times out (10s hard timeout)
- [x] **ENGN-05**: Claude API returns structured JSON output validated against schema before rendering
- [x] **ENGN-06**: Matchup data pipeline fetches hero-vs-hero item win rates from OpenDota/Stratz and caches in SQLite

### Output Display

- [x] **DISP-01**: Item timeline displays recommendations in phases: starting, laning, core, late game
- [x] **DISP-02**: Each recommended item shows hero/item portrait from Steam CDN with gold cost
- [x] **DISP-03**: Each recommended item includes 1-3 sentence analytical reasoning explaining WHY (referencing abilities, matchup dynamics, stats)
- [x] **DISP-04**: Situational items display as decision tree cards with conditions (e.g., "if enemy has evasion -> MKB; if magic burst -> BKB")
- [x] **DISP-05**: Loading skeleton/spinner displays during Claude API calls (2-10 seconds)
- [x] **DISP-06**: Dark theme with spectral cyan (#00d4ff) primary, Radiant teal (#6aff97), Dire red (#ff5555)

### Mid-Game Adaptation

- [x] **MIDG-01**: User can click items in the timeline to mark them as purchased (locked from re-evaluation)
- [x] **MIDG-02**: User can select lane result (Won/Even/Lost) to adjust remaining recommendations
- [x] **MIDG-03**: User can input damage profile via toggles ("heavy magic damage", "right-click heavy") and manual percentage entry
- [x] **MIDG-04**: User can mark key enemy items spotted (e.g., enemy BKB, enemy Blink Dagger)
- [x] **MIDG-05**: User can hit Re-Evaluate to regenerate only unpurchased remaining items with updated game state

### Infrastructure

- [x] **INFR-01**: Docker Compose deploys two containers: frontend (Nginx, port 8421) and backend (FastAPI, port 8420)
- [ ] **INFR-02**: Daily data refresh pipeline updates hero/item matchup data from OpenDota/Stratz APIs
- [x] **INFR-03**: Environment variable configuration via .env file (ANTHROPIC_API_KEY required, API keys optional)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Team Synergy

- **TEAM-01**: Recommendations factor in allied hero synergies and team composition gaps
- **TEAM-02**: "Your team needs X" suggestions based on full allied draft

### Neutral Items

- **NEUT-01**: Neutral item tier recommendations based on game timing
- **NEUT-02**: Neutral item suggestions adjusted for hero role and build

### Auto Integration

- **AUTO-01**: GSI integration reads game state automatically (gold, items, game time)
- **AUTO-02**: Screenshot/scoreboard parsing for auto-fill of damage profiles and enemy items
- **AUTO-03**: Auto-detect purchased items via GSI (eliminate manual click-to-mark)

### Persistence

- **PERS-01**: Build history saves recommendations from past sessions
- **PERS-02**: Session review allows revisiting and comparing past game itemizations

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| In-game overlay (Overwolf/GSI) | Controversial, massive complexity, Valve policy risk. Web app on second monitor is the target |
| Voice/TTS callouts | Audio implementation complex, competes with game audio |
| Community build sharing | Social features are scope creep for a personal advisor |
| Mobile-optimized layout | Desktop-first use case (second monitor/alt-tab). Don't break on mobile, don't optimize |
| Auto gold/net worth tracking | Requires GSI or tedious manual entry. Phase-based timing instead |
| Real-time meta/patch tracking | Extremely complex for marginal value. Data refresh pipeline handles naturally |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DRFT-01 | Phase 1 | Complete |
| DRFT-02 | Phase 2 | Complete |
| DRFT-03 | Phase 2 | Complete |
| DRFT-04 | Phase 2 | Complete |
| DRFT-05 | Phase 2 | Complete |
| DRFT-06 | Phase 2 | Complete |
| DRFT-07 | Phase 2 | Complete |
| DRFT-08 | Phase 4 | Complete |
| ENGN-01 | Phase 3 | Complete |
| ENGN-02 | Phase 3 | Complete |
| ENGN-03 | Phase 3 | Complete |
| ENGN-04 | Phase 3 | Complete |
| ENGN-05 | Phase 3 | Complete |
| ENGN-06 | Phase 3 | Complete |
| DISP-01 | Phase 4 | Complete |
| DISP-02 | Phase 4 | Complete |
| DISP-03 | Phase 4 | Complete |
| DISP-04 | Phase 4 | Complete |
| DISP-05 | Phase 4 | Complete |
| DISP-06 | Phase 1 | Complete |
| MIDG-01 | Phase 5 | Complete |
| MIDG-02 | Phase 5 | Complete |
| MIDG-03 | Phase 5 | Complete |
| MIDG-04 | Phase 5 | Complete |
| MIDG-05 | Phase 5 | Complete |
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 6 | Pending |
| INFR-03 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation*
