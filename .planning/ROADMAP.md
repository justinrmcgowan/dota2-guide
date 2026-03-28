# Roadmap: Prismlab

## Milestones

- [x] **v1.0 MVP** - Phases 1-6 (shipped 2026-03-21)
- [x] **v1.1 Allied Synergy & Neutral Items** - Phases 7-9 (shipped 2026-03-23)
- [x] **v2.0 Live Game Intelligence** - Phases 10-14 (shipped 2026-03-26)
- [x] **v3.0 Design Overhaul & Performance** - Phases 15-18 (shipped 2026-03-27)
- [x] **v4.0 Coaching Intelligence** - Phases 19-23 (shipped 2026-03-28)
- [ ] **v5.0 Supreme Companion** - Phases 24-29 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>v1.0 MVP (Phases 1-6) - SHIPPED 2026-03-21</summary>

- [x] **Phase 1: Foundation** - Project scaffolding, Docker, DB models, OpenDota client
- [x] **Phase 2: Draft Inputs** - Hero picker, role/playstyle selection, lane/side UI
- [x] **Phase 3: Recommendation Engine** - Rules layer, Claude API integration, hybrid orchestrator
- [x] **Phase 4: Item Timeline & End-to-End Flow** - Phased item display with reasoning tooltips
- [x] **Phase 5: Mid-Game Adaptation** - Lane result, damage profile, enemy items, re-evaluate
- [x] **Phase 6: Data Pipeline & Hardening** - Daily refresh, error handling, polish

</details>

<details>
<summary>v1.1 Allied Synergy & Neutral Items (Phases 7-9) - SHIPPED 2026-03-23</summary>

- [x] **Phase 7: Tech Debt & Polish** - Dead code removal, tests, admin proxy
- [x] **Phase 8: Allied Synergy** - Ally item context, team coordination prompt rules
- [x] **Phase 9: Neutral Items** - Neutral item pipeline, Claude ranking, tier display

</details>

<details>
<summary>v2.0 Live Game Intelligence (Phases 10-14) - SHIPPED 2026-03-26</summary>

- [x] **Phase 10: GSI Receiver & WebSocket Pipeline** - Dota 2 GSI endpoint, WebSocket broadcast, frontend connection
- [x] **Phase 11: Live Game Dashboard** - Auto hero/role detection, item marking, stats bar, game clock
- [x] **Phase 12: Auto-Refresh & Lane Detection** - Event triggers, cooldown queue, lane auto-detect, toast notifications
- [x] **Phase 13: Screenshot Parsing** - Claude Vision endpoint, screenshot modal, clipboard paste, Apply to Build
- [x] **Phase 14: Recommendation Quality & System Hardening** - Rate limiter, response cache, validation, rules expansion

</details>

<details>
<summary>v3.0 Design Overhaul & Performance (Phases 15-18) - SHIPPED 2026-03-27</summary>

- [x] **Phase 15: Store Consolidation & Tech Debt** - Merge GSI hooks, deduplicate types, auto-suggest playstyle
- [x] **Phase 16: Backend Data Cache** - In-memory hero/item cache, three-layer cache coordination, session safety
- [x] **Phase 17: Design System Migration** - Tactical Relic Editorial retheme across all components
- [x] **Phase 18: Screenshot KDA Feed-Through** - Feed parsed KDA/level data into recommendation context

</details>

<details>
<summary>v4.0 Coaching Intelligence (Phases 19-23) - SHIPPED 2026-03-28</summary>

- [x] **Phase 19: Data Foundation & Prompt Architecture** - Ability/timing data pipeline, DataCache extensions, system-prompt-vs-user-message data split (completed 2026-03-27)
- [x] **Phase 20: Counter-Item Intelligence** - Ability-driven counter rules, counter_target tagging, threat context for Claude (completed 2026-03-27)
- [x] **Phase 21: Timing Benchmarks** - Timing windows in UI, urgency indicators, Claude timing reasoning, GSI live comparison (completed 2026-03-27)
- [x] **Phase 22: Build Path Intelligence** - Component ordering, adaptive build paths, GSI gold tracking (completed 2026-03-27)
- [x] **Phase 23: Win Condition Framing** - Draft classification, strategy anchoring, enemy win condition assessment (completed 2026-03-27)

