# Phase 33: Game Analytics & Match Logging - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning
**Mode:** Auto-generated (--auto flag, recommended defaults selected)

<domain>
## Phase Boundary

Log every match with full game data and recommendation tracking. Store in DB for analyzing recommendation effectiveness over time. Provide a match history dashboard for reviewing past games and accuracy metrics.

</domain>

<decisions>
## Implementation Decisions

### Data Capture
- **D-01:** Capture a full end-of-game snapshot when game ends (match_id change or POST_GAME state detected by Phase 27 lifecycle logic).
- **D-02:** Data points per match: match_id, hero_id, hero_name, role, playstyle, side, lane, allies (hero_ids), opponents (hero_ids), lane_opponents, game_length (seconds), win/loss, kills, deaths, assists, GPM, XPM, net_worth, last_hits, denies.
- **D-03:** Items data: final inventory (6 slots + backpack + neutral), items purchased during game (from GSI tracking), has_aghanims_shard, has_aghanims_scepter.
- **D-04:** Recommendation tracking: store the full recommendation response (phases + items) alongside the items actually purchased. Calculate follow-rate (recommended items bought / total recommended).
- **D-05:** Capture timestamp, engine_mode used (fast/auto/deep), and whether it was a fallback response.

### Storage Schema
- **D-06:** Normalized SQLAlchemy tables:
  - `match_log` — one row per match (match_id PK, hero, role, win, duration, KDA, GPM, XPM, timestamps)
  - `match_items` — one row per item slot (FK to match_log, slot_type, item_id, item_name)
  - `match_recommendations` — one row per recommended item (FK to match_log, phase, item_id, item_name, priority, was_purchased bool)
- **D-07:** Keep all data indefinitely. No auto-delete or retention policy.
- **D-08:** SQLite (existing DB). No new database — add tables to existing `prismlab.db`.

### Match History UI
- **D-09:** New page/view accessible from a "Match History" link in the header.
- **D-10:** Main view: sortable table with columns: date, hero (icon), role, result (W/L), duration, KDA, GPM, follow-rate %, mode.
- **D-11:** Expandable row detail: full item build, recommendations given, which were followed, overall_strategy text.
- **D-12:** Filters: hero, win/loss, date range, mode (fast/auto/deep).

### Accuracy Metrics
- **D-13:** Primary metric: **Follow Rate** — (recommended items that were purchased / total items recommended) per match.
- **D-14:** Secondary metric: **Win Rate by Follow Rate** — do games where more recommendations were followed have higher win rates?
- **D-15:** Display aggregate stats at top of match history: total games, win rate, average follow rate, average follow rate on wins vs losses.

### Claude's Discretion
- Backend endpoint design (REST routes for match history + stats)
- Frontend routing approach (React Router or conditional render)
- Table component library (or custom Tailwind table)
- Chart library for accuracy visualizations (if any)
- GSI end-of-game data extraction timing

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Game Lifecycle (captures end-of-game)
- `prismlab/frontend/src/hooks/useGameIntelligence.ts` — New game detection via match_id change (Phase 27). This is where end-of-game snapshot capture should trigger.
- `prismlab/frontend/src/stores/gameStore.ts` — Has hero, role, allies, opponents, lane data (persisted via localStorage)
- `prismlab/frontend/src/stores/recommendationStore.ts` — Has recommendations data, purchased/dismissed items
- `prismlab/frontend/src/stores/gsiStore.ts` — Live GSI state with KDA, GPM, items, match_id, game_state

### Backend Data Layer
- `prismlab/backend/data/models.py` — Existing SQLAlchemy models (extend with match_log tables)
- `prismlab/backend/data/database.py` — DB session management
- `prismlab/backend/main.py` — Router registration

### Frontend Layout
- `prismlab/frontend/src/components/layout/Header.tsx` — Add Match History link
- `prismlab/frontend/src/App.tsx` — Add routing/view switching

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 27's `useGameIntelligence` already detects game end (match_id change) — hook into this for capture trigger
- `gameStore` + `recommendationStore` + `gsiStore` have ALL the data needed at game end — just snapshot and POST to backend
- Existing SQLAlchemy + async session pattern in `database.py`
- Tailwind table styling patterns throughout the app

### Established Patterns
- FastAPI routers in `api/routes/` — add `match_history.py`
- Pydantic models for request/response schemas in `engine/schemas.py`
- Zustand stores with localStorage persist (Phase 27)

### Integration Points
- `useGameIntelligence` match_id change detection → trigger snapshot POST
- New `POST /api/match-log` endpoint to receive end-of-game data
- New `GET /api/match-history` endpoint with filters for the UI
- New `GET /api/match-stats` endpoint for aggregate metrics
- Header component → add Match History navigation link

</code_context>

<specifics>
## Specific Ideas

- The capture must happen BEFORE the clear() call in useGameIntelligence's new-game detection — snapshot the stores, POST to backend, THEN clear
- Follow-rate is the key metric: "did the player actually buy what we recommended?"
- This data becomes the foundation for the custom LLM training (Phase 26) — real match outcomes validate recommendation quality

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 33-game-analytics*
*Context gathered: 2026-03-28*
