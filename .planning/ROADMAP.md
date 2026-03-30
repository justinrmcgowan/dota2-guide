# Roadmap: Prismlab

## Milestones

- [x] **v1.0 MVP** - Phases 1-6 (shipped 2026-03-21)
- [x] **v1.1 Allied Synergy & Neutral Items** - Phases 7-9 (shipped 2026-03-23)
- [x] **v2.0 Live Game Intelligence** - Phases 10-14 (shipped 2026-03-26)
- [x] **v3.0 Design Overhaul & Performance** - Phases 15-18 (shipped 2026-03-27)
- [x] **v4.0 Coaching Intelligence** - Phases 19-23 (shipped 2026-03-28)
- [x] **v5.0 Supreme Companion** - Phases 24-29, 33 (shipped 2026-03-29)
- [x] **v6.0 Draft Intelligence** - Phases 30-31 (shipped 2026-03-29)
- [ ] **v7.0 Engine Hardening** - Phases 34-38 (in progress)
- [ ] **v8.0 Desktop Distribution** - Phase 32 (planned)

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

<details>
<summary>v5.0 Supreme Companion (Phases 24-29, 33) - SHIPPED 2026-03-29</summary>

- [x] **Phase 24: Audio Prompts & Volume Control** - TTS/audio cues for item timing alerts, purchase reminders, coaching callouts with volume control (completed 2026-03-29)
- [x] **Phase 25: API-Driven Draft Input** - Auto-populate allies/opponents from OpenDota/Stratz live match API using Steam ID (completed 2026-03-28)
- [x] **Phase 26: Engine Optimization** - Reduce eval latency, rule-only fast path, local LLM via Ollama, courier exclusion, concise reasoning (completed 2026-03-28)
- [x] **Phase 27: Game Lifecycle Management** - Handle mid-game abandons, new game starts, state reset between matches, GSI reconnection (completed 2026-03-28)
- [x] **Phase 28: Patch 7.41 Data Refresh** - New items, updated costs/recipes for patch 7.41 (completed 2026-03-28)
- [x] **Phase 29: Stream Deck Integration** - Elgato Stream Deck plugin consuming existing WebSocket game state feed (completed 2026-03-29)
- [x] **Phase 33: Game Analytics & Match Logging** - Match logging, recommendation tracking, match history dashboard (completed 2026-03-28)

</details>

<details>
<summary>v6.0 Draft Intelligence (Phases 30-31) - SHIPPED 2026-03-29</summary>

- [x] **Phase 30: ML Win Predictor** - XGBoost/logistic regression model trained on 200k+ recent matches, draft win probability, synergy/counter matrices by MMR bracket (completed 2026-03-29)
- [x] **Phase 31: Hero Selector** - Role/lane-filtered hero suggestions ranked by predicted win rate, ally synergy, and enemy counter-value (completed 2026-03-29)

</details>

### v7.0 Engine Hardening (In Progress)

- [x] **Phase 34: UX Speed & Instant Items** - Two-pass recommendations (rules-fast then Claude-full), 3s draft polling, GSI auto-trigger, parallel enrichment, cross-phase deduplication (completed 2026-03-30)
- [ ] **Phase 35: Quality Foundation** - Pro/high-MMR build baselines from OpenDota, response validation layer with retry, 30+ expanded deterministic rules (item-vs-item, meta-aware, timing-aware)
- [ ] **Phase 36: Prompt Intelligence** - Exemplar few-shot prompting (15-20 gold-standard builds), time-aware reasoning with game clock injection, edge case handling (unusual roles, partial drafts, Turbo mode)
- [ ] **Phase 37: Latency & Caching** - Hierarchical 3-tier cache (hero+role → matchup → full request), cache warming for top 90 hero+role combos, SSE streaming endpoint for progressive item display
- [ ] **Phase 38: Adaptiveness & Accuracy** - Diff-based re-evaluation (send only what changed to Claude), post-match accuracy tracking (follow rate, follow win rate), accuracy dashboard on match history

### v8.0 Desktop Distribution (Planned)

- [ ] **Phase 32: Tauri Desktop App** - Native Windows app via Tauri (React frontend in native webview, Python backend as sidecar), first-run wizard with API key entry, auto-detect Dota 2 path, GSI cfg placement, system tray, native notifications

## Phase Details

### v7.0 Engine Hardening (In Progress)

**Milestone Goal:** Make Prismlab's recommendation engine monetization-ready by improving quality, latency, and coverage. Advice should feel like a genuine 8K+ MMR coach. Zero-click from hero pick to starting items. Post-match accuracy tracking to prove value.

