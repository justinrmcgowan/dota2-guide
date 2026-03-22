# Requirements: Prismlab

**Defined:** 2026-03-22
**Core Value:** At any point in any game, the player knows exactly what to buy next and why — they never feel lost on itemization.

## v1.1 Requirements

Requirements for v1.1 release. Each maps to roadmap phases.

### Allied Synergy

- [ ] **ALLY-01**: Allied heroes are passed to Claude context builder for recommendation reasoning
- [ ] **ALLY-02**: Recommendations avoid duplicating team aura/utility items (Pipe, Vlads, Crimson, etc.)
- [ ] **ALLY-03**: Recommendations factor in allied combo/setup potential (Enigma + follow-up items, Magnus + BKB priority)
- [ ] **ALLY-04**: Recommendations identify and fill team role gaps (missing stuns, save, wave clear) via item priorities

### Neutral Items

- [ ] **NEUT-01**: Neutral item data (name, tier, effects) stored in database
- [ ] **NEUT-02**: Dedicated "Best Neutral Items" section in recommendations ranked by tier (T1-T5)
- [ ] **NEUT-03**: Inline neutral item callouts in phase reasoning when a neutral item changes the build path

### Polish & Tech Debt

- [ ] **DEBT-01**: Remove unused frontend item API methods and other dead code
- [ ] **DEBT-02**: Wire /admin endpoint through Nginx reverse proxy
- [ ] **DEBT-03**: Fill test coverage gaps from v1.0 sprint
- [ ] **DEBT-04**: General UI polish — loading states, error messages, edge cases

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Live Game Integration

- **GSI-01**: Auto-detect game state from Dota 2 Game State Integration
- **GSI-02**: Auto gold/net worth tracking from GSI data
- **GSI-03**: Screenshot/scoreboard parsing for enemy item detection

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile optimization | Desktop-first — don't break on mobile but don't optimize for it |
| Real-time voice coaching | High complexity, not core to itemization value |
| Multi-game history / analytics | Build advisor, not analytics platform |
| OAuth / user accounts | Single-user tool, no auth needed |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ALLY-01 | Pending | Pending |
| ALLY-02 | Pending | Pending |
| ALLY-03 | Pending | Pending |
| ALLY-04 | Pending | Pending |
| NEUT-01 | Pending | Pending |
| NEUT-02 | Pending | Pending |
| NEUT-03 | Pending | Pending |
| DEBT-01 | Pending | Pending |
| DEBT-02 | Pending | Pending |
| DEBT-03 | Pending | Pending |
| DEBT-04 | Pending | Pending |

**Coverage:**
- v1.1 requirements: 11 total
- Mapped to phases: 0
- Unmapped: 11

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after initial definition*
