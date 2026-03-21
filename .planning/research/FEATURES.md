# Feature Research

**Domain:** Dota 2 adaptive item advisor
**Researched:** 2026-03-21
**Confidence:** HIGH

## Competitive Landscape Summary

The Dota 2 item recommendation space has several established players, each with distinct approaches:

| Tool | Approach | Strengths | Weaknesses |
|------|----------|-----------|------------|
| **In-game guides** (Torte de Lini, ImmortalFaith) | Static, manually curated builds for every hero | Universal reach (90% of matches use them), always visible in-game shop | Static -- same build regardless of matchup, no adaptation, no reasoning |
| **Dota Plus** (Valve) | ML-powered suggestions from millions of matches, in-game overlay | Real-time, draft-aware, three build paths, adapts to lane/inventory | No explanations for "why," shallow -- just shows popular items, requires subscription |
| **Dotabuff Adaptive Items** | ML model via Overwolf overlay, draft-aware with timing estimates | Adapts on the fly if you deviate, shows gold progress and purchase timing | Requires Overwolf, no reasoning/explanation, limited to build path (no decision trees) |
| **Dota Coach** (Overwolf) | Professionally-curated coaching with in-game overlay | Timer notifications, hero coaching text, actively maintained | Requires Overwolf, coaching is generic per-hero not per-matchup |
| **STRATZ** | Auto-generated guides from top player match data | Always up-to-date, multiple guide variants per hero, free, rich stats | Web-only post-game analysis, no real-time adaptation, no reasoning text |
| **Dota2ProTracker** | Aggregated 7K+ MMR and pro match data | Filtered by position and facet, updated daily, shows most common sequences | Reference tool not advisor, no adaptation, no explanations |
| **OpenDota** | Open API with matchup win rates, item popularity by phase | Free, comprehensive data, open source | Raw data platform, not a recommendation tool -- requires interpretation |
| **Spectral Builds** | Stats-based builds with optional "explain" feature | Unique explanation attempt, community-driven | Explanations are basic, builds are static, small audience |
| **dota2-helper** (GitHub) | LLM-powered (Groq/GPT-OSS 120B) item + ability advice | Full draft context, ability-level reasoning, natural language output | Hobby project, no mid-game adaptation, no item tracking, no phase progression |

**The critical gap:** No existing tool combines all three of (1) draft/matchup awareness, (2) mid-game adaptation, and (3) natural language reasoning explaining "why." Prismlab fills this gap.

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Searchable hero picker with portraits | Every Dota tool has this. Without it, users cannot interact at all | MEDIUM | Fuzzy search, attribute/attack-type filters, hero portraits from Steam CDN. Reusable for your hero + opponent slots |
| Hero portraits and item icons from CDN | Players identify heroes/items visually, not by text | LOW | Steam CDN URLs are well-documented. Never self-host these |
| Role/position selection (Pos 1-5) | Role fundamentally changes item builds. Same hero, different role = different items | LOW | Simple 5-button selector. Unlocks playstyle options |
| Item build organized by game phase | Every guide (static or dynamic) segments starting/early/core/late. Players think in phases | MEDIUM | Timeline UI with starting, laning, core, situational phases. This is the primary output surface |
| Starting item recommendations | The first thing a player needs to know. Universal expectation from any item guide | LOW | Rule-based layer can handle most starting item logic without LLM |
| Lane opponent context | Dota Plus, Dotabuff Adaptive Items, and even static guides implicitly build around matchups | MEDIUM | 1-2 opponent slots. Lane matchup is the single most important input for item decisions |
| Dark theme with Dota aesthetic | Every Dota tool uses dark UI. A light theme would feel alien and hostile | LOW | Deep charcoal background, spectral cyan accent, Radiant/Dire color coding |
| Item images with cost displayed | Players need to see what the item looks like and what it costs. Basic information | LOW | CDN images with gold cost overlay |
| Loading states during recommendation generation | LLM calls take 2-5 seconds. Without loading feedback, users think it is broken | LOW | Skeleton loaders or spinner on the recommendation panel only |
| Fallback when AI/API fails | Claude API may timeout or fail. Users must still get something useful | MEDIUM | Rules-only fallback produces reasonable (if generic) builds. Users see a notice that reasoning is unavailable |

