# Engine Hardening Design Spec

**Date:** 2026-03-30
**Goal:** Make Prismlab's recommendation engine monetization-ready by improving quality, UX speed, latency, and coverage across the board.
**Approach:** Full Stack Hardening (Approach C) — balanced improvements to data quality, reasoning, infrastructure, and usability.

## Context

Prismlab ships 7 milestones (v1.0-v6.0) with a hybrid recommendation engine: 3-mode routing (fast/auto/deep), deterministic rules layer, Claude API + Ollama integration, XGBoost win predictor, 3-layer caching, and graceful fallback. The app is deployed on Unraid and functional.

Before monetization or desktop distribution, the core recommendation engine needs hardening across 4 dimensions:
1. **Quality** — advice must feel like a genuine 8K+ MMR coach
2. **UX Speed** — zero manual clicks from hero pick to first recommendation
3. **Latency** — sub-second starting items, progressive loading for full builds
4. **Coverage** — handle edge cases, unusual roles, and mid-game adaptation better

## Pillar 1: Recommendation Quality

### 1A. Pro/High-MMR Build Baselines

**Problem:** Current item popularity data is all-bracket. A Herald BKB timing is not an Immortal BKB timing.

**Solution:**
- Fetch Divine/Immortal item win rates per hero per matchup from OpenDota `heroes/{id}/itemPopularity` with `?minMmr=5420`
- Cache as `hero_item_baselines` in DataCache, refreshed on pipeline cycle
- Context builder adds "What top players build" section showing top 5 items per phase with win rates
- Claude explains *deviations* from pro builds rather than inventing from scratch

**Fallback:** Current all-bracket popularity data if bracket-filtered fetch fails.

**Files affected:**
- `backend/data/opendota_client.py` — new endpoint method
- `backend/data/cache.py` — new `_hero_item_baselines` dict
- `backend/engine/context_builder.py` — new `_build_pro_reference_section()`
- `backend/data/pipeline.py` — add to refresh cycle

### 1B. Exemplar Few-Shot Prompting

**Problem:** The system prompt tells Claude *how* to reason but never shows a perfect example. Output quality varies.

**Solution:**
- Curate 15-20 gold-standard recommendations covering main archetypes:
  - Pos 1 carry vs burst lineup
  - Pos 1 carry vs sustained damage
  - Pos 2 mid vs ganking mid
  - Pos 3 offlane vs physical carry
  - Pos 3 offlane vs magic damage
  - Pos 4 soft support vs invisible heroes
  - Pos 5 hard support vs heavy physical
  - Additional archetypes enumerated during implementation (15-20 total covering all 5 positions x common threat profiles)
- Store as JSON files in `engine/prompts/exemplars/`
- Archetype matcher: given request (role, matchup damage type, enemy threat profile), select 1-2 closest exemplars
- Inject into user message as few-shot examples between context and instructions

**Files affected:**
- `backend/engine/prompts/exemplars/` — new directory with JSON exemplar files
- `backend/engine/exemplar_matcher.py` — new module
- `backend/engine/context_builder.py` — inject exemplars into user message

### 1C. Response Validation Layer

**Problem:** If Claude returns parseable JSON, it's accepted. No sanity checking for logical errors.

**Solution:**
- Post-parse validation in `HybridRecommender`:
  - **Phase-cost validation:** Starting items total < 625g, laning items each < 2500g, core items each > 1000g
  - **Duplicate detection:** Same item_id must not appear in multiple phases
  - **Counter-logic audit:** If enemies have 3+ stuns and no BKB/Linken's recommended, flag
  - **Empty phase check:** late_game and situational must not be empty
- On validation failure: retry once with error appended to user message ("Your previous recommendation had issue X, please correct")
- Track validation failure rates as metrics (log to stdout for now)

**Files affected:**
- `backend/engine/response_validator.py` — new module
- `backend/engine/recommender.py` — call validator after LLM parse, before enrichment

### 1D. Post-Match Accuracy Tracking

**Problem:** No way to measure if recommendations are actually good. No feedback loop.

**Solution:**
- Extend existing `MatchLog` + `MatchRecommendation` tables:
  - Add `followed: bool` field to MatchRecommendation (was this item purchased?)
  - Add `accuracy_score: float` to MatchLog (% of core recs purchased)
