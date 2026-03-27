# Pitfalls Research

**Domain:** Adding coaching intelligence (timing benchmarks, counter-item depth, build paths, win condition framing) to an existing hybrid rules+LLM Dota 2 item advisor
**Researched:** 2026-03-27
**Confidence:** HIGH (based on codebase analysis, OpenDota API documentation, Anthropic prompt caching docs, and Dota 2 domain knowledge)

## Critical Pitfalls

### Pitfall 1: System Prompt Bloat Breaking Cache Economics

**What goes wrong:**
The system prompt is currently ~13,326 chars (~3,300 tokens). Claude Haiku 4.5 requires a minimum of 4,096 tokens for prompt caching to activate. Adding four new feature areas (timing benchmarks, ability counters, build paths, win conditions) to the system prompt will push it well past 5,000+ tokens -- each new section with examples adds 300-800 tokens. The prompt is currently right at the caching threshold. Growing it carelessly means every new instruction section gets cached but the per-request cost grows linearly with prompt size. Worse, if someone restructures the prompt and the prefix changes, every request becomes a cache write instead of a cache read, multiplying input token costs by 1.25x.

**Why it happens:**
Each v4.0 feature seems to need its own instructions in the system prompt: "when timing data is available, reference it," "evaluate abilities for counter-item logic," "recommend components in order," "frame overall_strategy around win condition." Developers add these incrementally without measuring the token delta or testing cache hit rates. The 5-minute cache TTL means even small changes to the prompt prefix cause expensive cache misses.

**How to avoid:**
1. Measure the current system prompt token count precisely before starting (use `anthropic.count_tokens` or tiktoken approximation).
2. Set a budget: the system prompt should not exceed ~5,000 tokens (currently ~3,300). That leaves ~1,700 tokens for all v4.0 additions.
3. Put dynamic data (timing benchmarks, ability descriptions, component lists) in the USER message, not the system prompt. The system prompt should contain only static reasoning instructions.
4. New system prompt sections should be directives ("If timing data is present, compare to benchmark and flag early/late"), not data ("Battle Fury typical timing: 14 min"). Data goes in user message.
5. After all additions, verify cache hit rate in production logs by checking `cache_read_input_tokens` vs `cache_creation_input_tokens` in Claude API responses.

**Warning signs:**
- System prompt exceeds 5,500 tokens after v4.0 additions.
- `cache_creation_input_tokens` appears on >20% of requests (should be <5% after warmup).
- Claude API latency increases noticeably (cache misses are slower).
- Per-request cost jumps without corresponding quality improvement.

**Phase to address:**
First phase -- establish the prompt architecture before any feature work. Define what goes in system prompt vs. user message for all four features upfront.

---

### Pitfall 2: OpenDota Scenarios/itemTimings Rate Limit Exhaustion

**What goes wrong:**
The `/scenarios/itemTimings` endpoint returns timing data as an array of `{hero_id, item, time, games, wins}` objects. To populate benchmarks, you might naively query per hero+item pair. For 124+ heroes with 10-20 items each, that is 1,240-2,480 API calls just for initial population. OpenDota free tier allows 50,000 calls/month and 60 requests/minute. The existing system already uses calls for matchup data (`/heroes/{id}/matchups`) and item popularity (`/heroes/{id}/itemPopularity`) -- adding timing queries could exhaust the monthly budget within a single full-refresh cycle. Also note: the `games` and `wins` fields in the response are strings, not integers, which will cause silent parsing bugs if treated as numeric.

**Why it happens:**
The itemTimings endpoint accepts optional `hero_id` and `item` filters. Developers assume they need to query per hero+item pair for precision. In reality, querying with just `hero_id` (omitting `item`) returns all item timings for that hero in a single call. But even 124 calls per refresh cycle adds 3,720 calls/month (daily refresh) on top of existing matchup and popularity calls.