</details>

### v5.0 Supreme Companion (In Progress)

**Milestone Goal:** Transform Prismlab into the definitive Dota 2 companion -- with audio coaching, auto-populated drafts from live API data, sub-5s recommendation latency, graceful game lifecycle handling, and patch 7.41 data freshness.

- [ ] **Phase 24: Audio Prompts & Volume Control** - TTS/audio cues for item timing alerts, purchase reminders, coaching callouts with volume control
- [x] **Phase 25: API-Driven Draft Input** - Auto-populate allies/opponents from OpenDota/Stratz live match API using Steam ID (completed 2026-03-28)
- [x] **Phase 26: Engine Optimization** - Reduce eval latency, rule-only fast path, local LLM via Ollama, courier exclusion, concise reasoning (completed 2026-03-28)
- [ ] **Phase 27: Game Lifecycle Management** - Handle mid-game abandons, new game starts, state reset between matches, GSI reconnection
- [ ] **Phase 28: Patch 7.41 Data Refresh** - New items (Wizard Hat, Shawl, Splintmail, Chasm Stone, Consecrated Wraps, Essence Distiller, Crella's Crozier, Hydra's Breath), updated costs/recipes
- [ ] **Phase 29: Stream Deck Integration** - Elgato Stream Deck plugin consuming existing WebSocket game state feed, rendering live Dota 2 data to XL buttons

## Phase Details

### Phase 19: Data Foundation & Prompt Architecture
**Goal**: Ability metadata, hero-ability mappings, and item timing benchmarks are fetched, cached, and available in DataCache -- and the prompt architecture cleanly separates static directives (system message) from dynamic data (user message)
**Depends on**: Phase 18
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. After a data refresh, the DataCache contains ability metadata for all heroes (behavior, damage type, BKB-pierce, dispellable) queryable by property
  2. After a data refresh, the DataCache contains item timing benchmarks (hero, item, time bucket, games, win rate) for all heroes with sufficient sample size
  3. The system prompt stays under 5,000 tokens total and contains only reasoning directives -- no dynamic data (timing numbers, ability descriptions, component lists)
  4. Three-cache coherence is maintained: after refresh, DataCache contains fresh ability + timing data, RulesEngine is re-initialized, and ResponseCache is cleared -- atomically
**Plans:** 3/3 plans complete
Plans:
- [x] 19-01-PLAN.md -- Data layer foundation: OpenDota fetch methods, SQLAlchemy models, test scaffolds
- [x] 19-02-PLAN.md -- DataCache extension, timing service, refresh pipeline, seed integration
- [ ] 19-03-PLAN.md -- System prompt v4.0 directives and token budget tests

### Phase 20: Counter-Item Intelligence
**Goal**: Counter-item recommendations are driven by enemy ability properties instead of hardcoded hero ID lists, and Claude's reasoning names the specific ability being countered
**Depends on**: Phase 19
**Requirements**: CNTR-01, CNTR-02, CNTR-03, CNTR-04
**Success Criteria** (what must be TRUE):
  1. The rules engine recommends counter-items by querying ability properties (channeled, passive, BKB-pierce) rather than matching against hardcoded hero ID lists
  2. At least 5 new counter-item rules fire correctly: channeled ult interrupts (Eul's), single-target ult saves (Lotus/Linken's), escape counters, high-regen counters (Spirit Vessel), and burst/passive counters (Break items)
  3. Counter-item reasoning in the recommendation response names the specific enemy ability being countered (e.g., "Eul's Scepter to interrupt Witch Doctor's Death Ward")
  4. When enemy performance data is available (KDA from screenshots or GSI), counter-item priority escalates against high-performing enemies
**Plans:** 3/3 plans complete
Plans:
- [x] 20-01-PLAN.md -- Schema extension, test fixtures, ability helpers, threat utility
- [ ] 20-02-PLAN.md -- Refactor 14 rules to ability-first, add 4 new rule methods, threat escalation
- [x] 20-03-PLAN.md -- Context builder ability annotations for Claude user message

