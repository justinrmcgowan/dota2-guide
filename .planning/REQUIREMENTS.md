# Requirements: Prismlab

**Defined:** 2026-03-27
**Core Value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.

## v4.0 Requirements

Requirements for v4.0 Coaching Intelligence. Each maps to roadmap phases.

### Data Foundation

- [x] **DATA-01**: System fetches and caches hero ability metadata (behavior, damage type, BKB-pierce, dispellable) from OpenDota constants
- [x] **DATA-02**: System fetches and caches hero-to-ability mapping from OpenDota constants
- [x] **DATA-03**: System fetches and caches item timing benchmark data (hero, item, time bucket, games, win rate) from OpenDota scenarios endpoint
- [x] **DATA-04**: System prompt restructured — directives stay in system message (~5K token budget), all dynamic data (timing, abilities, components) moves to user message

### Timing Benchmarks

- [x] **TIME-01**: User can see timing benchmarks (good/average/late window with win rate gradients) on each recommended item
- [x] **TIME-02**: User can see urgency indicators distinguishing timing-sensitive items (steep win rate falloff) from flexible items
- [ ] **TIME-03**: Claude's reasoning references specific timing benchmarks when explaining item urgency
- [x] **TIME-04**: User can see live comparison of current gold/clock against timing benchmarks during GSI-connected games

### Counter-Item Intelligence

- [x] **CNTR-01**: Counter-item rules query ability properties (channeled, passive, BKB-pierce) instead of hardcoded hero ID lists
- [x] **CNTR-02**: System includes 5-8 new counter-item rules covering channeled ults, single-target ults, escape abilities, high regen, and burst damage patterns
- [x] **CNTR-03**: Counter-item reasoning names the specific enemy ability being countered
- [x] **CNTR-04**: Counter-item priority escalates based on enemy performance data (KDA from screenshots/GSI)

### Build Path Intelligence

- [ ] **PATH-01**: User can see the optimal component purchase order for each recommended item
- [ ] **PATH-02**: User can see reasoning for component ordering (why this component first)
- [ ] **PATH-03**: User can see which components are affordable at current gold during GSI-connected games
- [ ] **PATH-04**: Component ordering adapts to game state — lost lane prioritizes defensive components, won lane prioritizes offensive

### Win Condition Framing

- [ ] **WCON-01**: System classifies 10-hero drafts into macro strategy archetypes (teamfight, split-push, pick-off, deathball, late-game scale)
- [ ] **WCON-02**: Win condition statement anchors overall_strategy and frames all item recommendations
- [ ] **WCON-03**: Item priorities adjust based on win condition — early win condition deprioritizes luxury items
- [ ] **WCON-04**: System assesses enemy team's win condition and recommends counter-strategy items

## v3.0 Requirements (Complete)

### Design System