- After match ends, compute:
  - "Follow rate" — % of core recommendations that were actually purchased
  - "Follow win rate" — win rate when user bought 60%+ of core recs vs when they didn't
- Dashboard card on match history page:
  - "When you followed Prismlab: X% WR. When you deviated: Y% WR"
  - Per-item stats: items frequently recommended but rarely bought → prompt tuning signal
- API endpoint: `GET /api/analytics/accuracy` for aggregate stats

**Files affected:**
- `backend/models/match_log.py` — add `followed` field
- `backend/api/routes/analytics.py` — new accuracy endpoint
- `frontend/src/pages/MatchHistory.tsx` — accuracy dashboard cards
- `frontend/src/hooks/useGameIntelligence.ts` — enrich match log with follow data

## Pillar 2: UX Speed — Zero-Click to First Recommendation

### 2A. Auto-Run on Hero Detection

**Problem:** Even with GSI auto-filling the draft, user must manually click "Get Item Build." By then, they've left the fountain.

**Solution:**
- In `useLiveDraft` or `useGameIntelligence`: when `selectedHero` transitions from null to a hero AND `role` is set (from Stratz position or auto-infer), automatically call `recommend()`
- Guard: only auto-fire once per hero selection (don't re-fire on poll updates that don't change hero)
- Guard: don't auto-fire if user is mid-edit (e.g., manually changing opponents)
- The "Get Item Build" button remains for manual cold-start and re-triggers

**Files affected:**
- `frontend/src/hooks/useLiveDraft.ts` — trigger recommend after hero+role set
- `frontend/src/hooks/useRecommendation.ts` — expose `recommend()` for programmatic call
- `frontend/src/components/draft/GetBuildButton.tsx` — no change (still available)

### 2B. Faster Draft Polling

**Problem:** 10s polling interval means worst-case 10s delay to detect hero pick.

