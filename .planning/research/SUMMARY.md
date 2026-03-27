# Project Research Summary

**Project:** Prismlab v4.0 — Coaching Intelligence
**Domain:** Dota 2 hybrid rules+LLM item advisor — coaching intelligence expansion
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

Prismlab v4.0 adds four coaching intelligence layers to an existing, validated hybrid recommendation engine: timing benchmarks (when to buy items relative to win-rate cliffs), ability-specific counter-item logic (what counters a specific mechanic, not just a hero), build path ordering (which components to buy first and why), and win condition framing (how your team's draft wins). All four features share the same integration pattern: new data fetched in the refresh pipeline, stored in SQLite, loaded into the DataCache singleton, consumed by the RulesEngine deterministically and by the ContextBuilder as structured Claude context. Zero new pip packages and zero new npm packages are required — the entire milestone is application code over existing infrastructure.

The recommended execution order mirrors data dependency: abilities and timing data must be in the DataCache before any intelligent feature can fire. Build the data foundation first (new OpenDota endpoints, two new SQLite tables, extended DataCache frozen dataclasses), then wire ability-aware counter rules, then surface timing benchmarks in context and UI, then add build path resolution, and finally add win condition classification. This order is not arbitrary — each phase's artifacts are prerequisites for the next. The two most important new data sources are OpenDota `/constants/abilities` + `/constants/hero_abilities` (for counter-item depth) and `/scenarios/itemTimings` (for timing benchmarks). Both endpoints have been verified live with confirmed response schemas.

The most dangerous pitfall is the one that touches all four features: treating the system prompt as a data store rather than a directive layer. Every new feature has a temptation to embed its data in the system prompt (timing numbers, ability descriptions, component lists). This breaks Claude's prompt cache economics, inflates token costs, and increases latency. The correct architecture is firm: static reasoning instructions go in the system prompt (budget: ~5,000 tokens total, currently ~3,300), dynamic per-request data goes in the user message (budget: ~2,000 tokens). The secondary risk is OpenDota rate-limit exhaustion if timing data is fetched per hero+item pair rather than per hero (124 calls vs. up to 2,480 calls per refresh cycle). Both risks have clear mitigations documented in PITFALLS.md and must be addressed before any feature work begins.

## Key Findings

### Recommended Stack

No new dependencies are introduced in v4.0. The existing stack (React 19, Vite 8, Tailwind v4, Zustand 5, FastAPI, SQLAlchemy, SQLite, httpx, APScheduler, anthropic SDK, DataCache singleton) handles everything. New backend code consists entirely of new methods on existing classes (`OpenDotaClient`, `DataCache`, `RulesEngine`, `ContextBuilder`) plus two new engine modules (`build_path.py`, `win_condition.py`) and two new data service modules (`timing_service.py`, `ability_service.py`). Two new SQLAlchemy models (`HeroItemTimings`, `HeroAbilityData`) extend the existing schema with no breaking changes.

**Core new components (no new packages):**
- `OpenDotaClient.fetch_item_timings()` / `fetch_abilities()` / `fetch_hero_abilities()`: New API methods using existing `httpx.AsyncClient`
- `HeroItemTimings` + `HeroAbilityData`: New SQLite tables following existing `HeroItemPopularity`/`MatchupData` patterns
- `TimingBucket` + `AbilityCached`: New frozen dataclasses extending existing `HeroCached`/`ItemCached` pattern in DataCache
- `BuildPathResolver` (`engine/build_path.py`, NEW): Resolves component trees from existing `ItemCached.components` (already in cache — no new data needed)
- `WinConditionClassifier` (`engine/win_condition.py`, NEW): Classifies team compositions from existing `HeroCached.roles` (already in cache — no new data needed)
- Extended refresh pipeline: 144 additional API calls per cycle (2 abilities endpoints + 140 per-hero timing calls), consuming ~4,320 calls/month — well within the 50,000/month free tier

### Expected Features

**Must have (table stakes for v4.0):**
- Per-item timing benchmark display with urgency signal — shown as win-rate ranges (good/on-track/late), NOT single-minute targets
- Timing context in Claude's user message so it can reason about urgency and timing windows in natural language
- Ability-aware counter-item rules that query ability properties dynamically rather than hardcoded hero ID lists
- Counter reasoning that names the specific ability being countered ("Eul's interrupts Witch Doctor's Death Ward")
- Build path component ordering for high-impact items (BKB, Manta, Diffusal, Orchid, S&Y — scope narrowed to 10-15 items, not the full catalog)
- Win condition statement in `overall_strategy` framing how the team wins, not just what to counter

**Should have (competitive differentiators for v4.0):**
- Live timing comparison via GSI (compare current gold and game clock against expected timing window)
- Component gold tracking (highlight which components are affordable at current gold)
- Counter-item priority escalation based on enemy KDA from screenshot/GSI data
- Enemy win condition assessment (requires expanding `RecommendRequest` to include all 5 enemy hero IDs, currently only lane opponents)

**Defer (v5+):**
- Dynamic win condition re-assessment mid-game (stateful game-phase tracking beyond current event triggers)
- Timing-aware re-evaluation weighting (complex item pivot logic when timing windows are missed)
- Full ability-property-driven refactor of the existing 18 hardcoded rules (ship new ability-driven rules alongside the existing rules first, full migration later)
- Per-match-ID timing comparison against personal history (requires Steam login and replay parsing — out of scope)

### Architecture Approach

All four v4.0 features integrate via the same established pattern: data flows from OpenDota API through the refresh pipeline into SQLite, is loaded atomically into DataCache at startup/refresh, consumed synchronously by RulesEngine (deterministic signal generation), assembled into structured context by ContextBuilder (user message sections), reasoned about by Claude via the LLMEngine (explanation quality), and merged/validated by HybridRecommender before returning to the frontend. The ResponseCache sits at the top to prevent redundant work. Adding v4.0 features means extending each layer — not bypassing it or adding new sidecars.

**Major components and their v4.0 roles:**
1. `data/refresh.py` — extended with 144 new API calls (abilities x2, timing x140+ heroes), rate-limited with `asyncio.Semaphore(2)` and 1s batch delays to respect 60 req/min
2. `data/cache.py` — extended with `TimingBucket` + `AbilityCached` frozen dataclasses, new lookup methods (`has_channeled_ability`, `get_build_path`, `get_timing_benchmarks`, `get_abilities_by_property`)
3. `engine/rules.py` — extended with 4-6 new ability-driven counter rules (Eul's vs channeled, Lotus vs single-target, Manta vs dispellable, BKB priority upgrade, Break vs passive)
4. `engine/context_builder.py` — three new section builders (`_build_timing_section`, `_build_ability_threats_section`, `_build_team_strategy_section`)
5. `engine/build_path.py` (NEW) — `BuildPathResolver` resolves component trees deterministically from cached data; cheapest-first default with survival-component override for lost-lane scenarios
6. `engine/win_condition.py` (NEW) — `WinConditionClassifier` classifies team compositions from `HeroCached.roles` into six archetypes (teamfight, split-push, pick-off, 4-protect-1, deathball, tempo)
7. `engine/prompts/system_prompt.py` — ~600 token additions for timing instructions, ability-aware counter guidance, win condition framing, and component ordering notes (new total ~3,900 tokens, safely within cache threshold)
8. `engine/schemas.py` — `ComponentStep` model added, `ItemRecommendation.build_path` optional field, `RecommendResponse.win_condition` optional field; all new fields are optional so the frontend degrades gracefully when null

### Critical Pitfalls

1. **System prompt bloat breaks cache economics** — The system prompt must stay under ~5,000 tokens. Dynamic data (timing numbers, ability descriptions, component lists) belongs in the USER message, not the system prompt. System prompt additions should be directives only ("If timing data is present, flag items that are behind schedule"), never data. Set this architecture before writing any feature code; it governs all four features simultaneously. Warning sign: `cache_creation_input_tokens` on >20% of requests.

2. **OpenDota rate limit exhaustion from naive timing fetch** — Query `/scenarios/itemTimings?hero_id={id}` without an item filter to get all items for one hero in a single call (124 total calls), not per hero+item pair (up to 2,480 calls). Parse `games` and `wins` fields explicitly as strings and cast to int in application code — they are NOT integers in the API response and will cause silent validation errors if assumed otherwise.

3. **Three-cache coherence breakage** — Timing and ability data must join the existing DataCache atomic swap, not live in separate singletons. The invalidation order in `refresh_all_data()` must update DataCache (with all new dicts) before clearing ResponseCache. An integration test must verify: after refresh, ResponseCache is empty AND DataCache contains fresh data for heroes, items, abilities, and timings simultaneously.

4. **Rules engine and LLM contradicting each other on counter-items** — Add a `counter_target` field to `RuleResult` identifying which enemy hero/ability the rule addresses. Pass this explicitly in the "Already Recommended" section of the user message so Claude knows not to recommend a second counter for the same threat. Without this, both layers may address the same threat independently (e.g., rules recommends Spirit Vessel vs Alchemist healing; LLM also recommends Shiva's Guard vs Alchemist healing).

5. **Win condition classification creating item recommendation tunnel vision** — Win condition classification must be a contextual suggestion fed to Claude, not a filter on item recommendations. Classify as primary + fallback archetype, and let Claude reason about whether it applies given the current game state. Re-evaluate requests must be able to change the win condition framing when lane results or game state change. Hardcoding item priority overrides based on win condition is explicitly the wrong approach.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Data Foundation + Prompt Architecture
**Rationale:** Everything else depends on ability data and timing data being in DataCache. Establish the system-prompt-vs-user-message data split for all four features before writing any feature code — this architectural decision cannot be retrofitted cleanly. Build new OpenDota client methods, SQLite models, DataCache extensions, and refresh pipeline expansions. Verify three-cache coherence with an integration test before proceeding to any feature phase.
**Delivers:** Three new OpenDota client methods; `HeroItemTimings` + `HeroAbilityData` SQLite tables; `TimingBucket` + `AbilityCached` frozen dataclasses in DataCache with new lookup methods; extended `refresh_all_data()` with rate-limited timing + ability fetches (`asyncio.Semaphore(2)`, 1s batch delays); integration test verifying three-cache coherence post-refresh.
**Addresses:** Foundation for all four feature categories; resolves Pitfall P1 (prompt architecture) and P3 (cache coherence) before they can cause damage.
**Avoids:** P1 (prompt bloat — data/instruction split established upfront), P2 (rate-limited timing fetch — per-hero not per-hero-per-item), P3 (DataCache atomic swap extended to include new dicts).

### Phase 2: Ability-Aware Counter-Item Rules
**Rationale:** Ability data is now in DataCache. The highest-value, lowest-latency improvement is new RulesEngine rules that query ability properties instead of hero ID lists. These fire before the LLM call, add zero API cost, and dramatically improve counter-item depth. Establishing the `counter_target` tagging on `RuleResult` here also prevents the rules/LLM contradiction pitfall from taking hold before Phase 3 adds timing context.
**Delivers:** 4-6 new ability-driven rule methods in `rules.py`; `counter_target` field on `RuleResult`; updated `_build_rules_lines()` in ContextBuilder passing target context to LLM; new `_build_ability_threats_section()` in ContextBuilder; ability-aware counter instructions added to system prompt (~200 tokens).
**Uses:** `DataCache.has_channeled_ability()`, `get_abilities_by_property()` — delivered in Phase 1.
**Avoids:** P4 (rules/LLM contradiction — explicit `counter_target` tagging prevents duplicate countering of the same threat).

### Phase 3: Timing Benchmarks
**Rationale:** Timing data is in DataCache from Phase 1. This phase wires it into the recommendation pipeline as Claude context first (highest leverage, minimal schema risk), and as optional RulesEngine urgency rules when GSI clock data is present. Timing display in the frontend is additive and backward-compatible because timing information flows through Claude's reasoning text initially, with UI badges as a polishing step.
**Delivers:** `_build_timing_section()` in ContextBuilder (top 5 items per hero, early/on-track/late windows with win rate at each bracket); timing benchmark instructions in system prompt (~150 tokens); optional urgency rules in `rules.py` when GSI clock is available; frontend urgency badges on item cards showing ranges not single-minute targets; timing context display in PhaseCard.
**Avoids:** P5 (prescriptive timing — ranges with win-rate correlation displayed, adjusted for lane result; never a single "buy by X:XX" target), P2 (timing data already cached, no per-request API calls).

### Phase 4: Build Path Intelligence
**Rationale:** `ItemCached.components` has always been in DataCache — this phase is entirely schema and presentation work, not a data pipeline addition. Placed after Phases 2-3 because it requires schema changes (`ComponentStep`, `ItemRecommendation.build_path`) that need frontend coordination, and because the ability-aware context from Phase 2 enables Claude to produce richer component reasoning. Scope is deliberately narrow: 10-15 high-impact items only.
**Delivers:** `engine/build_path.py` (`BuildPathResolver` with cheapest-first default + survival-component-first override when lane is lost); `ComponentStep` model in `schemas.py`; optional `build_path` field on `ItemRecommendation`; enrichment step in `recommender.py` after `_validate_item_ids()`; system prompt component ordering notes (~100 tokens); frontend build path display (one level of components below item card).
**Avoids:** P6 (static build paths ignoring game state — LLM handles nuanced game-state-aware ordering; `BuildPathResolver` handles mechanical component resolution; no static ordering table for >15 items; rule is "cheapest useful component first" as fallback, not a bespoke ordering per item).

### Phase 5: Win Condition Framing
**Rationale:** Win condition classification uses only `HeroCached.roles` already in cache — no new data pipeline dependency. Placed last because it is the most nuanced feature (classification accuracy for ambiguous drafts is a judgment call), and benefits from all prior context (ability threats, timing urgency) being available to Claude when it reasons about macro strategy. The classifier is a hint to Claude, not a deterministic filter.
**Delivers:** `engine/win_condition.py` (`WinConditionClassifier` with primary + secondary archetype, timing window, key hero identification, confidence score); `_build_team_strategy_section()` in ContextBuilder; win condition framing instructions in system prompt (~150 tokens); optional `WinCondition` field on `RecommendResponse`; frontend strategy banner above item timeline.
**Avoids:** P7 (classification tunnel vision — win condition is a suggestion to Claude, not an item filter; re-evaluate requests can change framing when game state changes; enemy composition included in analysis; low-confidence drafts defer entirely to Claude without a classification label).

### Phase Ordering Rationale

- Phase 1 is a hard prerequisite: ability data and timing data must be in DataCache before counter-item rules or timing benchmarks can fire.
- Phases 2 and 3 are ordered by cost-to-benefit: ability-driven rules add zero LLM token cost and fire on every request; timing benchmarks add ~100-200 tokens to the user message and require careful token budget management.
- Phase 4 is placed after Phases 2-3 because schema changes require frontend coordination and benefit from Phase 2's ability context for richer component reasoning.
- Phase 5 requires no new data pipeline work but is the most judgment-intensive to validate; it is safest to ship last when the rest of the intelligence layers are proven.
- All phases add only optional fields to the response schema (`build_path`, `win_condition`) — frontend backward compatibility is guaranteed by design and no forced simultaneous frontend+backend deploy is required.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Counter-Item Rules):** The boundary between which counters belong as deterministic rules vs. LLM reasoning is judgment-intensive. The 4-6 new rules identified are the clear-cut cases. A phase planning session should audit the existing 18 hardcoded rules to identify which are candidates for ability-driven migration vs. which should remain as hero ID lists because they address meta-level behaviors not captured in ability properties.
- **Phase 3 (Timing Benchmarks):** The GSI-timing integration path (live comparison of game clock vs. benchmark window) requires explicit ResponseCache key design. Adding exact gold or game time to the cache key will obliterate hit rates. The coarse-grained gold bracket approach (0-2K, 2K-5K, 5K-10K, 10K+) is the proposed solution but needs explicit design and validation during phase planning before implementation.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Data Foundation):** All three new endpoints are verified live with confirmed response schemas. The DataCache extension follows the existing `HeroCached`/`ItemCached` frozen dataclass pattern exactly. Standard SQLAlchemy table additions; no migration complexity on existing tables.
- **Phase 4 (Build Path):** The `ItemCached.components` data is already in production since v1. `BuildPathResolver` is a BFS/DFS over nested lists — a well-understood algorithm with no external dependencies or novel integration patterns.
- **Phase 5 (Win Condition):** `HeroCached.roles` (OpenDota tags: Carry, Support, Nuker, Disabler, Pusher, Initiator, etc.) is already in cache. Classification rules are a role-tag counting exercise; the LLM does the nuanced reasoning.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All three new OpenDota endpoints verified live with confirmed response schemas. Zero new dependencies confirmed against current `requirements.txt`. Existing SQLAlchemy/DataCache patterns proven across v1-v3. |
| Features | HIGH | Timing endpoint data structure confirmed with real Anti-Mage Battle Fury data (7 time buckets, string-typed games/wins). Ability metadata fields (behavior, bkbpierce, dispellable, dmg_type) verified against real hero abilities including Enigma Black Hole, Witch Doctor Death Ward, CM Freezing Field. Build path data (`ItemCached.components`) already in production. |
| Architecture | HIGH | Based on direct codebase reading of all relevant backend source files. Integration points are concrete (specific method names, file paths, class signatures). All four features follow the same data-flow pattern as existing matchup and popularity data pipelines. |
| Pitfalls | HIGH | Prompt caching token threshold confirmed from Anthropic documentation (Haiku 4.5: 4,096 minimum). Rate limits verified from OpenDota documentation and confirmed via live testing. Three-cache coherence risk identified from direct `refresh.py` code analysis (lines 121-134). `games`/`wins` string-not-int issue confirmed from go-opendota struct definition. |

**Overall confidence:** HIGH

### Gaps to Address

- **Win condition classification accuracy for ambiguous drafts:** The hero-role-tag counting approach works cleanly for well-defined compositions but may misclassify hybrid drafts. During Phase 5 planning, define the confidence threshold below which the classifier defers entirely to Claude without providing a classification label to avoid misleading framing.
- **Minimum sample size for timing benchmarks:** OpenDota itemTimings data thins out for heroes with low pick rates. The system needs a minimum game-count threshold (suggested: 50 games per time bucket) below which timing data is treated as absent rather than displayed. Define this threshold during Phase 3 planning.
- **Full enemy team in `RecommendRequest` for win condition:** The current schema sends `lane_opponents` but not all 5 enemy heroes. Win condition framing needs all 10 heroes for accurate classification. During Phase 5 planning, determine whether to expand the request schema (preferred) or approximate from available data.
- **ResponseCache key design for GSI context:** Adding game clock or exact gold to the cache key will destroy hit rates. The coarse-grained gold bracket approach is the proposed solution but has not been validated against real GSI refresh patterns (1Hz tick rate, 30s auto-refresh cycle). Design and validate this explicitly during Phase 3 planning before implementation.

## Sources

### Primary (HIGH confidence)
- [OpenDota API](https://docs.opendota.com/) — canonical reference; `/scenarios/itemTimings`, `/constants/abilities`, `/constants/hero_abilities` all verified live with confirmed response schemas
- [odota/dotaconstants](https://github.com/odota/dotaconstants) — `build/abilities.json` and `build/hero_abilities.json` schema reference; source data for OpenDota constants endpoints
- [Anthropic Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — token thresholds (Haiku 4.5: 4,096 minimum), 5-minute cache TTL, breakpoint strategy
- Direct codebase analysis — all backend source files: `rules.py`, `cache.py`, `system_prompt.py`, `recommender.py`, `context_builder.py`, `llm.py`, `refresh.py`, `schemas.py`, `models.py`, `opendota_client.py`

### Secondary (MEDIUM confidence)
- [go-opendota package](https://pkg.go.dev/github.com/jasonodonnell/go-opendota) — confirms `games`/`wins` as string fields in itemTimings response; confirms ItemTimings struct definition
- [OpenDota rate limit blog post](https://blog.opendota.com/2018/04/17/changes-to-the-api/) — 50,000 calls/month, 60 req/min; limits verified still active via live testing
- [STRATZ item timings methodology](https://medium.com/stratz/dota-2-item-timings-22d2dbd76bc4) — win rate gradient analysis, central 69% purchase window approach; informs how to present timing data as ranges
- [BSJ coaching articles](https://bsjdota.com/blog/) — five win condition archetypes (hard carry, push, pickoff, teamfight, split push); emphasis on mid-game adaptation and win condition shifts
- [DotaCoach.gg features](https://dotacoach.gg/en/app/features) — competitor analysis: counter items per enemy, phase-based item suggestions; Overwolf overlay approach

### Tertiary (LOW confidence)
- [Steam Community team composition guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2395798524) — archetype classification heuristics for deterministic rules
- [Hybrid LLM+rules system literature](https://medium.com/@ceciliabonucchi/bridging-intelligence-the-next-evolution-in-ai-with-hybrid-llm-and-rule-based-systems-db0d89998c6d) — consistency challenges between deterministic and LLM layers; confirms contradiction risk pattern

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
