# Feature Research: v4.0 Coaching Intelligence

**Domain:** Item timing benchmarks, ability-specific counter-itemization, build path ordering, win condition framing
**Researched:** 2026-03-27
**Confidence:** HIGH (timing data confirmed via live API calls, ability data structure verified, existing system thoroughly audited)

---

## Feature Landscape

### Category 1: Timing Benchmarks

#### Table Stakes

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Per-item timing benchmark display (good/average/late) | Every major Dota stats site (STRATZ, Dotabuff, Dota2ProTracker) shows timing windows. Players think in "I need BKB by 20 min" terms. Without benchmarks, item recommendations feel like a shopping list, not coaching | MEDIUM | OpenDota `/api/scenarios/itemTimings` endpoint, new `ItemTimingBenchmark` DB model, data pipeline addition, schema changes to `RecommendPhase` and `ItemRecommendation` | **Verified**: endpoint returns `{hero_id, item, time (seconds), games, wins}` bucketed in ~2-5 minute intervals. Anti-Mage Battle Fury data shows 7 time buckets from 450s to 1800s with win rates declining from 100% (tiny sample at 7.5min) to 63% at 15min to 40% at 20min to 0% at 30min. Win rate gradient is the key metric: "each minute past 15:00 costs ~3% win rate" |
| Urgency signal on recommended items | Player needs to know "buy this NOW" vs "buy this when convenient." Currently all items in a phase are presented equally. A simple urgency indicator (timing-sensitive vs flexible) is the minimum coaching signal | LOW | Timing benchmark data feeding into rules engine and/or system prompt, frontend urgency badge on ItemCard | Derive from timing gradient: items with steep win rate falloff (>2%/min) are timing-critical. Items with flat gradients are flexible. Surface as a visual indicator per item |
| Timing data in system prompt context | Claude already receives item popularity data per hero. Adding timing benchmarks ("BKB optimal: 18-22 min, win rate drops 3%/min after") gives Claude the data to write coaching-quality reasoning like "You need BKB before 20 min or you lose the timing window against their lockdown" | LOW | context_builder.py additions to inject timing data into Claude user message | Piggybacks on existing popularity section pattern. ~50-100 tokens of additional context per hero |

#### Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Live timing comparison via GSI | During a live game, compare actual gold/items against expected timing benchmarks at the current game clock. "You should have BKB by now -- you're 3 minutes late, prioritize it" | MEDIUM | GSI store (game_clock, gold, items_inventory), timing benchmark data, frontend comparison logic | GSI already provides `game_clock`, `gold`, `net_worth`, and `items_inventory`. The comparison logic is: (1) identify which core items the player hasn't purchased yet, (2) check if current game clock exceeds the optimal purchase window, (3) surface urgency. This is a natural extension of the existing auto-refresh trigger system |
| Timing-aware re-evaluation weighting | When a player is behind on a timing window, the re-evaluate call should deprioritize "ideal" items and shift toward cheaper power spike alternatives. "You missed the Radiance timing -- pivot to fighting items" | HIGH | Modified system prompt context that communicates timing misses, potentially new rules for common timing pivots (e.g., if BF timing missed on AM, suggest Maelstrom) | Requires the system prompt to receive "player is X minutes behind on Y item" context. Claude can reason about this, but the data pipeline needs to calculate and inject it |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Prescriptive timing targets ("buy by exactly 14:32") | Feels precise and "pro" | False precision. Timing benchmarks are population averages across all skill brackets. Individual game variance (lane result, rotations, deaths) makes exact targets misleading. A player who lost lane badly and hits BKB at 23 min might still be ahead of curve for their game state | Show timing windows as ranges ("good: 15-18 min, average: 18-22 min, late: 22+ min") with context about what affects timing. Use win rate gradients, not exact targets |
| Per-match-ID timing comparison ("your last 10 games") | Would let players track their improvement | Requires Steam login, Dota 2 match history access, and match replay parsing -- massive scope expansion. Not aligned with v4.0 coaching intelligence goals | Defer entirely. Focus on population-level benchmarks that help in the current game |

---

### Category 2: Counter-Item Intelligence (Ability-Specific)