**How to avoid:**
1. Query `/scenarios/itemTimings?hero_id={id}` (without item filter) to get all item timings for one hero in a single call. This brings it down to 124 calls for full coverage.
2. Cache timing data aggressively in SQLite with a 48-hour TTL. Timing benchmarks are statistical aggregates and change slowly -- daily refresh is sufficient.
3. Lazy-load on first request: only fetch timing data for heroes that are actually requested, not the entire pool on startup. Most games involve 10 heroes.
4. Budget API calls: add a monthly counter to DataRefreshLog. Halt timing fetches if approaching 40,000 calls (leave buffer for matchup/popularity data).
5. Parse `games` and `wins` as strings and cast to int explicitly in application code.

**Warning signs:**
- OpenDota returns HTTP 429 responses during refresh cycle.
- Monthly API call count approaches 40,000 before month-end.
- Timing data is stale for >7 days because refresh keeps failing.
- Background refresh tasks pile up due to rate limiting.
- Type errors from treating `games`/`wins` as integers directly.

**Phase to address:**
Timing benchmarks phase -- design the data pipeline before building the benchmark comparison logic.

---

### Pitfall 3: Three-Cache Coherence Breakage with New Data Layers

**What goes wrong:**
The system already has a delicate three-cache coherence protocol: DataCache (frozen dataclasses) -> RulesEngine (consumes DataCache via constructor injection) -> ResponseCache (SHA-256 keyed, 5-min TTL). The refresh pipeline in `refresh.py` invalidates them in this exact order (lines 121-134). Adding timing benchmark data and ability data creates two new data layers that must participate in this same invalidation chain. If timing data refreshes but ResponseCache is not cleared, cached responses contain stale timing comparisons. If ability data refreshes but the rules engine's counter-item rules still reference old ability metadata, rules contradict the prompt context.

**Why it happens:**
The current coherence protocol is implicit -- it lives in `refresh_all_data()` as sequential code, not as a formal invalidation contract. New developers adding timing data will create a separate cache (e.g., `TimingCache`) and forget to wire it into the refresh pipeline. Or they wire it in but in the wrong order (ResponseCache clears before TimingCache updates, creating a window where new responses are built from stale timing data and then cached).

**How to avoid:**
1. Extend DataCache to hold timing and ability data alongside heroes and items. One cache, one refresh, one atomic swap. Do not create separate TimingCache or AbilityCache singletons.
2. If separate caches are unavoidable, formalize the invalidation order as a named method: `invalidate_all_caches()` that runs in guaranteed sequence: DataCache -> RulesEngine sees new data via reference -> ResponseCache.clear().
3. Add an integration test that verifies: after `refresh_all_data()`, ResponseCache is empty AND DataCache contains fresh data AND timing data matches DB state.
4. Add a version counter to DataCache. ResponseCache entries include the version at creation time. On read, reject entries with stale versions.

**Warning signs:**
- Users see timing benchmarks that reference item costs or names that don't match current game data.
- Rules engine recommends counter-items that contradict the LLM's ability-aware reasoning.
- ResponseCache hit rate stays high after a data refresh (should drop to 0% briefly).
- "Ghost" recommendations appear -- items that were valid in old data but no longer exist.

**Phase to address:**
First phase -- extend the DataCache architecture before adding any new data types.

---

### Pitfall 4: Rules Engine and LLM Contradicting Each Other on Counter-Items

**What goes wrong:**
Currently, the rules engine makes broad hero-level counter-recommendations (Spirit Vessel vs "high regen heroes" like Alchemist). The v4.0 counter-item depth feature adds ability-specific logic (Eul's vs channeled ults, Lotus Orb vs single-target spells). If the rules engine recommends Spirit Vessel against Alchemist (hero-level counter) while the LLM's ability-aware reasoning recommends Shiva's Guard instead (because it counters Chemical Rage's attack speed AND healing), the user sees two anti-heal items in the same build. The merge logic in `HybridRecommender._merge()` deduplicates by `item_id` (lines 209-214), but cannot detect semantic conflicts between different items targeting the same threat.

**Why it happens:**
The rules engine and LLM operate at different abstraction levels. Rules say "this hero is a problem, buy this item." The LLM says "this hero's specific ability is a problem, buy this different item." Neither system knows the strategic intent behind the other's recommendation. The current "Already Recommended" section in the user message (built by `_build_rules_lines()`) passes item name + reasoning text, but the reasoning doesn't tag which threat it addresses.