### Phase 21: Timing Benchmarks
**Goal**: Users see data-backed timing windows on recommended items -- how early is good, when is on-track, when is late -- with urgency signals for timing-sensitive purchases and live tracking during GSI games
**Depends on**: Phase 19
**Requirements**: TIME-01, TIME-02, TIME-03, TIME-04
**Success Criteria** (what must be TRUE):
  1. Each recommended item displays timing benchmark ranges (good / on-track / late) with associated win rate gradients, not single-minute targets
  2. Items with steep win-rate falloff at later purchase times show a distinct urgency indicator, visually separating timing-critical items from flexible ones
  3. Claude's reasoning references specific timing benchmarks when explaining item urgency (e.g., "BKB before 25 minutes has a 58% win rate vs. 41% after 30 minutes")
  4. During GSI-connected games, the user can see how their current gold and game clock compare against the timing benchmark window for upcoming items
**Plans:** 2/2 plans complete
Plans:
- [x] 21-01-PLAN.md -- Backend zone classification, schema extension, context builder timing section, recommender enrichment
- [x] 21-02-PLAN.md -- Frontend TimingBar component, CSS urgency animation, ItemCard/PhaseCard/ItemTimeline wiring, GSI integration

### Phase 22: Build Path Intelligence
**Goal**: Users see the optimal component purchase order for each recommended item, with reasoning for why to buy each component in that order, adapting to game state
**Depends on**: Phase 20 (ability context enriches component reasoning), Phase 21 (timing context informs urgency of component ordering)
**Requirements**: PATH-01, PATH-02, PATH-03, PATH-04
**Success Criteria** (what must be TRUE):
  1. Each recommended item shows an ordered list of components to purchase, not just the final item name
  2. Each component step includes reasoning for its position in the order (e.g., "Ogre Axe first for +10 STR survivability in a losing lane")
  3. During GSI-connected games, components that are affordable at the player's current gold are visually highlighted
  4. Component ordering adapts to game state: losing lane shifts defensive components earlier, winning lane prioritizes offensive components
**Plans:** 2/2 plans complete
Plans:
- [x] 22-01-PLAN.md -- Backend: ComponentStep/BuildPathResponse schemas, _enrich_build_paths enrichment, system prompt directive
- [x] 22-02-PLAN.md -- Frontend: BuildPathSteps component, PhaseCard integration, GSI gold affordability
**UI hint**: yes

### Phase 23: Win Condition Framing
**Goal**: Item recommendations are anchored by a team-level win condition statement that classifies how the draft wins, frames the overall strategy, and accounts for the enemy team's macro plan
**Depends on**: Phase 20, Phase 21, Phase 22 (all intelligence layers proven before adding macro framing)
**Requirements**: WCON-01, WCON-02, WCON-03, WCON-04
**Success Criteria** (what must be TRUE):
  1. Given a full 10-hero draft, the system classifies the allied team into a macro strategy archetype (teamfight, split-push, pick-off, deathball, late-game scale) with a confidence indicator
  2. The win condition statement appears in the recommendation response and visibly anchors the overall_strategy -- item recommendations reflect the team's win condition, not just individual matchup counters
  3. When the win condition favors early aggression, luxury late-game items are deprioritized in favor of earlier power spikes; when it favors scaling, timing-sensitive mid-game items are still flagged but the build path extends toward late-game
  4. The system assesses the enemy team's likely win condition and recommends counter-strategy items (e.g., "Enemy draft wins through teamfight -- consider split-push enabling items to avoid 5v5")
**Plans:** 2/2 plans complete
Plans:
- [x] 23-01-PLAN.md -- Backend: WinConditionClassifier, schema extension, context builder Team Strategy section, recommender enrichment
- [x] 23-02-PLAN.md -- Frontend: WinConditionBadge component, ItemTimeline integration, all_opponents request wiring
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 19 -> 20 -> 21 -> 22 -> 23

