# Requirements: v6.0 Draft Intelligence

**Defined:** 2026-03-29
**Core Value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.

## ML Win Prediction

- [ ] **PRED-01**: Given a full 10-hero draft, the system predicts win probability as a percentage for the allied team
- [ ] **PRED-02**: Win predictions are trained on 200k+ recent matches from OpenDota bulk data, filtered to current patch
- [ ] **PRED-03**: Precomputed synergy matrix scores hero pairs by observed win rate delta vs independent pick rates, segmented by MMR bracket
- [ ] **PRED-04**: Precomputed counter matrix scores hero matchups by observed win rate when opposing, segmented by MMR bracket
- [ ] **PRED-05**: Win probability displays alongside Claude's qualitative win condition assessment so users see both statistical and reasoning-based signals

## Hero Selection

- [ ] **HERO-01**: Given a partial draft (0-9 heroes), user's role (Pos 1-5), and lane, the system suggests top N hero picks ranked by predicted win rate
- [ ] **HERO-02**: Hero suggestions factor in synergy with already-picked allies and counter-value against already-picked enemies
- [ ] **HERO-03**: Suggestions are filtered by role/lane viability (heroes that can play the selected position)
- [ ] **HERO-04**: Hero suggestion UI integrates into the existing draft input flow as an optional "Suggest Hero" step before recommendations

## Future Requirements

(None — v6.0 is focused)

## Out of Scope

- Real-time draft tracking during captain's mode (live ban/pick integration) — v7.0+
- MMR-specific UI (showing different suggestions per rank) — single bracket for now
- Counter-pick explanations from ML model (use Claude reasoning instead)

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29*