### Differentiators (Competitive Advantage)

Features that set Prismlab apart from every existing tool. These are where the product competes.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Natural language reasoning per item ("the why") | **No existing tool explains WHY you should buy an item in the context of your specific game.** Dota Plus shows what is popular. Guides show what to buy. Nobody says "buy BKB because Lina Light Strike Array + Laguna Blade will kill you at level 9 if you do not have spell immunity." This is Prismlab core differentiator | HIGH | Claude API generates 1-3 sentence reasoning per item referencing specific hero abilities, matchup dynamics, and game state. This is the heart of the product |
| Playstyle-aware recommendations | No tool asks "how do you want to play?" -- they all assume a default playstyle. An aggressive Pos 1 carry needs different starting items than a passive farmer on the same hero | LOW | Dropdown per role (4 options each). Playstyle is injected into the Claude prompt as player intent. Simple to build, powerful in output |
| Mid-game re-evaluation with state updates | Dotabuff Adaptive Items adapts if you deviate. But no tool lets you say "I lost my lane, they have 3 physical damage cores, and I saw a BKB on their Sven" and get a completely revised build. Prismlab does | HIGH | Lane result selector, damage profile input, enemy item tracker, re-evaluate button. Past purchases locked, only future items regenerated. This is the "living advisor" concept |
| Situational decision trees (not just a linear build) | Existing tools give you one path (or three at best). Dota itemization is branching -- "if they have evasion, MKB; if they have magic damage, BKB." Prismlab shows these branches explicitly | MEDIUM | Decision tree cards in the UI with conditions and recommendations. Claude generates these as part of the situational phase |
| Hybrid engine (rules + LLM) | Rules fire instantly for obvious decisions (Magic Stick vs spell spammers). Claude handles nuance. Users get instant results for known patterns and rich reasoning for complex decisions. Fallback mode if LLM fails | HIGH | Rule-based layer is fast and deterministic. LLM layer is slow but intelligent. Orchestrator decides what needs reasoning vs what is obvious |
| Radiant/Dire side awareness | Side affects lane geometry, pull camps, Roshan proximity, triangle farming. No item tool factors this in. A Dire safelane carry might rush Helm of the Dominator to take early Roshan; a Radiant safelane carry would not | LOW | Simple toggle that gets injected into the prompt context. Low effort, meaningfully affects recommendations |
| Matchup-specific item data from OpenDota/Stratz | Most tools show global item popularity. Prismlab shows "in this specific matchup (your hero vs their heroes), these items have the highest win rates" | MEDIUM | Backend fetches matchup-specific item win rates and feeds them as context to Claude. Data pipeline required |
| Progressive information flow (draft -> laning -> mid -> late) | Matches how information reveals during an actual Dota game. You know draft first, then lane opponents, then damage profiles. No tool mirrors this naturally | MEDIUM | UI transitions through phases, revealing new input options and collapsing completed phases. State management via Zustand |
| Click-to-mark items as purchased | Locks in what you already bought so re-evaluation only generates remaining items. Simple interaction during live gameplay | LOW | Click handler on item icons, toggling purchased state. Re-evaluate uses this to scope the generation |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems. Explicitly NOT building these in V1.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| In-game overlay (Overwolf/GSI) | Players want recommendations visible during gameplay without alt-tabbing | Overwolf is bloated and controversial in the community. GSI requires local server setup and Steam configuration. Both add massive complexity. The overlay approach also risks Valve policy issues | Desktop web app on second monitor or alt-tab. V2 can explore GSI for auto-reading game state, but overlay is not the goal |
| Full allied team synergy analysis | "Your team needs wave clear" type advice sounds valuable | Dramatically increases prompt complexity, API cost, and recommendation surface. V1 focus is "win your lane" -- allied team context adds noise without proportional value | V1 takes 10-hero draft as context but focuses recommendations on YOUR lane matchup. V2 can add deep synergy analysis |
| Neutral item recommendations | Neutral items are part of every game after 7 minutes | Neutral item drops are random -- recommending "get Philosopher Stone" is useless if it does not drop. Timing is unpredictable. The decision space (5 tiers, random drops, team-wide sharing) does not fit the advisor model well | Defer to V2 where GSI might auto-detect drops. V1 focuses on purchased items only |
| Auto gold/net worth tracking | Knowing current gold would let the tool say "you can afford X right now" | Requires GSI or manual entry (which is tedious during a game). Gold changes every second. The cognitive overhead of updating gold manually exceeds the benefit | V1 uses phase-based timing estimates instead of real gold values. V2 with GSI can read gold automatically |
| Build history / session saving | Players might want to revisit recommendations from previous games | Adds database complexity, auth considerations, and maintenance burden for V1. The value is minimal -- each game is unique | Defer entirely. V1 is ephemeral -- each session is a fresh game. V2 can add persistence if demand exists |
| Voice callouts / TTS | "Buy BKB now" audio cues during gameplay | Audio implementation is complex, accessibility concerns, and most players already have game audio + voice chat competing for attention | Not planned for any version. Text-based reasoning is sufficient |
| Mobile-optimized layout | Some users might want phone access during games | Desktop-first matches the use case (second monitor or alt-tab). Mobile optimization is significant UI work with minimal value for the primary use case | Do not break on mobile (responsive basics) but do not optimize. V2 can consider mobile if demand exists |
| Real-time meta/patch tracking | "This item was buffed in 7.38, consider it more" | Requires parsing patch notes (unstructured text), tracking item changes across patches, and maintaining a diff system. Extremely complex for marginal value | Data refresh pipeline updates matchup stats post-patch. If item win rates change, recommendations naturally shift. Claude training data includes general patch awareness. V2 can add explicit patch note integration |
| Community build sharing | Let users share their generated builds | Social features are scope creep for a personal advisor tool. Requires auth, moderation, ranking systems | Not planned. The tool is a personal advisor, not a community platform |
| Screenshot/scoreboard parsing | Upload a screenshot to auto-fill game state | OCR/CV pipeline adds massive complexity. Accuracy issues with varying resolutions, UI skins, and game state visibility | V1 uses manual toggles and entry (quick enough during death timers). V2 can explore this |