Note: Phase 20 and Phase 21 both depend only on Phase 19 and could theoretically execute in parallel, but sequential execution is the default.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 19. Data Foundation & Prompt Architecture | v4.0 | 2/3 | Complete    | 2026-03-27 |
| 20. Counter-Item Intelligence | v4.0 | 2/3 | Complete    | 2026-03-27 |
| 21. Timing Benchmarks | v4.0 | 2/2 | Complete    | 2026-03-27 |
| 22. Build Path Intelligence | v4.0 | 2/2 | Complete    | 2026-03-27 |
| 23. Win Condition Framing | v4.0 | 2/2 | Complete    | 2026-03-27 |

### Phase 24: Audio Prompts & Volume Control

**Goal:** TTS or audio cue system that announces item timing alerts, purchase reminders, and coaching callouts with configurable volume control
**Requirements**: TBD
**Depends on:** Phase 23
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 24 to break down)

### Phase 25: API-Driven Draft Input

**Goal:** Auto-populate allies and opponents from OpenDota/Stratz live match API using Steam ID, replacing manual hero selection during active games
**Requirements**: DRAFT-01, DRAFT-02, DRAFT-03, DRAFT-04, DRAFT-05
**Depends on:** Phase 23
**Plans:** 2/2 plans complete

Plans:
- [x] 25-01-PLAN.md -- Backend: Stratz GraphQL client, OpenDota live extension, /api/live-match endpoint, settings defaults
- [x] 25-02-PLAN.md -- Frontend: Steam ID settings, live draft polling hook, auto-draft trigger, API client extension

### Phase 26: Engine Optimization

**Goal:** 3-mode recommendation engine (Fast/Auto/Deep) with local LLM via Ollama, API cost tracking with budget cap, and training data pipeline for fine-tuning
**Requirements**: ENG-01, ENG-02, ENG-03, ENG-04, ENG-05, ENG-06, ENG-07
**Depends on:** Phase 23
**Plans:** 3/3 plans complete

Plans:
- [x] 26-01-PLAN.md -- Backend: OllamaEngine, CostTracker, mode routing in HybridRecommender, config/schema extensions
- [x] 26-02-PLAN.md -- Frontend: Mode selector in Settings, budget display, mode wiring to recommend requests
- [x] 26-03-PLAN.md -- Training data generation script for Ollama fine-tuning

### Phase 27: Game Lifecycle Management

**Goal:** Gracefully handle mid-game abandons, new game detection, full state reset between matches, purchased items clearing, and GSI reconnection without stale data leaking between games
**Requirements**: LIFE-01, LIFE-02, LIFE-03, LIFE-04, LIFE-05
**Depends on:** Phase 23
**Success Criteria** (what must be TRUE):
  1. Game state (hero, role, playstyle, allies, opponents, purchased items, dismissed items, lane result) persists across page refreshes via localStorage
  2. When a new match starts (different GSI match ID), all match state is cleared but settings are preserved
  3. On GSI disconnect, match state is preserved for 10 minutes with a "Reconnecting..." indicator; auto-clears after timeout
  4. Backend session sync endpoint accepts and returns session state for multi-device durability
**Plans:** 1/2 plans executed

Plans:
- [x] 27-01-PLAN.md -- localStorage persistence (Zustand persist), match_id pipeline, new game detection + reset
- [ ] 27-02-PLAN.md -- Disconnect timeout handling, reconnect indicator, backend session sync endpoint

### Phase 28: Patch 7.41 Data Refresh

**Goal:** Update hero/item/ability database to Dota 2 patch 7.41 — 9 new items, Cornucopia removed, Refresher Orb rework, Shiva's/Blade Mail/Bloodstone recipe changes, updated costs, neutral T1 available from minute 0
**Requirements**: TBD
**Depends on:** Phase 23
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 28 to break down)

### Phase 29: Stream Deck Integration

**Goal:** Elgato Stream Deck plugin (Node.js, SDK v2) that connects to Prismlab's existing WebSocket broadcast as a display consumer, rendering live game state data (gold, KDA, game clock, items, Rosh status, tower counts, alive/dead) to Stream Deck XL buttons with no backend changes required
**Requirements**: TBD
**Depends on:** Phase 10 (GSI + WebSocket pipeline must be operational)
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 29 to break down)
