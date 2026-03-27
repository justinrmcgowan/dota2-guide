# Requirements: Prismlab

**Defined:** 2026-03-26
**Core Value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.

## v3.0 Requirements

Requirements for v3.0 release. Each maps to roadmap phases.

### Design System

- [x] **DESIGN-01**: Tailwind @theme block replaced with DESIGN.md tokens (obsidian surfaces, crimson/gold palette, 0px corners)
- [x] **DESIGN-02**: Newsreader (display/headline) and Manrope (body/label) fonts self-hosted via @fontsource-variable with metric-matching fallbacks
- [x] **DESIGN-03**: All components updated to use surface hierarchy (no 1px borders, tonal layering for depth)
- [x] **DESIGN-04**: Ambient crimson glow shadows replace drop shadows on floating elements
- [x] **DESIGN-05**: Gold left-accent strips on hero/legendary item cards
- [x] **DESIGN-06**: "Blood-glass" backdrop-blur overlays on tactical overlays (modals, settings panel, screenshot parser)
- [ ] **DESIGN-07**: Parchment noise texture overlay on base background
- [ ] **DESIGN-08**: All existing components pass visual audit against DESIGN.md spec (no rounded corners, no blue links, no #FFFFFF)

### Performance

- [x] **PERF-01**: In-memory DataCache singleton preloads hero and item data at startup, eliminating per-request DB queries
- [x] **PERF-02**: DataCache refreshes atomically on 6h pipeline cycle (coordinated with ResponseCache and RulesEngine invalidation)
- [x] **PERF-03**: Context builder and recommendation engine consume DataCache instead of direct DB queries

### Integration

- [x] **INT-01**: useGsiSync and useAutoRefresh consolidated into single useGameIntelligence hook with one gsiStore subscription
- [x] **INT-02**: Playstyle auto-suggested (first valid option for role) when GSI detects hero and role
- [ ] **INT-03**: Screenshot-parsed KDA and level data fed into recommendation request context for Claude reasoning
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

## Out of Scope

| Feature | Reason |
|---------|--------|
| Hotkey/clipboard screen capture | Manual paste sufficient -- lower complexity |
| Voice coaching | Text-only -- audio adds significant complexity |
| Ability build suggestions | Item-focused only -- abilities are a different domain |
| Mobile optimization | Desktop-first -- Dota 2 is a desktop game |
| User accounts / OAuth | Single-user tool, no auth needed |
| Redis/external caching | In-memory dict sufficient for single-user Unraid deployment |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DESIGN-01 | Phase 17 | Complete |
| DESIGN-02 | Phase 17 | Complete |
| DESIGN-03 | Phase 17 | Complete |
| DESIGN-04 | Phase 17 | Complete |
| DESIGN-05 | Phase 17 | Complete |
| DESIGN-06 | Phase 17 | Complete |
| DESIGN-07 | Phase 17 | Pending |
| DESIGN-08 | Phase 17 | Pending |
| PERF-01 | Phase 16 | Complete |
| PERF-02 | Phase 16 | Complete |
| PERF-03 | Phase 16 | Complete |
| INT-01 | Phase 15 | Complete |
| INT-02 | Phase 15 | Complete |
| INT-03 | Phase 18 | Pending |
| INT-04 | Phase 15 | Complete |
| INT-05 | Phase 16 | Complete |
| INT-06 | Phase 16 | Complete |

**Coverage:**
- v3.0 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-03-26*
*Traceability updated: 2026-03-26*