**Design Spec:** `docs/superpowers/specs/2026-03-30-engine-hardening-design.md`

### Phase 34: UX Speed & Instant Items
**Goal:** Zero manual clicks from hero pick (with GSI) to seeing starting items in under 3 seconds
**Depends on:** Phase 26 (engine modes), Phase 25 (live draft API)
**Success Criteria** (what must be TRUE):
  1. When GSI detects hero + role, recommendations fire automatically without clicking "Get Item Build"
  2. Rules-based starting items appear in <2s, full Claude recommendation merges in behind
  3. Draft polling detects hero picks within 3 seconds (not 10)
  4. No duplicate items appear across recommendation phases
  5. Enrichment pipeline runs in parallel (asyncio.gather)
**Status:** Complete (2026-03-30)

### Phase 35: Quality Foundation
**Goal:** Recommendations are grounded in what top players actually build, validated for logical consistency, and cover 50+ deterministic matchup scenarios
**Depends on:** Phase 34 (UX speed ensures fast feedback loop for testing quality changes)
**Success Criteria** (what must be TRUE):
  1. Context builder includes Divine/Immortal item win rates per hero per matchup from OpenDota
  2. Claude explains deviations from pro builds rather than inventing from scratch
  3. Response validator catches phase-cost violations, cross-phase duplicates, and missing counter items — retries once on failure
  4. Rules engine covers 50+ deterministic scenarios (currently ~20) including item-vs-item counters and meta-aware team composition rules
  5. Validation failure rates are logged for prompt tuning

### Phase 36: Prompt Intelligence
**Goal:** Claude's reasoning consistently matches the quality of an expert coach through few-shot exemplars, game-clock awareness, and graceful handling of edge cases
**Depends on:** Phase 35 (quality foundation provides the data and validation that exemplars build on)
**Success Criteria** (what must be TRUE):
  1. 15-20 curated gold-standard recommendations are stored and the 1-2 closest are injected as few-shot examples per request
  2. Game clock is injected into context and rules hard-block timing-inappropriate items (no Midas after 20 min)
  3. Unusual roles are detected and flagged to Claude with adjusted context
  4. Partial drafts (<10 heroes) still produce useful recommendations with appropriate caveats
  5. Turbo mode flag halves all timing benchmarks

### Phase 37: Latency & Caching
**Goal:** P95 full recommendation latency under 5 seconds through hierarchical caching, pre-computation, and streaming
**Depends on:** Phase 35 (pro baselines are the data cached at L1/L2)
**Success Criteria** (what must be TRUE):
  1. Three-tier cache: hero+role+lane (1h TTL) → +opponents (5min) → full request (5min)
  2. Top 90 hero+role combos are pre-warmed on startup with rules-only recommendations
  3. SSE streaming endpoint delivers rules items immediately, Claude results progressively, enrichment data last
  4. Frontend progressively renders phases as they stream in

### Phase 38: Adaptiveness & Accuracy
**Goal:** Mid-game re-evaluations are faster and cheaper via diff-based context, and post-match tracking proves recommendation value
**Depends on:** Phase 35 (validation ensures accuracy tracking data is clean)
**Success Criteria** (what must be TRUE):
  1. Re-evaluations send only what changed since last eval (new enemy items, deaths, gold swings, phase transitions)
  2. Diff-based context reduces token usage by 40%+ for mid-game re-evals
  3. Post-match accuracy score computed: % of core recommendations purchased
  4. Match history dashboard shows "follow rate" and "follow win rate vs deviate win rate"
  5. Items frequently recommended but rarely purchased are flagged for prompt review

### v8.0 Desktop Distribution (Planned)

**Milestone Goal:** Package Prismlab as a one-click Windows installer that non-technical users can install and run locally, with automatic Dota 2 GSI configuration, API key setup, and system tray operation.

### Phase 32: Tauri Desktop App
**Goal:** Package Prismlab as a native Windows desktop application using Tauri v2
**Depends on:** Phase 27 (game lifecycle), Phase 28 (current patch data), v7.0 Engine Hardening (quality must be proven before shipping to external users)
**Requirements**: TBD
**Plans:** TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 34. UX Speed & Instant Items | 7/7 | Complete | 2026-03-30 |
| 35. Quality Foundation | 0/TBD | Not started | - |
| 36. Prompt Intelligence | 0/TBD | Not started | - |
| 37. Latency & Caching | 0/TBD | Not started | - |
| 38. Adaptiveness & Accuracy | 0/TBD | Not started | - |
| 32. Tauri Desktop App | 0/TBD | Not started | - |