## Feature Dependencies

```
[Hero Picker]
    |
    +--requires--> [Hero Data API + CDN Images]
    |
    +--enables---> [Role Selector]
                       |
                       +--enables---> [Playstyle Selector]
                       |
                       +--enables---> [Lane Selector]
                                          |
                                          +--enables---> [Opponent Picker]
                                                             |
                                                             +--enables---> [Recommendation Engine]
                                                                                |
                                                                                +--requires--> [Rules Layer]
                                                                                |
                                                                                +--requires--> [Claude API Integration]
                                                                                |
                                                                                +--requires--> [Matchup Data Pipeline]
                                                                                |
                                                                                +--enables---> [Item Timeline UI]
                                                                                                   |
                                                                                                   +--enables---> [Click-to-Mark Purchased]
                                                                                                                      |
                                                                                                                      +--enables---> [Mid-Game State Inputs]
                                                                                                                                        |
                                                                                                                                        +--enables---> [Re-Evaluate Button]

[Side Selector] --enhances--> [Recommendation Engine] (independent, can build anytime)

[Fallback Mode] --requires--> [Rules Layer] (must exist before LLM integration)
```

### Dependency Notes

- **Playstyle Selector requires Role Selector:** Playstyle options are role-dependent (Pos 1 aggressive laner vs Pos 5 lane protector)
- **Recommendation Engine requires all draft inputs:** Hero, role, playstyle, lane, opponents must be selectable before the engine has enough context
- **Rules Layer must exist before Claude integration:** Rules layer serves as fallback -- it must work independently before the LLM layer is added
- **Item Timeline requires Recommendation Engine:** Cannot render recommendations without generating them
- **Mid-Game inputs require Item Timeline:** Users need to see initial recommendations before updating game state
- **Re-Evaluate requires Click-to-Mark:** Must know what is already purchased to regenerate only remaining items
- **Matchup Data Pipeline enhances Recommendation Engine:** Can start with LLM-only reasoning, add statistical context later. But better to have data from the start