**Solution:**
- Reduce polling from 10s to 3s during active hero selection phase
- On GSI `hero_id` change event, immediately trigger draft fetch (don't wait for next poll)
- Once draft is complete (all 10 heroes picked), stop polling entirely
- Rate limit: backend live-match endpoint already caches Stratz/OpenDota responses

**Files affected:**
- `frontend/src/hooks/useLiveDraft.ts` — 3s interval, GSI-triggered immediate fetch
- `frontend/src/hooks/useGameIntelligence.ts` — detect hero_id change, trigger fetchDraft

### 2C. Instant Starting Items (Rules Fast Path)

**Problem:** Full Claude recommendation takes 2-15s. User needs starting items before leaving fountain (first 15s of game).

**Solution:**
- On auto-run trigger (2A), immediately fire a **fast-mode** (rules-only) request
- Display rules-based starting items within 1-2s
- Simultaneously fire the full auto/deep request in background
- When full recommendation arrives, merge it over the rules-only result:
  - Replace starting items if Claude disagrees
  - Add laning/core/late/situational phases
  - Show "Recommendations updated" toast
- Frontend needs a "partial" state: show what's available, loading indicator for remaining phases

**Files affected:**
- `frontend/src/hooks/useRecommendation.ts` — two-pass recommend (fast then full)
- `frontend/src/stores/recommendationStore.ts` — support partial data + merge
- `frontend/src/components/items/ItemTimeline.tsx` — render partial phases with loading states
- `backend/engine/recommender.py` — no change (fast mode already exists)

### 2D. Manual Draft Speedup (No GSI Fallback)

**Problem:** Without GSI, manually entering 10 heroes is 20+ clicks.

**Solution:**
- **Quick draft import:** Paste an OpenDota match URL → parse match ID → fetch heroes via OpenDota API → auto-fill all 10 heroes
  - Input field in Sidebar: "Paste match URL to import draft"
  - Backend endpoint: `GET /api/import-draft?match_id=12345`
- **One-click role+lane presets:** Buttons like "Pos 1 Safe", "Pos 2 Mid", "Pos 3 Off" that set role + lane + default playstyle in one click
  - Replace separate Role/Lane selectors with combined preset buttons (keep individual selectors as "Advanced" toggle)
- **Recent opponents memory:** Store last 5 match opponents in localStorage, show as quick-pick suggestions in opponent picker

**Files affected:**
- `backend/api/routes/draft.py` — new import-draft endpoint
- `frontend/src/components/layout/Sidebar.tsx` — import field, preset buttons
- `frontend/src/components/draft/OpponentPicker.tsx` — recent opponents suggestions

## Pillar 3: Latency Optimization

### 3A. Pre-Computed Popular Builds (Cache Warming)

**Problem:** First request for any hero+role combo hits the full pipeline cold.

**Solution:**
- On server startup (or daily pipeline), pre-compute recommendations for top 30 heroes x 3 common roles = ~90 combos
- Use fast mode (rules-only) for instant availability
- Store in ResponseCache with long TTL (24h)
- When user requests a pre-computed combo, serve instantly from cache
- Background-refresh with full matchup context when opponents become known

**Files affected:**
- `backend/engine/cache_warmer.py` — new module
- `backend/engine/recommender.py` — call warmer on startup
- `backend/data/pipeline.py` — trigger warmer after data refresh

### 3B. Streaming Recommendations (SSE)

**Note:** This supersedes 2C (rules fast path) when implemented. 2C is the quick win (two sequential requests); 3B is the proper solution (single streaming connection). Ship 2C first for immediate UX improvement, replace with 3B later.

**Problem:** User waits 5-15s for full response. All-or-nothing display.

**Solution:**
- New endpoint: `POST /api/recommend/stream` returning Server-Sent Events
- Event 1 (immediate): Rules-based items (starting + obvious counters)
- Event 2 (~2-5s): Claude's phase recommendations as they parse
- Event 3 (final): Enrichment data (timing, build paths, win condition, win probability)
- Frontend: `EventSource` or `fetch` with `ReadableStream`, progressively populate recommendationStore

**Files affected:**
- `backend/api/routes/recommend.py` — new streaming endpoint
- `backend/engine/recommender.py` — yield partial results
- `frontend/src/hooks/useRecommendation.ts` — SSE consumption
- `frontend/src/stores/recommendationStore.ts` — progressive merge

### 3C. Parallel Enrichment

**Problem:** `_enrich_all` runs timing, build paths, win condition, win probability sequentially.

**Solution:**
- Wrap the 4 enrichment calls in `asyncio.gather()`:
  - `_enrich_timing_data()`
  - `_enrich_build_paths()`
  - `_enrich_win_condition()`
  - `_enrich_win_probability()`
- These are independent — no data dependencies between them
- Expected speedup: ~2-4x for enrichment phase (currently serialized DB/cache lookups)

**Files affected:**
- `backend/engine/recommender.py` — `_enrich_all` → `asyncio.gather()`

### 3D. Hierarchical Cache Keys

**Problem:** Current cache key is full request hash. Changing one opponent invalidates the entire cache.

**Solution:**
- Three-tier cache:
  - **L1:** `hero+role+lane` → base build (TTL: 1h) — covers starting/laning items
  - **L2:** `hero+role+lane+opponents` → matchup build (TTL: 5min)
  - **L3:** `full_request_hash` → exact match (TTL: 5min, current behavior)
- On cache miss at L3, check L2 for matchup hit, then L1 for base hit
- Serve best available cache tier immediately, background-refresh with full context

**Files affected:**
- `backend/engine/recommender.py` — `ResponseCache` → `HierarchicalCache`

## Pillar 4: Coverage & Adaptiveness

### 4A. Expanded Rules Engine

**Problem:** Current rules are ability-based only. Missing item-vs-item and meta-aware counters.

**Solution:**
Add 30+ new rules in categories:
- **Item-vs-item counters:** Nullifier vs Aeon Disk/Eul's/Ghost Scepter heroes, Silver Edge vs passive-dependent (Bristleback, Phantom Assassin, Spectre), Spirit Vessel vs high-regen (Huskar, Alchemist, Morphling)
- **Meta-aware rules:** If 3+ physical cores on enemy → prioritize armor (Shiva's, AC, Crimson Guard). If 3+ magic damage → Hood/Pipe/BKB. If enemy has Techies/Tinker → prioritize mobility
- **Timing-aware rules:** If game_time > 25min, never recommend Midas. If game_time > 35min and no BKB, escalate BKB priority to "urgent"
- **Gold-aware rules:** If current gold < 1000 and dying frequently, recommend cheap defensive items over expensive core items

**Files affected:**
- `backend/engine/rules.py` — new rule methods
- `backend/data/cache.py` — any new lookup data needed

### 4B. Edge Case Handling

**Problem:** Unusual roles and game modes get weak recommendations.

**Solution:**
- **Unusual roles:** Detect when hero is in an uncommon role (pos 4 Mirana, pos 1 Dawnbreaker) via HERO_ROLE_VIABLE check. If uncommon, add context note to Claude: "This is an uncommon role for this hero — adjust builds accordingly"
- **Partial draft:** If fewer than 10 heroes picked, still recommend. Add context: "Draft is incomplete — X heroes picked. Recommendations will improve as more heroes are revealed." Focus on hero-intrinsic items (stats, lane sustainability) rather than counter-specific items
- **Turbo mode:** Add `turbo: bool` flag to request. If true, halve all timing benchmarks (20min BKB → 10min in Turbo). Adjust gold thresholds in rules engine

**Files affected:**
- `backend/engine/schemas.py` — add `turbo` field
- `backend/engine/context_builder.py` — partial draft and unusual role annotations
- `backend/engine/rules.py` — turbo mode timing adjustments

### 4C. Diff-Based Re-Evaluation

**Problem:** Mid-game re-evaluation sends full context every time. Wasteful and slow.

**Solution:**
- Track last evaluation state in `recommendationStore`
- On re-eval, compute diff: what changed since last evaluation?
  - New enemy items spotted
  - Death count changed
  - Gold/NW changed significantly (>1000g swing)
  - Game phase changed (laning → mid → late)
- Send Claude a focused "UPDATE" message: "Since last evaluation: enemy PA bought BKB at 22min, you died twice, gold dropped to 3200. What changes to the build?"
- Smaller context → faster response → lower token cost

**Files affected:**
- `backend/engine/context_builder.py` — new `build_diff()` method
- `backend/engine/recommender.py` — detect re-eval, use diff builder
- `frontend/src/stores/recommendationStore.ts` — store last eval state for diffing

### 4D. Time-Aware Reasoning

**Problem:** Recommendations don't account for game clock. Midas at 25 min is terrible advice.

**Solution:**
- Add `game_time_seconds: int | None` to RecommendRequest (populated from GSI clock)
- Rules engine: hard-block timing-inappropriate items:
  - Midas after 20 min → never recommend
  - BKB before 10 min → only if enemy has 3+ disables
  - Rapier before 35 min → only if team is losing and hero is traditional Rapier carrier
- Context builder: inject game clock into Claude message: "Current game time: 24:30. Adjust recommendations for this timing window."
- Claude already gets timing benchmarks; this adds hard rules for obviously wrong timing

**Files affected:**
- `backend/engine/schemas.py` — add `game_time_seconds` field
- `backend/engine/rules.py` — timing-gated rules
- `backend/engine/context_builder.py` — inject game clock

## Phase Breakdown (Suggested Implementation Order)

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **Phase 1** | UX Speed + Instant Items | Auto-run on hero detection (2A), faster polling (2B), rules fast path (2C), parallel enrichment (3C) |
| **Phase 2** | Quality Foundation | Pro build baselines (1A), response validation (1C), expanded rules (4A) |
| **Phase 3** | Prompt Intelligence | Exemplar few-shot prompting (1B), time-aware reasoning (4D), edge case handling (4B) |
| **Phase 4** | Latency & Caching | Hierarchical cache (3D), cache warming (3A), streaming SSE (3B) |
| **Phase 5** | Adaptiveness | Diff-based re-eval (4C), post-match accuracy tracking (1D) |
| **Phase 6** | Manual Draft UX | Draft import (2D), role+lane presets, recent opponents |

## Non-Goals

- No model fine-tuning or custom LLM training
- No allied team hero recommendations (already shipped in v1.1)
- No mobile optimization (desktop-first per CLAUDE.md)
- No real-money transaction integration (monetization strategy is out of scope for this spec)
- No Tauri desktop packaging (deferred to after hardening)

## Success Criteria

1. Zero-click from hero pick (with GSI) to seeing starting items — under 3 seconds
2. Response validation catches 95%+ of logically wrong recommendations before user sees them
3. Post-match accuracy shows positive correlation between following Prismlab builds and winning
4. P95 latency for full recommendation < 5 seconds (currently up to 15s)
5. Rules engine covers 50+ deterministic scenarios (currently ~20)
6. Users without GSI can import a draft in < 3 clicks
