# Phase 30: ML Win Predictor - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Statistical win probability prediction from hero compositions using XGBoost trained on OpenDota match data, with precomputed synergy and counter matrices, displayed inside the existing WinConditionBadge alongside qualitative strategy classification.

</domain>

<decisions>
## Implementation Decisions

### Data Acquisition
- OpenDota SQL Explorer for bulk match data (free, up to 200k rows per query, SQL-level patch/rank filtering)
- Current patch only (7.41) — most accurate for current meta
- 4 MMR brackets: Herald-Crusader, Archon-Legend, Ancient-Divine, Immortal
- Manual retraining script — run when new patch drops, not scheduled

### Model & Feature Design
- XGBoost classifier — standard for Dota prediction, handles non-linear hero interactions
- One-hot hero encoding — binary 252-dim vector (126 per team), simple and proven
- Hero-only features — no role encoding, positions implicit in draft context
- One model per MMR bracket (4 total)

### Matrix Granularity
- 50-match minimum per hero pair to include in synergy/counter matrices
- Pool across brackets when a pairing has insufficient data in a specific bracket — some signal better than none
- 4 brackets for synergy/counter matrices matching the model brackets

### Win Probability Display
- Win probability percentage displayed inside existing WinConditionBadge — e.g. "Teamfight 54%"
- Opacity-based confidence encoding (100/75/50) matching WinConditionBadge pattern — no text labels
- Appears alongside Claude's qualitative win condition so users see both statistical and reasoning signals

### Claude's Discretion
- XGBoost hyperparameters and training pipeline details
- SQL query structure for OpenDota Explorer
- Synergy/counter matrix storage format (JSON, SQLite, pickle)
- API endpoint design for serving predictions
- How to handle partial drafts (<10 heroes) — could show partial prediction or wait for complete draft

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `prismlab/backend/engine/win_condition.py` — WinConditionClassifier with draft archetype classification
- `prismlab/frontend/src/components/timeline/WinConditionBadge.tsx` — displays archetype pills with opacity-based confidence
- `prismlab/backend/data/opendota_client.py` — existing OpenDota API client (extend for SQL Explorer)
- `prismlab/backend/scripts/generate_training_data.py` — existing training data generation pattern (Phase 26)
- `prismlab/backend/data/cache.py` — DataCache singleton pattern for precomputed data

### Established Patterns
- Zustand stores for frontend state
- DataCache with frozen dataclasses for backend cached data
- Post-LLM enrichment pattern (add data after Claude generates, don't send to Claude)
- Three-cache coherence (DataCache + RulesEngine + ResponseCache)

### Integration Points
- WinConditionBadge.tsx — add win probability prop
- RecommendResponse schema — add win_probability field
- /api/recommend endpoint — compute and include win probability
- DataCache — load precomputed matrices on startup

</code_context>

<specifics>
## Specific Ideas

- Win probability should feel like an enhancement to the existing WinConditionBadge, not a separate feature
- The "54%" number next to "Teamfight" gives users a quick statistical gut-check alongside the qualitative assessment
- Synergy/counter matrices are a byproduct of training that Phase 31 (Hero Selector) will consume

</specifics>

<deferred>
## Deferred Ideas

- Real-time draft tracking during captain's mode (v7.0+)
- Hero embeddings / hero2vec for richer feature engineering (future iteration)
- Role-aware model (carry Lina vs support Lina) — data fragmentation concern
- Confidence text labels ("Low confidence") — opacity pattern is sufficient

</deferred>