#### Table Stakes

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Ability-aware counter-item rules | Current rules engine has 18 rules that operate on hero ID lists (e.g., "Spirit Vessel vs Alchemist/Huskar/etc"). This is a flat mapping that misses the WHY. A player fighting Enigma needs Eul's to cancel Black Hole, but the current system has no concept of "channeled ultimate" as a counter-item trigger. DotaCoach.gg already shows "counter items against each enemy hero" | HIGH | OpenDota `/api/constants/abilities` endpoint (verified structure: `dname`, `behavior`, `dmg_type`, `bkbpierce`, `desc`, `target_team`, `target_type`, `attrib`), OpenDota `/api/constants/hero_abilities` for hero-to-ability mapping, new ability data storage, new counter-item mapping logic | **Verified**: ability data includes `behavior` (e.g., "Channeled"), `dmg_type` ("Magical"/"Physical"/"Pure"), `bkbpierce` ("Yes"/"No"). This enables rules like: "enemy has channeled ultimate -> Eul's/Hex counter" rather than hardcoded hero lists. Key counter categories to model: channeled abilities, passives (Break), escape abilities (Silence/Root), high regen (anti-heal), physical burst (Ghost Scepter), magic burst (BKB/Pipe) |
| Expanded counter-item rule set | Current 18 rules cover basics (BKB vs magic, MKB vs evasion, Spirit Vessel vs regen). Missing critical counter-item patterns: Eul's vs channeled ults (Enigma, CM, Witch Doctor, Pudge), Lotus Orb vs single-target ultimates (Lion, Lina, Necro), Nullifier vs Ghost/Glimmer carries, Linken's vs strong single-target initiation (Beastmaster, Batrider, Doom) | MEDIUM | Rules engine extension, ability behavior data to drive rule triggers instead of hardcoded hero lists | Can be implemented incrementally: start with 5-8 new ability-driven rules, then expand. The rule framework (`RulesEngine.evaluate()`) is clean and extensible -- each rule is a standalone method |
| Counter-item reasoning that names the specific ability | Players expect "buy Eul's to cancel Enigma's Black Hole" not "buy Eul's because Enigma has disables." Current rules already name enemy heroes but not their specific abilities | LOW | Ability data (dname field) available in the counter-item logic, template reasoning strings that reference ability names | The `_hero_name()` lookup pattern already exists. Adding `_ability_name()` for the most relevant ability is a small extension. Reasoning templates become: f"Against {hero_name}'s {ability_name}, {item_name} provides..." |

#### Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Ability-type-driven dynamic rules instead of hero lists | Instead of maintaining a static list of "channeled ult heroes," query the ability data: "any enemy hero whose ultimate has behavior=Channeled." This makes the rules engine automatically correct when new heroes are added or abilities are reworked. Zero maintenance on patch day | HIGH | Ability data cached in DataCache (new `AbilityCached` dataclass), hero-ability mapping cached, rules engine refactored to query abilities rather than hero ID sets | This is the architectural shift from "rules reference hero IDs" to "rules reference ability properties." Requires: (1) fetch and cache ability constants, (2) build hero -> abilities -> properties index, (3) refactor rules to use property queries. The payoff is enormous: rules never go stale after patches |
| Counter-item priority escalation based on enemy performance | If enemy PA has 8 kills and 1 death (from screenshot/GSI data), escalate the priority of counter items against her from "situational" to "core." "PA is 8-1 -- Ghost Scepter is now a survival necessity, not optional" | MEDIUM | Enemy context data (already in RecommendRequest as `enemy_context`), priority escalation logic in rules engine or system prompt | The enemy_context field already carries KDA data from screenshots. The system prompt already has "Enemy Power Levels" guidance. This feature connects counter-item rules to threat assessment. Implementation: rules engine checks enemy_context when deciding priority level for counter items |
| Item interaction awareness | Some counter items have specific interactions that matter: Lotus Orb reflects the SPELL not just blocks it (so it reflects Doom's Doom back). Linken's blocks one spell but not AoE. BKB doesn't block pure damage through spell immunity. Surfacing these nuances in reasoning | LOW | Already available via system prompt guidance and Claude's training data. Add specific interaction notes to counter-item reasoning templates | This is primarily a system prompt enhancement plus richer reasoning templates in the rules engine. Claude already knows these interactions but needs prompting to surface them |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Fully automated ability data parsing from game files | Parse npc_abilities.txt directly from Dota 2 game files for maximum accuracy | Requires game file extraction pipeline, version tracking, format parsing that changes with patches. OpenDota constants already does this and provides a clean API | Use OpenDota `/api/constants/abilities` and `/api/constants/hero_abilities`. Same data, zero maintenance |
| Counter-item popups during live game that obscure the UI | Real-time "BUY THIS NOW" alerts during teamfights | Distracting during gameplay, creates alert fatigue. DotaCoach uses a sidebar overlay, not intrusive popups | Surface urgency via the existing recommendation timeline with priority indicators, not interruption-style alerts |

---

### Category 3: Build Path Intelligence

#### Table Stakes

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Component ordering for recommended items | Currently Prismlab says "buy Battle Fury" but not "buy Quelling Blade first, then Perseverance for lane sustain, then Broadswords." Players at mid-skill brackets don't know the optimal component order. This is standard in DotaFire guides and DotaCoach's build suggestions | MEDIUM | Item component data (already in DB: `Item.components` stores component internal_names), cost data for components, new `build_path` field on `ItemRecommendation` schema | **Verified**: Item.components is already seeded from OpenDota (e.g., Battle Fury = `['pers', 'broadsword', 'broadsword', 'quelling_blade']`). Component items are also in the Item table with costs. The data exists -- this is a presentation and schema enhancement |
| Component-level reasoning | "Buy Perseverance first because the HP/mana regen keeps you in lane" is more useful than "buy Battle Fury." Each component serves a purpose -- the ordering should reflect game state priorities | MEDIUM | Build path ordering logic, per-component reasoning templates or system prompt guidance, schema changes | Can be implemented in two ways: (1) deterministic component ordering in rules/backend with template reasoning, or (2) ask Claude to reason about component ordering in the system prompt. Hybrid approach: backend provides ordered component list, Claude provides reasoning for the ordering |
| Component gold tracking | When a player has 1200g and needs Battle Fury (3900g), show "you can afford Perseverance (1400g) -- buy it now" rather than showing the full item as unaffordable | MEDIUM | GSI gold data (already in `gsiStore.liveState.gold`), component cost data, frontend logic to highlight affordable components | Natural extension of GSI integration. The gold data and component costs are already available -- this is frontend presentation logic |

#### Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Game-state-aware component priority | If player is losing lane (lane_result: "lost"), prioritize regen/defensive components of items. If winning, prioritize offensive components. "You lost lane -- rush Ring of Health from Perseverance before Broadsword" | HIGH | Lane result data (already in RecommendRequest), game-state-dependent component ordering logic | Requires conditional ordering logic: same final item, different component priority based on game state. This is true coaching intelligence -- understanding that BKB components should be Ogre Axe first when you need stats to survive, vs Mithril Hammer first when you need damage |
| "Skip component" intelligence | Some items have components that are skippable in certain situations. If you already have a Quelling Blade from starting items, don't buy another one for Battle Fury -- it's already counted. Surface this as "you already have Quelling Blade -- 3550g remaining" | LOW | Purchased items list (already tracked), component deduplication logic | Already partially handled by the purchased_items filter. Extension: recognize when purchased items overlap with components of recommended items |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-buy suggestions via key binds | "Press F5 to auto-buy next component" | Prismlab is a web app, not an Overwolf overlay. Cannot interact with the Dota 2 client directly. Also crosses into automation territory | Show the next component clearly with its cost. Player buys manually |
| Full item tree visualization with every sub-component | Show the complete dependency tree for every item (Perseverance = Ring of Health + Void Stone, Ring of Health = 700g, etc.) | Information overload. Players don't need to see that Ring of Health is a base component -- they know that. Multi-level trees create visual noise | Show one level of components only: the direct components of the target item. This is what DotaFire and in-game shop do |

---

### Category 4: Win Condition Framing

#### Table Stakes

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| Team composition classification | Classify the full 10-hero draft into macro strategy archetypes: Teamfight, Split-push, Pick-off/Gank, Deathball/Push, Late-game Scale. Players think in these terms. "We have a teamfight draft, so build aura items" vs "we have a split-push draft, so build mobility and tower damage" | MEDIUM | All 10 hero IDs (already in RecommendRequest: `hero_id` + `allies` + `lane_opponents` as proxy for enemy team), hero roles data from OpenDota constants (already cached), classification logic | **Approach**: Use hero role tags from OpenDota (e.g., "Pusher", "Initiator", "Carry", "Support", "Nuker", "Disabler") to classify team composition. A team with 3+ "Pusher" tagged heroes is deathball. A team with strong "Carry" + "Initiator" is teamfight. This can be deterministic rules or part of the system prompt |
| Win condition statement in overall_strategy | Currently `overall_strategy` describes the itemization game plan. Adding a win condition frame ("Your team wins by grouping at 20 min and forcing fights before their carry farms -- build team items") gives all item recommendations a strategic anchor | LOW | System prompt enhancement, team composition data passed to context builder | The `overall_strategy` field already exists in `LLMRecommendation`. This is a system prompt modification to instruct Claude to frame the strategy around how the team wins, not just what items to buy |
| Win condition aligned item priorities | If the win condition is "end before 30 min," late game luxury items should be deprioritized. If the win condition is "protect the carry until 40 min," survival and utility items are priority | LOW | Win condition classification feeding into system prompt context, potentially adjusting the `priority` field of recommendations | Claude can already reason about this -- it just needs the explicit win condition context. "Your team's win condition is early aggression. Prioritize items that peak at 20-25 min over 40 min items" |

#### Differentiators

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Dynamic win condition re-assessment | Win condition shifts during the game. A "teamfight at 25 min" draft that loses all lanes becomes a "defend and stall to 40 min" draft. Re-evaluate should adjust the win condition based on game state (lane results, tower count, gold advantage) | HIGH | GSI data (tower counts already in `gsiStore.liveState`), game clock, lane results, win condition classification that accepts game state inputs | Requires the win condition engine to be stateful: initial classification based on draft, then updated based on game events. This is sophisticated coaching intelligence -- recognizing that the game plan has changed |
| Enemy win condition assessment | "Their team wants to end before 35 min. Buy items that delay the game: wave clear, defensive auras, buyback gold" | MEDIUM | Enemy team composition (lane_opponents + other enemies from draft), same classification logic applied to enemy team | Requires full enemy team (currently the app tracks lane_opponents, not all 5 enemies). The 10-hero draft picker already captures all enemies, but the recommendation request only sends `lane_opponents`. Would need to expand the request or use the draft store |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Win probability prediction | "Your team has 62% chance to win" | Requires match prediction model trained on millions of games. Massive scope creep. Also psychologically harmful -- players tilt when shown low win probability | Frame win conditions as "how to win" not "probability of winning." Focus on actionable strategy, not prediction |
| Teammate coordination suggestions | "Tell your offlaner to buy Pipe" | Prismlab is a single-player tool. Cannot communicate with teammates. Suggesting items for others creates frustration when teammates don't comply | Frame ally awareness as "your offlaner typically builds Pipe -- if they don't, consider it yourself" (already partially done via ally item context) |

---

## Feature Dependencies

```
[Timing Benchmarks: Data Pipeline]
    |-- requires --> [OpenDota itemTimings API integration]
    |-- requires --> [ItemTimingBenchmark DB model + cache]
    |-- enables --> [Timing display in PhaseCard/ItemCard]
    |-- enables --> [Timing context in system prompt]
    |-- enables --> [Live timing comparison via GSI]

[Counter-Item Intelligence]
    |-- requires --> [Ability data fetch + cache (OpenDota constants/abilities)]
    |-- requires --> [Hero-ability mapping (OpenDota constants/hero_abilities)]
    |-- enables --> [Ability-driven rules (replaces hero ID lists)]
    |-- enables --> [Ability-naming in counter reasoning]
    |-- enhances --> [Existing 18 rules with deeper context]

[Build Path Intelligence]
    |-- requires --> [Item.components data (ALREADY IN DB)]
    |-- requires --> [Component cost resolution (ALREADY IN CACHE)]
    |-- enables --> [Component ordering in recommendations]
    |-- enables --> [Component gold tracking with GSI]
    |-- enhances --> [Timing Benchmarks: component-aware timing]

[Win Condition Framing]
    |-- requires --> [Hero role tag data (ALREADY CACHED)]
    |-- requires --> [Team composition classification logic]
    |-- enables --> [Win condition in overall_strategy]
    |-- enables --> [Win condition aligned item priorities]
    |-- enhances --> [Timing Benchmarks: win condition adjusts timing urgency]
    |-- enhances --> [Counter-Item Intelligence: win condition adjusts counter priority]

[Build Path Intelligence] -- enhances --> [Timing Benchmarks]
    (component ordering considers timing windows)

[Win Condition Framing] -- enhances --> [Counter-Item Intelligence]
    (win condition shifts which counters matter most)
```

### Dependency Notes

- **Timing Benchmarks require OpenDota itemTimings integration**: New API endpoint (`/api/scenarios/itemTimings`) not currently used. Needs fetch, cache, and data pipeline additions. Separate from existing `itemPopularity` pipeline.
- **Counter-Item Intelligence requires ability data**: Two new constants endpoints to fetch and cache. This is a one-time data fetch (refresh daily with items/heroes). The `hero_abilities` mapping links hero internal names to ability internal names; the `abilities` constants provide the mechanical data.
- **Build Path Intelligence already has its data**: `Item.components` is already seeded from OpenDota, costs are in the cache. This is primarily schema/presentation work, not data pipeline work. Fastest to ship.
- **Win Condition Framing primarily uses existing data**: Hero roles are already cached. The classification logic is new but deterministic. The main work is system prompt engineering and optional new rules.
- **Win Condition enhances everything else**: A "teamfight at 25 min" win condition makes timing benchmarks more urgent, shifts counter-item priorities toward team-fight-relevant counters, and changes build path ordering toward earlier completed items.

---

## MVP Definition

### Phase 1: Data Foundation + Quick Wins

Ship the data pipeline and the features that already have all data available.

- [ ] **Build path intelligence (component ordering)** -- data already exists, schema + presentation work only
- [ ] **Ability data fetch and cache** -- fetch `constants/abilities` and `constants/hero_abilities`, store in cache
- [ ] **Item timing data fetch and cache** -- fetch `/api/scenarios/itemTimings`, store in new DB model
- [ ] **Win condition classification logic** -- deterministic rules on hero role tags

### Phase 2: Core Intelligence Integration

Wire the new data into the recommendation engine.

- [ ] **Timing benchmarks in system prompt** -- inject timing windows into Claude context
- [ ] **Timing display on ItemCard/PhaseCard** -- frontend urgency badges
- [ ] **Expanded counter-item rules (ability-driven)** -- 5-8 new rules using ability behavior data
- [ ] **Counter reasoning names specific abilities** -- reasoning templates reference ability dname
- [ ] **Win condition in overall_strategy** -- system prompt instructs Claude to frame around win condition

### Phase 3: Live Game Intelligence

Features that depend on GSI integration and game-state awareness.

- [ ] **Live timing comparison** -- compare current gold/clock against timing benchmarks
- [ ] **Component gold tracking** -- highlight affordable components at current gold
- [ ] **Counter-item priority escalation** -- enemy KDA data shifts counter priorities

### Future Consideration (v5+)

- [ ] **Dynamic win condition re-assessment** -- defer: requires stateful game-phase tracking beyond current event triggers
- [ ] **Timing-aware re-evaluation weighting** -- defer: complex interaction between timing misses and item pivots
- [ ] **Full ability-type-driven dynamic rules** -- defer: full refactor of rules engine from hero-ID-based to ability-property-based. Ship incremental ability rules first, refactor later
- [ ] **Enemy win condition assessment** -- defer: requires passing all 5 enemy hero IDs (currently only lane opponents)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Notes |
|---------|------------|---------------------|----------|-------|
| Build path component ordering | HIGH | MEDIUM | P1 | Data exists, high coaching value, no API dependency |
| Timing benchmark data pipeline | HIGH | MEDIUM | P1 | Enables 3+ downstream features |
| Ability data fetch + cache | HIGH | MEDIUM | P1 | Enables counter-item depth |
| Win condition classification | HIGH | LOW | P1 | Uses existing cached data |
| Timing display on item cards | HIGH | LOW | P1 | Frontend-only after data pipeline |
| Timing context in system prompt | HIGH | LOW | P1 | 20-line context_builder addition |
| Expanded counter-item rules (ability-driven) | HIGH | MEDIUM | P1 | Core coaching value |
| Counter reasoning names abilities | MEDIUM | LOW | P1 | Polish, piggybacking on counter rules |
| Win condition in overall_strategy | HIGH | LOW | P1 | System prompt enhancement |
| Component-level reasoning | MEDIUM | MEDIUM | P2 | Requires careful prompt engineering |
| Live timing comparison via GSI | HIGH | MEDIUM | P2 | Depends on timing data pipeline |
| Component gold tracking (GSI) | MEDIUM | MEDIUM | P2 | Depends on build path work |
| Counter-item priority escalation | MEDIUM | MEDIUM | P2 | Uses existing enemy_context |
| Urgency signal badges | MEDIUM | LOW | P2 | Frontend polish after timing data |
| Game-state-aware component priority | MEDIUM | HIGH | P3 | Complex conditional logic |
| Dynamic win condition re-assessment | HIGH | HIGH | P3 | Stateful game tracking |
| Enemy win condition assessment | MEDIUM | MEDIUM | P3 | Needs full enemy team data |

**Priority key:**
- P1: Ships in v4.0 core phases
- P2: Ships in v4.0 polish phases if time permits
- P3: Future consideration (v4.x or v5.0)

---

## Competitor Feature Analysis

| Feature | DotaCoach.gg | STRATZ | Dotabuff | Dota2ProTracker | Prismlab v4.0 Approach |
|---------|--------------|--------|----------|-----------------|----------------------|
| Item timing data | Not shown | Purchase Pattern with win rate gradient, detailed view with time sliders | End-of-game item win rates only (skewed) | Pro match item builds with implicit timing | Population timing benchmarks from OpenDota, surfaced per-item with urgency signals. Win rate gradient analysis for timing sensitivity |
| Counter items | Per-enemy hero counter items in sidebar overlay | Hero page shows common counters | Hero matchup page with items | Not explicitly shown | Ability-specific counter items with named-ability reasoning. Driven by ability mechanics, not just hero ID lists |
| Build path ordering | Static hero builds with component order | Not explicitly shown | Guide builds have ordering | Pro builds show purchase order | Dynamic component ordering based on game state. Components prioritized by lane result and gold availability |
| Win condition framing | Not shown (hero-specific coaching only) | Not shown | Not shown | Not shown | **Unique differentiator**: Team composition classified into macro strategy, all item recommendations framed around how the team wins. No competitor does this |
| Ability reasoning depth | Counter tips mention abilities by name | Hero ability pages separate from items | Guides reference abilities | Not shown | Counter-item rules driven by ability behavior properties (channeled, passive, escape). Reasoning templates name the specific ability and explain the interaction |
| Live game integration | Overwolf overlay with real-time suggestions | No live integration | No live integration | No live integration | GSI-powered timing comparison, component affordability tracking, priority escalation from live enemy performance |

**Key competitive insight**: No existing tool combines timing benchmarks + ability-driven counter intelligence + win condition framing into a unified recommendation. DotaCoach comes closest with its counter items and coaching, but it's an Overwolf overlay, not a reasoning engine. STRATZ has the best timing data but presents it as analytics, not coaching. Prismlab's unique value is the hybrid engine that synthesizes all this data into contextual, explained recommendations.

---

## Existing System Integration Points

### Backend

| Component | What Changes | Impact |
|-----------|-------------|--------|
| `opendota_client.py` | Add `fetch_item_timings(hero_id)`, `fetch_abilities()`, `fetch_hero_abilities()` methods | LOW -- follows existing pattern of `fetch_*` methods |
| `data/models.py` | Add `ItemTimingBenchmark` model, optionally `HeroAbility` model | LOW -- new tables, no schema migration on existing tables |
| `data/cache.py` | Add ability data to `DataCache`, add timing data access methods | MEDIUM -- new dataclass (`AbilityCached`), new index structures |
| `data/seed.py` | Add ability and hero_abilities seeding | LOW -- follows existing seed pattern |
| `data/refresh.py` | Add timing data refresh to daily pipeline | LOW -- follows existing refresh pattern |
| `engine/rules.py` | New counter-item rules using ability data, optional refactor from hero-ID lists | MEDIUM -- 5-8 new rule methods, or refactor existing rules to use ability queries |
| `engine/schemas.py` | Add `build_path` field to `ItemRecommendation`, add timing fields to `RecommendPhase`, add `win_condition` to `LLMRecommendation` | MEDIUM -- schema changes require frontend type updates |
| `engine/context_builder.py` | Add timing benchmark section, ability context section, win condition section to user message | MEDIUM -- 3 new section builders following existing patterns |
| `engine/prompts/system_prompt.py` | Add timing benchmark guidance, ability-specific counter rules, win condition framing instructions | LOW -- text additions to existing prompt |
| `engine/recommender.py` | Pass timing and win condition data through merge pipeline | LOW -- data flows through existing merge/validate pipeline |

### Frontend

| Component | What Changes | Impact |
|-----------|-------------|--------|
| `types/recommendation.ts` | Add `build_path`, `timing_benchmark`, `win_condition` fields | LOW -- type additions |
| `components/timeline/ItemCard.tsx` | Add urgency badge, timing indicator, component ordering display | MEDIUM -- new visual elements |
| `components/timeline/PhaseCard.tsx` | Add timing benchmark display per phase | LOW -- small additions to existing layout |
| `components/timeline/ItemTimeline.tsx` | Add win condition banner at top of timeline | LOW -- new section above phases |
| `stores/recommendationStore.ts` | Store timing comparison state, win condition | LOW -- small state additions |

---

## Sources

- [OpenDota API Documentation](https://docs.opendota.com/) -- confirmed `/api/scenarios/itemTimings` endpoint, `/api/constants/abilities`, `/api/constants/hero_abilities`
- [OpenDota itemTimings endpoint](https://www.opendota.com/scenarios/itemTimings) -- live data verified via API call, returns `{hero_id, item, time, games, wins}`
- [OpenDota dotaconstants repository](https://github.com/odota/dotaconstants) -- `build/hero_abilities.json` and `build/abilities.json` for ability data
- [STRATZ Item Timings Analysis](https://medium.com/stratz/dota-2-item-timings-22d2dbd76bc4) -- defines timing importance via win rate gradient analysis, central 69% purchase window methodology
- [STRATZ API](https://stratz.com/api) -- alternative data source for timing data (GraphQL), 2000 req/hour free tier
- [DotaCoach.gg Features](https://dotacoach.gg/en/app/features) -- competitor analysis: counter items per enemy, phase-based item suggestions, Overwolf overlay
- [Dota2ProTracker](https://dota2protracker.com/) -- pro match build orders from 7000+ MMR matches
- [DotA-Item-Timings Project](https://github.com/nander25/DotA-Item-Timings) -- prior art using OpenDota API for item timing analysis
- [Go OpenDota Client](https://pkg.go.dev/github.com/jasonodonnell/go-opendota) -- confirmed ScenariosService.ItemTimings method signature and response structure
- [Dota 2 Team Composition Strategy](https://steamcommunity.com/sharedfiles/filedetails/?id=2395798524) -- team composition classification concepts: teamfight, split push, ganking, deathball
- [Dota 2 Abilities by Type (Wiki)](https://dota2.fandom.com/wiki/Abilities/Abilities_by_type) -- canonical reference for ability classifications

---
*Feature research for: v4.0 Coaching Intelligence*
*Researched: 2026-03-27*