## MVP Definition

### Launch With (v1)

Minimum viable product -- what is needed to validate the core value proposition ("always know what to buy and WHY").

- [ ] Hero picker with search and portraits -- core input mechanism
- [ ] Role selector (Pos 1-5) -- fundamental to item builds
- [ ] Playstyle selector (role-dependent) -- key differentiator, low cost
- [ ] Side selector (Radiant/Dire) -- differentiator, trivial to build
- [ ] Lane selector (Safe/Off/Mid) -- required context for recommendations
- [ ] Opponent picker (1-2 lane opponents) -- the matchup is the core input
- [ ] Rules-based starting item recommendations -- instant, no API call needed
- [ ] Claude API integration for reasoned recommendations -- the differentiating output
- [ ] Hybrid engine orchestrator (rules + LLM with fallback) -- reliability requirement
- [ ] Item timeline UI with phase cards -- the primary output surface
- [ ] Reasoning tooltips/text per item -- the "why" that makes this unique
- [ ] Situational decision tree cards -- branching recommendations for late game
- [ ] Dark theme with Dota aesthetic -- visual table stakes
- [ ] Loading states during LLM calls -- UX requirement
- [ ] Docker Compose deployment -- deployment target is Unraid

### Add After Validation (v1.x)

Features to add once the core draft-to-recommendation flow is working and validated.

- [ ] Click-to-mark items as purchased -- enables re-evaluation
- [ ] Lane result selector (Won/Even/Lost) -- first mid-game input
- [ ] Damage profile input (Physical/Magical/Pure %) -- mid-game adaptation
- [ ] Enemy item tracker -- spot key items on enemies
- [ ] Re-evaluate button -- regenerate remaining items with updated state
- [ ] Phase progression (collapse past phases, expand current) -- UI polish
- [ ] Matchup data pipeline from OpenDota (item win rates per matchup) -- enriches recommendations with data
- [ ] Data refresh scripts (daily cron) -- keeps matchup data current
- [ ] Performance optimization (debounce, caching) -- production readiness

### Future Consideration (v2+)

Features to defer until the core product is validated and stable.

- [ ] Full allied team synergy analysis -- "your team needs X" recommendations
- [ ] Neutral item tier recommendations -- depends on drop randomness problem
- [ ] GSI integration for auto-reading game state -- eliminates manual input
- [ ] Build history / session persistence -- revisit past game recommendations
- [ ] Mobile-optimized layout -- if user demand materializes
- [ ] Patch notes integration -- explicit "this item was buffed" context
- [ ] Screenshot/scoreboard parsing -- auto-fill game state from image

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hero picker with search | HIGH | MEDIUM | P1 |
| Role selector | HIGH | LOW | P1 |
| Playstyle selector | HIGH | LOW | P1 |
| Side selector | MEDIUM | LOW | P1 |
| Lane selector | HIGH | LOW | P1 |
| Opponent picker | HIGH | MEDIUM | P1 |
| Rules-based starting items | HIGH | MEDIUM | P1 |
| Claude API integration | HIGH | HIGH | P1 |
| Hybrid engine orchestrator | HIGH | HIGH | P1 |
| Item timeline UI | HIGH | MEDIUM | P1 |
| Reasoning text per item | HIGH | LOW (output of LLM) | P1 |
| Situational decision trees | MEDIUM | MEDIUM | P1 |
| Dark Dota theme | HIGH | LOW | P1 |
| Loading states | HIGH | LOW | P1 |
| Fallback mode (rules-only) | HIGH | LOW | P1 |
| Click-to-mark purchased | MEDIUM | LOW | P2 |
| Lane result selector | MEDIUM | LOW | P2 |
| Damage profile input | MEDIUM | LOW | P2 |
| Enemy item tracker | MEDIUM | MEDIUM | P2 |
| Re-evaluate button | HIGH | MEDIUM | P2 |
| Phase progression UI | MEDIUM | MEDIUM | P2 |
| Matchup data pipeline | HIGH | HIGH | P2 |
| Data refresh scripts | MEDIUM | MEDIUM | P2 |
| Allied team synergy | MEDIUM | HIGH | P3 |
| Neutral items | LOW | MEDIUM | P3 |
| GSI integration | MEDIUM | HIGH | P3 |
| Build history | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch -- validates the core concept
- P2: Should have, add when core flow works -- completes the mid-game adaptation story
- P3: Nice to have, future consideration -- V2 scope