- [x] **DESIGN-01**: Tailwind @theme block replaced with DESIGN.md tokens (obsidian surfaces, crimson/gold palette, 0px corners)
- [x] **DESIGN-02**: Newsreader (display/headline) and Manrope (body/label) fonts self-hosted via @fontsource-variable with metric-matching fallbacks
- [x] **DESIGN-03**: All components updated to use surface hierarchy (no 1px borders, tonal layering for depth)
- [x] **DESIGN-04**: Ambient crimson glow shadows replace drop shadows on floating elements
- [x] **DESIGN-05**: Gold left-accent strips on hero/legendary item cards
- [x] **DESIGN-06**: "Blood-glass" backdrop-blur overlays on tactical overlays (modals, settings panel, screenshot parser)
- [x] **DESIGN-07**: Parchment noise texture overlay on base background
- [x] **DESIGN-08**: All existing components pass visual audit against DESIGN.md spec (no rounded corners, no blue links, no #FFFFFF)

### Performance

- [x] **PERF-01**: In-memory DataCache singleton preloads hero and item data at startup, eliminating per-request DB queries
- [x] **PERF-02**: DataCache refreshes atomically on 6h pipeline cycle (coordinated with ResponseCache and RulesEngine invalidation)
- [x] **PERF-03**: Context builder and recommendation engine consume DataCache instead of direct DB queries

### Integration

- [x] **INT-01**: useGsiSync and useAutoRefresh consolidated into single useGameIntelligence hook with one gsiStore subscription
- [x] **INT-02**: Playstyle auto-suggested (first valid option for role) when GSI detects hero and role
- [x] **INT-03**: Screenshot-parsed KDA and level data fed into recommendation request context for Claude reasoning
- [x] **INT-04**: TriggerEvent interface deduplicated (single source in triggerDetection.ts)
- [x] **INT-05**: refresh_lookups() session safety fixed (fresh session or atomic swap)
- [x] **INT-06**: ResponseCache cleared on data pipeline refresh (coordinated with DataCache)

## Future Requirements

Deferred to future release.

### Advanced Automation

- **AUTO-01**: Hotkey screen capture (ShareX-style) instead of manual paste
- **AUTO-02**: Clipboard auto-detect for new screenshots
- **AUTO-03**: Ability build suggestions (not just items)

### Mobile & Accessibility

- **MOB-01**: Mobile-responsive layout optimization
- **MOB-02**: Voice coaching / audio callouts

### Advanced Intelligence (v4.x+)

- **ADVINT-01**: Dynamic win condition re-assessment during live game based on game state changes (tower count, gold advantage, lane results)
- **ADVINT-02**: Timing-aware re-evaluation weighting — missed timing suggests cheaper power spike alternatives
- **ADVINT-03**: Full ability-type-driven dynamic rules — complete refactor from hero-ID lists to ability-property queries across all 18+ rules

## Out of Scope

| Feature | Reason |
|---------|--------|
| Prescriptive timing targets (exact minute) | False precision — population averages don't account for individual game variance. Use ranges instead |
| Per-match timing comparison | Requires Steam login + match history access — massive scope expansion |
| Auto-buy keybind suggestions | Web app cannot interact with Dota 2 client |
| Full item tree visualization | Information overload — show one level of components only |
| Win probability prediction | Requires match prediction model — scope creep, psychologically harmful |
| Teammate coordination suggestions | Single-player tool — can't control what teammates buy |
| Counter-item popup alerts | Distracting during gameplay — use inline urgency indicators |
| Hotkey/clipboard screen capture | Manual paste sufficient — lower complexity |
| Voice coaching | Text-only — audio adds significant complexity |
| Ability build suggestions | Item-focused only — abilities are a different domain |
| Mobile optimization | Desktop-first — Dota 2 is a desktop game |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 19 | Complete |
| DATA-02 | Phase 19 | Complete |
| DATA-03 | Phase 19 | Complete |
| DATA-04 | Phase 19 | Complete |
| CNTR-01 | Phase 20 | Complete |
| CNTR-02 | Phase 20 | Complete |
| CNTR-03 | Phase 20 | Complete |
| CNTR-04 | Phase 20 | Complete |
| TIME-01 | Phase 21 | Complete |
| TIME-02 | Phase 21 | Complete |
| TIME-03 | Phase 21 | Pending |
| TIME-04 | Phase 21 | Complete |
| PATH-01 | Phase 22 | Pending |
| PATH-02 | Phase 22 | Pending |
| PATH-03 | Phase 22 | Pending |
| PATH-04 | Phase 22 | Pending |
| WCON-01 | Phase 23 | Pending |
| WCON-02 | Phase 23 | Pending |
| WCON-03 | Phase 23 | Pending |
| WCON-04 | Phase 23 | Pending |
| DESIGN-01 | Phase 17 | Complete |
| DESIGN-02 | Phase 17 | Complete |
| DESIGN-03 | Phase 17 | Complete |
| DESIGN-04 | Phase 17 | Complete |
| DESIGN-05 | Phase 17 | Complete |
| DESIGN-06 | Phase 17 | Complete |
| DESIGN-07 | Phase 17 | Complete |
| DESIGN-08 | Phase 17 | Complete |
| PERF-01 | Phase 16 | Complete |
| PERF-02 | Phase 16 | Complete |
| PERF-03 | Phase 16 | Complete |
| INT-01 | Phase 15 | Complete |
| INT-02 | Phase 15 | Complete |
| INT-03 | Phase 18 | Complete |
| INT-04 | Phase 15 | Complete |
| INT-05 | Phase 16 | Complete |
| INT-06 | Phase 16 | Complete |

**Coverage:**
- v4.0 requirements: 20 total
- Mapped to phases: 20/20
- Unmapped: 0

---
*Requirements defined: 2026-03-27*
*Last updated: 2026-03-27 after roadmap creation*