**How to avoid:**
1. Tag RuleResult with a `counter_target` field: which enemy hero/ability this rule counters. Pass this to the LLM: "Spirit Vessel (counters Alchemist's healing -- do not duplicate anti-heal)."
2. In the system prompt, add: "If the rules engine already counters a specific threat, recommend items that address OTHER threats or complement the existing counter."
3. For ability-specific counters that are deterministic enough (Eul's vs Witch Doctor Death Ward, BKB vs Enigma Black Hole), add them to the rules engine directly. Reserve the LLM for nuanced multi-factor reasoning where a simple lookup is insufficient.
4. Test for conflicts: create test cases where rules produce a counter-item, verify LLM output complements rather than contradicts.

**Warning signs:**
- Two items in the same build targeting the same enemy hero with different reasoning.
- User message says "Already Recommended: Spirit Vessel (counters healing)" but LLM still recommends Shiva's Guard "to counter Alchemist's healing."
- Rules and LLM recommend overlapping categories (two anti-heal items, two break items) in the same build.

**Phase to address:**
Counter-item depth phase -- redesign the rules-to-LLM communication protocol before adding new counter rules.

---

### Pitfall 5: Timing Benchmarks Becoming Prescriptive Instead of Descriptive

**What goes wrong:**
OpenDota timing data shows statistical purchase times across skill brackets. Telling a player "your Battlefury should be done by 14 minutes" when that benchmark comes from aggregate data across all brackets creates unrealistic expectations. The player might rush Battlefury without boots to hit the timing, or feel discouraged when they consistently miss it. Worse, the `/scenarios/itemTimings` endpoint returns time buckets with games/wins counts -- interpreting "items purchased at time X had Y% win rate" as "you should buy item at time X" is a fundamental misuse of correlational data.

**Why it happens:**
Raw statistical benchmarks feel authoritative and are easy to display. Developers treat average timing as a target rather than a baseline. The OpenDota endpoint provides time + games + wins (enabling win rate calculation per time bucket), but the temptation is to distill this into a single "target time" number that loses all nuance.

**How to avoid:**
1. Present benchmarks as ranges with win rate correlation: "BKB completed by 22 min: 58% WR. After 28 min: 44% WR." This conveys urgency without being prescriptive.
2. Contextualize with game state: if `lane_result` is "lost", shift timing expectations by 3-5 minutes. If "won", tighten them.
3. In the system prompt, frame benchmarks as: "Use timing data to convey urgency, not as rigid targets. A player behind schedule should still buy the right item even if late."
4. Never surface "you're behind schedule" without an actionable follow-up for what to do about it.
5. Group time buckets into ranges (early/on-time/late) rather than showing a single minute target.

**Warning signs:**
- Benchmarks displayed as single numbers ("14:00") instead of ranges ("12-18 min").
- No adjustment for lane result, role, or game state in timing display.
- Users report feeling stressed/discouraged by timing pressure.
- LLM reasoning says "you need X by Y minutes" without contextual caveats.

**Phase to address:**
Timing benchmarks phase -- define the presentation philosophy before implementing the data pipeline.

---

### Pitfall 6: Component-Level Build Path Ordering Without Game State Awareness

**What goes wrong:**
Recommending "buy Ogre Axe before Mithril Hammer for BKB" is correct in isolation, but wrong if the player already has 2,150 gold and an open slot (Mithril Hammer gives more immediate combat value at that gold threshold). Build path ordering is context-dependent: gold available, inventory slots remaining, whether the player is actively fighting or farming. A static "always buy component A before B" recommendation ignores the dynamic game state.

**Why it happens:**
Build path ordering is intellectually satisfying to precompute ("always buy the stats component first for lane") but practically depends on factors that change every 30 seconds. Developers create a static ordering table per item and forget that current gold, current inventory, and game tempo all matter.

**How to avoid:**
1. Build path ordering should be LLM-driven, not rules-driven. The LLM can reason about "you have 1,200 gold and need survivability, so buy Ogre Axe first for the +10 STR."
2. In the user message, include current gold (from GSI when available) and purchased components. Let the LLM reason about ordering dynamically.
3. For rules-only fallback, use a simple heuristic: cheapest useful component first (maximizes chance of buying something before dying).
4. Do NOT precompute static build orders for all items. Focus on 10-15 high-impact items where component ordering actually matters (BKB, Manta, Sange & Yasha, Diffusal Blade, Orchid Malevolence, Eye of Skadi).
5. Use the Item model's existing `components` field (already in DataCache as `ItemCached.components`) to provide the component list in the user message.

**Warning signs:**
- Static build path tables covering 50+ items (most items don't need ordering guidance).
- Build path recommendations that don't change based on game state or gold available.
- Component ordering contradicts what the player can actually afford right now.
- Build path suggestions for items with only 1-2 components (where ordering is trivial).

**Phase to address:**
Build path intelligence phase -- define scope narrowly (high-impact items only) and delegate ordering logic to the LLM with game state context.

---

### Pitfall 7: Win Condition Classification Overfitting to Draft, Ignoring Game Evolution

**What goes wrong:**
Classifying a team as "teamfight-heavy" at draft time and then framing every item recommendation around "you need teamfight items" ignores how the game actually develops. A draft that looks like a teamfight composition might need to split-push because the enemy's teamfight is stronger. A "4-protect-1" draft might need to fight early because the carry got shut down. Static win condition classification at draft creates tunnel vision in recommendations.

**Why it happens:**
Win condition classification based on hero roles/abilities is a clean system to build. Developers create a lookup: "If team has Enigma + Dark Seer + Invoker -> teamfight." But actual win conditions depend on who's ahead, enemy item timings, and which heroes are online. BSJ (8K+ MMR coach) identifies five archetypes -- hard carry, push, pickoff, teamfight, split push -- but emphasizes these shift mid-game based on execution.

**How to avoid:**
1. Win condition framing should be a suggestion in `overall_strategy`, NOT a filter on item recommendations. "Your team's natural win condition is teamfight around 25-30 min" is guidance; "only recommend teamfight items" is tunnel vision.
2. Re-evaluate win condition on re-evaluate requests: if mid-game state shows the carry behind, shift framing from "protect carry to late game" to "create space and extend."
3. Classify as primary + fallback: "Primary: teamfight at 25 min. Fallback if behind: split push to buy time."
4. Let the LLM handle win condition reasoning. Provide team composition data (hero names + roles) and let it reason about macro strategy. Do not hardcode a classification lookup table.
5. Include enemy composition in win condition analysis. Your win condition partially depends on what the enemy wants to do.

**Warning signs:**
- Win condition label assigned once at draft and never updated.
- Item recommendations filtered or biased by win condition (removes valid situational items).
- `overall_strategy` reads like a generic strategy article instead of a matchup-specific game plan.
- No mechanism to re-evaluate win condition when game state changes.

**Phase to address:**
Win condition framing phase -- design as an LLM-reasoned feature that adapts to game state, not as a deterministic classification.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding ability counter-items in rules engine | Instant, no API call, deterministic | Every Dota patch that changes abilities requires manual rule updates. 124 heroes x 4 abilities = 496 potential mappings. | Only for the 10-15 most iconic and stable counters (BKB vs Black Hole, Eul's vs Death Ward, etc.) |
| Putting timing benchmark data in system prompt | Simpler than user message construction | Inflates system prompt beyond cache-optimal size, changes per hero break cache hits | Never -- timing data is per-request context, belongs in user message |
| Static win condition lookup table | Fast classification, no LLM call needed | Stale after Dota patches change hero meta, ignores game state evolution | Only as a seed/hint to the LLM, never as the final classification |
| Fetching all timing data on startup | Complete data availability immediately | 124+ API calls on every restart, slow startup, rate limit risk | Only if lazy-loading proves too slow for first-request UX |
| Duplicating component data into a separate build path table | Easier to query component orders | Two sources of truth for item components. When Dota patches change recipes, both must update. | Never -- use existing `ItemCached.components` from DataCache |
| Adding new Pydantic fields to existing schemas without versioning | Quick feature addition | Frontend and backend must deploy simultaneously; old cached responses break validation | Only during v4.0 development while frontend/backend are co-deployed |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenDota `/scenarios/itemTimings` | Querying per hero+item pair (N*M calls). Also, `games` and `wins` fields are strings not integers -- will cause validation errors if parsed as int directly. | Query per hero (omit item filter) for one call per hero. Parse `games`/`wins` as strings, cast to int in application code. |
| OpenDota ability data | Assuming `/constants/abilities` is sufficient. It has ability details (dmg_type, behavior, cd, mc, attrib) but NOT which hero owns which ability. `/constants/hero_abilities` maps hero -> ability keys. Must join both. | Fetch both `/constants/abilities` and `/constants/hero_abilities`, join in application code, cache the merged result in DataCache. |
| Claude API structured output | Adding new fields to LLM_OUTPUT_SCHEMA (e.g., `timing_comparison`, `build_order`, `win_condition`) without updating the hand-crafted inline JSON schema in `schemas.py`. Pydantic model and JSON schema drift apart silently. | Update both `LLMRecommendation` Pydantic model AND `LLM_OUTPUT_SCHEMA` dict simultaneously. Add automated test that validates schema matches model. |
| ResponseCache SHA-256 keying | New context (current gold, game time from GSI) not included in `RecommendRequest` but passed via other means -> cache returns stale results that ignore the new context. | All context that affects recommendations MUST be fields on `RecommendRequest` so the SHA-256 hash changes when context changes. |
| DataCache atomic swap | Adding new dict fields (`_timing_data`, `_ability_data`) to DataCache but not swapping them atomically with heroes/items. A request reads new hero data with old timing data during the swap window. | Build ALL new dicts first, then swap ALL references in a single code block. Mirror the existing pattern at `cache.py` lines 169-174. |
| Item components field | `ItemCached.components` is a tuple of internal_name strings (e.g., `("ogre_axe", "mithril_hammer", "recipe_bkb")`). These are internal names, not display names and not item IDs. Must resolve through DataCache to get IDs and display names. | Add a `resolve_components(item_id)` method to DataCache that returns component details (id, name, cost) from the component internal names. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| User message token explosion from timing + ability + component data | Claude API latency increases from 2s to 5s+. Token costs double. Possible timeout within 45s window for complex matchups. | Budget user message at ~2,000 tokens max. Timing data: top 5 items only. Ability data: only abilities relevant to counter-items. Component data: only for recommended items, not entire catalog. | When all 4 features include full data for 5 enemies x 4 abilities each + 10 items with timing + 6 items with components |
| N+1 API calls for timing data during recommendation | First request for a new hero triggers a blocking API call for 1-3 seconds on top of existing matchup + popularity calls | Pre-populate timing data for frequently-played heroes during daily refresh. Lazy-load the rest with stale-while-revalidate pattern (same as matchup data). | When lazy-loading timing data for every unique hero in real-time requests |
| ResponseCache invalidation frequency from GSI context | Adding `game_time` or `current_gold` to `RecommendRequest` means every request at a different gold level is a cache miss. Hit rate drops from ~30% to <5%. | Only include coarse-grained context in cache key: gold_bracket (0-2K, 2K-5K, 5K-10K, 10K+) instead of exact gold. Or: disable ResponseCache entirely for GSI-driven auto-refresh requests. | When GSI auto-refresh sends requests every 30s with changing gold values |
| Ability data bloating DataCache memory | 124 heroes x 4-6 abilities x ~500 bytes per ability (name, desc, dmg_type, cd, mc, attrib). Total ~300-400KB. | Acceptable for single-server deployment. Store only counter-relevant fields (name, dmg_type, behavior: channeled/passive, key tags like "heal", "stun", "silence"). Omit full attrib arrays. | Not a real concern at this deployment scale (Unraid single server) |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing raw OpenDota API key in timing data error messages | API key leaks to frontend via error responses containing raw exception messages | Sanitize all error messages before returning to frontend. Already handled for existing endpoints but must be verified for new timing data endpoints. |
| Ability description injection via OpenDota constants | Corrupted ability descriptions from dotaconstants could inject unexpected content into Claude prompts | Sanitize ability descriptions: strip HTML, limit length to 200 chars, reject entries with suspicious patterns (URLs, code blocks, instruction-like text). |
| Unrestricted scenarios API access from user-triggered hero changes | A user rapidly changing heroes triggers burst OpenDota API calls for timing data, potentially exhausting rate limits for all users | Debounce timing data fetches (500ms minimum). Use lazy-load with DB cache, never fetch from API directly on user action. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Timing benchmarks displayed as rigid deadlines | Player feels stressed; might rush items ignoring game state; tilts when behind | Show as ranges with win rate correlation: "BKB by 20-25 min (56% WR). After 30 min (44% WR). You're at 22 min -- on track." |
| Component build order for every item | Information overload. Most items have 2-3 components where order barely matters. | Only show ordering guidance for items where it genuinely matters (BKB, Manta, S&Y, Diffusal). Omit for trivial component trees. |
| Win condition label with no actionable connection to items | "Your win condition: Teamfight at 25 min" is informative but doesn't tell the player what to buy differently | Connect to item urgency: "Teamfight spike at 25 min. Completing BKB before then lets you frontline during your power window." |
| Ability counter-items without naming the ability | "Buy Eul's to counter channeled ults" -- which ult? From which hero? | Always name hero AND ability: "Eul's counters Witch Doctor's Death Ward (3.5s channel). Cast immediately when you see the animation." |
| Cluttering the item timeline with too many new visual elements | Timing badges + component arrows + win condition banner + counter-item tags = visual noise drowning out the actual item recommendations | Introduce ONE new visual element per phase. Phase 1: timing info in reasoning text only (no new UI). Phase 2: counter-item tags. Phase 3: component hints in tooltip. Phase 4: win condition in overall_strategy. |

## "Looks Done But Isn't" Checklist

- [ ] **Timing benchmarks:** Often missing game state adjustment -- verify benchmarks shift when `lane_result` is "lost" vs "won"
- [ ] **Timing benchmarks:** Often missing fallback for low-data heroes -- verify graceful degradation when OpenDota returns <100 games for a hero+item pair (show nothing rather than misleading stats)
- [ ] **Counter-item rules:** Often missing the "already countered" check -- verify that if rules engine recommends a counter, the LLM doesn't recommend a second conflicting counter for the same threat
- [ ] **Counter-item rules:** Often missing patch resilience -- verify that if an ability is reworked (changes damage type, loses channel), the counter rule is invalidated or updated
- [ ] **Build path ordering:** Often missing purchased-component awareness -- verify that if the player already bought Ogre Axe (marked purchased), the build path skips to the next component
- [ ] **Build path ordering:** Often missing the "just buy the recipe" case -- verify that when all components are purchased, the recommendation says "complete the item (buy recipe for Xg)"
- [ ] **Win condition framing:** Often missing re-evaluation -- verify that a re-evaluate request with different `lane_result` or `damage_profile` can change the win condition framing
- [ ] **Win condition framing:** Often missing enemy composition -- verify win condition considers BOTH allied AND enemy team composition
- [ ] **Schema updates:** Often missing frontend sync -- verify new response fields (`timing_data`, `component_order`, `win_condition`) are handled by frontend even when null/missing (backward compatibility)
- [ ] **Cache invalidation:** Often missing ResponseCache clear after timing/ability data refresh -- verify `refresh_all_data()` clears ResponseCache after ALL new data layers update
- [ ] **LLM_OUTPUT_SCHEMA sync:** Often missing schema update -- verify hand-crafted JSON schema in `schemas.py` matches `LLMRecommendation` model after adding new output fields

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| System prompt too large, cache economics degraded (P1) | LOW | Extract dynamic data to user message sections. Single refactor session. No schema changes needed. |
| OpenDota rate limit exhausted mid-month (P2) | LOW | Switch to cached-only mode for timing data. Serve stale benchmarks until month resets. No user-facing breakage -- just stale stats. |
| Three-cache coherence broken (P3) | MEDIUM | Add version counter to DataCache. ResponseCache rejects entries with stale versions. Requires code changes in cache.py + recommender.py + testing. |
| Rules/LLM counter-item contradiction (P4) | MEDIUM | Add `counter_target` field to RuleResult. Update `_build_rules_lines()` in context_builder.py to pass it. Update system prompt with dedup guidance. |
| Timing benchmarks demoralizing users (P5) | LOW | Change display from target to range with win rate. Primarily a presentation change in reasoning text and frontend. |
| Build path ordering ignoring game state (P6) | MEDIUM | Redesign as LLM-driven context. Requires user message changes + system prompt update. Rules-only fallback needs cheapest-first heuristic. |
| Win condition classification stale after draft (P7) | LOW | Move to LLM-reasoned win condition. Already the recommended approach -- stop hardcoding and let LLM adapt per request. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| System prompt bloat (P1) | Phase 1: Prompt architecture | Token count measured before/after. System prompt stays under 5,000 tokens. Cache hit rate >90% in steady state. |
| OpenDota rate limit (P2) | Timing benchmarks phase | Monthly API call budget tracked. Timing data fetched per-hero not per-hero-per-item. Integration test for 429 handling. |
| Three-cache coherence (P3) | Phase 1: DataCache extension | Integration test: refresh -> all caches coherent. ResponseCache empty after refresh. |
| Rules/LLM contradiction (P4) | Counter-item depth phase | Test: rules produce counter -> LLM complements, not contradicts. `counter_target` present in RuleResult. |
| Prescriptive timings (P5) | Timing benchmarks phase | Benchmarks displayed as ranges. Win rate shown. Lane result adjusts expectations. |
| Static build paths (P6) | Build path phase | Component ordering varies with game state in LLM output. No static ordering table for >15 items. |
| Stale win condition (P7) | Win condition phase | Re-evaluate changes win condition when game state differs. LLM generates framing, no hardcoded lookup. |
| User message token explosion | Phase 1: Prompt architecture | User message stays under 2,000 tokens. Timing/ability/component data trimmed to essentials per request. |
| LLM_OUTPUT_SCHEMA drift | Every phase adding new response fields | Automated test: hand-crafted schema validates against LLMRecommendation model. |
| ResponseCache over-invalidation from GSI | Timing/GSI integration | Cache key uses coarse-grained gold brackets. Hit rate monitored. |

## Sources

- [Anthropic Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- Token thresholds per model (Haiku 4.5: 4,096 minimum), cache TTL (5 min default), breakpoint strategy
- [go-opendota package](https://pkg.go.dev/github.com/jasonodonnell/go-opendota) -- ItemTimings struct definition: `{hero_id: int, item: string, time: int, games: string, wins: string}`
- [OpenDota API](https://docs.opendota.com/) -- Rate limits: 50,000 calls/month free, 60 req/min. Scenarios endpoint at `/scenarios/itemTimings`
- [odota/dotaconstants](https://github.com/odota/dotaconstants) -- `abilities.json` structure (dname, behavior, dmg_type, dmg, cd, mc, attrib), `hero_abilities.json` for hero-to-ability mapping
- [BSJ: How to Identify Your Win Condition](https://bsjdota.com/blog/how-to-identify-your-win-condition-in-every-game-of-dota-2/) -- Five archetypes: hard carry, push, pickoff, teamfight, split push
- [BSJ: Common Mistakes in Dota 2](https://bsjdota.com/blog/common-lesser-known-mistakes-in-dota-2/) -- Item build ordering mistakes, timing variance by bracket
- [Hybrid Rule-Based and LLM Systems](https://medium.com/@ceciliabonucchi/bridging-intelligence-the-next-evolution-in-ai-with-hybrid-llm-and-rule-based-systems-db0d89998c6d) -- Consistency challenges: hallucinations, contradictions, sycophancy in hybrid architectures
- [LLM Token Optimization](https://redis.io/blog/llm-token-optimization-speed-up-apps/) -- System prompt as major cost driver, prompt creep from 500 to 2,000 tokens over time
- Codebase analysis: `rules.py` (18 rules, hero-level counters), `cache.py` (DataCache with frozen dataclasses, 12 lookup methods), `system_prompt.py` (~13,326 chars), `recommender.py` (merge/dedup/validate pipeline), `context_builder.py` (user message assembly, ~1,500 token target), `llm.py` (Haiku 4.5, 45s timeout, prompt-instructed JSON), `refresh.py` (three-cache invalidation chain), `schemas.py` (hand-crafted LLM_OUTPUT_SCHEMA)

---
*Pitfalls research for: v4.0 Coaching Intelligence features added to existing Prismlab hybrid rules+LLM architecture*
*Researched: 2026-03-27*