## Competitor Feature Analysis

| Feature | In-Game Guides | Dota Plus | Dotabuff Adaptive | STRATZ Guides | Dota2ProTracker | Prismlab |
|---------|---------------|-----------|-------------------|---------------|-----------------|----------|
| Item recommendations | Static per hero | Draft-aware, 3 paths | Draft-aware, adapts on deviation | Per hero, multiple variants | Per hero/position/facet | Draft + matchup + playstyle + side aware |
| Explains "why" | Tooltip notes (manual) | No | No | No | No | **Yes -- natural language per item** |
| Matchup-specific | No | Partially (draft context) | Partially (draft context) | Win rates shown | Win rates shown | **Yes -- abilities + interactions cited** |
| Mid-game adaptation | No | Recalculate button | Adapts on purchase deviation | No (post-game analysis) | No | **Yes -- lane result, damage profile, enemy items** |
| Playstyle input | No | No | No | No | No | **Yes -- 4 playstyles per role** |
| Side awareness | No | No | No | No | No | **Yes -- Radiant/Dire lane geometry** |
| Situational branches | No | No | No | No | No | **Yes -- decision tree cards** |
| In-game overlay | Yes (native) | Yes (native) | Yes (Overwolf) | No | No | No (web app, second monitor) |
| Data source | Manual curation | Valve match database | Dotabuff ML models | Top player matches | 7K+ MMR matches | OpenDota/Stratz + Claude reasoning |
| Cost | Free | $3.99/mo subscription | Free (Overwolf, 3 module slots) | Free | Free | Free (self-hosted, user pays Claude API) |
| Always up-to-date | Manual updates per patch | Auto-updated | Auto-updated | Auto-updated weekly | Auto-updated daily | Data pipeline + LLM knowledge |

## Key Insight

The competitive landscape reveals a clear pattern: **existing tools answer "WHAT to buy" but none answer "WHY to buy it in this specific game."** The closest attempt is Spectral Builds "explain" feature, which provides basic statistical reasoning but not matchup-specific coaching-level analysis.

Prismlab differentiation is not another item recommender. It is an **item reasoning engine** -- the recommendations are the vehicle, but the reasoning is the product. A player using Prismlab should internalize itemization logic over time because they receive explanations, not just instructions.

## Sources

- [Dotabuff Adaptive Items announcement](https://www.dotabuff.com/blog/2021-06-23-announcing-the-dotabuff-apps-new-adaptive-items-module) -- MEDIUM confidence (2021, features may have evolved)
- [Dota Plus official page](https://www.dota2.com/plus) -- HIGH confidence (official Valve source, features verified)
- [STRATZ Hero Guides blog post](https://medium.com/stratz/dota-2-hero-guides-2c19fab79795) -- MEDIUM confidence (could not fetch full content, details from search snippets)
- [Dota2ProTracker](https://dota2protracker.com/) -- HIGH confidence (active site on current patch 7.40c)
- [Torte de Lini background](https://esports.gg/news/dota-2/torte-de-lini-interview/) -- HIGH confidence (interview with guide creator)
- [Dota Coach Overwolf](https://www.overwolf.com/app/dota-coach.com-dota_coach) -- MEDIUM confidence (search snippet data)
- [dota2-helper GitHub project](https://github.com/samiamjidkhan/dota2-helper) -- HIGH confidence (verified GitHub repo)
- [Spectral Hero Builds](https://builds.spectral.gg/) -- MEDIUM confidence (active project)
- [OpenDota API docs](https://docs.opendota.com/) -- HIGH confidence (official documentation)
- [Sequential Item Recommendation research](https://arxiv.org/abs/2201.08724) -- HIGH confidence (peer-reviewed paper)

---
*Feature research for: Dota 2 adaptive item advisor*
*Researched: 2026-03-21*
