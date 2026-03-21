# Project Research Summary

**Project:** Prismlab -- Dota 2 Adaptive Item Advisor
**Domain:** Game advisor / hybrid recommendation engine (rules + LLM)
**Researched:** 2026-03-21
**Confidence:** HIGH

## Executive Summary

Prismlab is a Dota 2 item advisor that fills a clear gap in the competitive landscape: no existing tool combines draft/matchup awareness, mid-game adaptation, and natural language reasoning explaining "why" a player should buy a specific item. The market has static guides (Torte de Lini, ImmortalFaith), ML-powered suggestions without explanations (Dota Plus, Dotabuff Adaptive Items), and raw stats platforms (OpenDota, STRATZ, Dota2ProTracker). Prismlab differentiates by being an **item reasoning engine** -- the recommendations are the vehicle, but the matchup-specific explanations are the product. The technology to build this well exists and is mature: React 19 + Vite 8 + Tailwind v4 for the frontend, FastAPI + SQLAlchemy + SQLite for the backend, Claude Sonnet 4.6 with guaranteed structured JSON output for the AI reasoning layer.

The recommended approach is a **hybrid recommendation architecture** where a fast, deterministic rules engine handles obvious item decisions (Magic Stick vs. spell-spammers, Quelling Blade for melee cores) and fires first on every request, while the Claude API provides nuanced, matchup-specific reasoning that references actual hero abilities and game dynamics. The rules layer serves double duty as the fallback when the LLM is slow or unavailable. This pattern is well-validated in recommendation system literature and maps cleanly to the retrieval-augmented generation paradigm. The two-container Docker Compose deployment (React/Nginx frontend + FastAPI backend) is straightforward for the Unraid target.

The key risks are: (1) LLM hallucinating item names or abilities from old patches -- mitigated by passing a complete item ID mapping in every prompt and validating every ID in the response against the database; (2) generic "always-good" recommendations instead of matchup-specific reasoning -- mitigated by enriching the prompt context with opponent abilities and enforcing specificity constraints in the system prompt with few-shot examples; (3) Claude API latency killing mid-game usability -- mitigated by a hard 10-second timeout with instant rules-only fallback; and (4) SQLite locking issues on Unraid Docker volumes -- mitigated by using cache drives (not array drives) and enabling WAL mode from the start.

## Key Findings

### Recommended Stack

The stack is modern, well-documented, and fully compatible. Every major technology has been updated from the original blueprint to current stable versions: React 18 to 19.2.x, Python 3.12 to 3.13.x, Tailwind v3 to v4 (breaking change: CSS-first config replaces `tailwind.config.js`), and Vite 5 to 8 (ships Rolldown, 10-30x faster builds). The Claude model target is Sonnet 4.6 (`claude-sonnet-4-6-20250514`) with structured outputs GA -- no beta headers needed, guaranteed JSON schema compliance at the token generation level.

**Core technologies:**
- **React 19 + Vite 8 + TypeScript:** UI framework with Rust-powered bundler. React Compiler auto-optimizes without manual memoization.
- **Tailwind CSS v4:** CSS-first configuration via `@theme` block. Uses `@tailwindcss/vite` plugin directly, no PostCSS config needed.
- **Zustand 5:** ~1KB state management. Single GameStore with slices pattern for draft, game state, and recommendation data.
- **TanStack Query v5:** Server state management for all backend API calls. Handles caching, loading, error states, and mutation lifecycle.
- **FastAPI + Pydantic v2:** Async API framework with Rust-core validation. Auto-generated OpenAPI docs.
- **SQLAlchemy 2.0 + SQLite:** ORM with synchronous sessions (SQLite doesn't benefit from async drivers). File-based DB on Docker volume.
- **Claude Sonnet 4.6:** Item reasoning engine. ~$0.003-0.01 per recommendation. Structured outputs guarantee valid JSON matching the recommendation schema.
- **httpx:** Async HTTP client for OpenDota REST, Stratz GraphQL, and Claude API calls.

**Critical version notes:**
- Tailwind v4 is a breaking change from v3. No `tailwind.config.js` file. Colors use OKLCH by default.
- Vite 8 plugin ecosystem is updated (`@vitejs/plugin-react` v6 drops Babel for Oxc).
- Use synchronous SQLAlchemy sessions for SQLite, async only for Claude API and external HTTP calls.

### Expected Features

**Must have (table stakes):**
- Searchable hero picker with Steam CDN portraits
- Role/position selection (Pos 1-5)
- Item build organized by game phase (starting, laning, core, situational)
- Lane opponent context (1-2 opponent slots)
- Dark theme with Dota aesthetic (spectral cyan, Radiant/Dire color coding)
- Loading states during LLM calls (2-5 second waits)
- Fallback when Claude API fails (rules-only output)
- Item images with gold cost displayed

**Should have (differentiators -- this is where Prismlab competes):**
- Natural language reasoning per item ("the why") -- core differentiator, no competitor does this
- Playstyle-aware recommendations (aggressive/passive/etc. per role)
- Mid-game re-evaluation with lane result, damage profile, enemy items
- Situational decision trees (branching recommendations, not linear builds)
- Hybrid engine (instant rules + nuanced LLM reasoning)
- Radiant/Dire side awareness (affects lane geometry, Roshan proximity)
- Matchup-specific item data from OpenDota/Stratz
- Click-to-mark items as purchased (for re-evaluation scoping)

**Defer (v2+):**
- In-game overlay (Overwolf/GSI) -- massive complexity, Valve policy risk
- Full allied team synergy analysis -- V1 focuses on "win your lane"
- Neutral item recommendations -- random drops don't fit the advisor model
- Auto gold/net worth tracking -- requires GSI or tedious manual entry
- Build history / session saving -- V1 is ephemeral
- Mobile-optimized layout -- desktop-first matches the second-monitor use case

### Architecture Approach

The system follows a layered hybrid architecture with clear separation between data ingestion, recommendation logic, and presentation. The frontend uses a single Zustand store (with slices for draft, game state, and recommendations) feeding a progressive UI that mirrors how information reveals during an actual Dota game. The backend uses FastAPI dependency injection to compose the Hybrid Recommender from three components: a Rules Engine (deterministic, instant), a Context Builder (assembles prompt from SQLite data), and an LLM Engine (Claude API with structured output). The pipeline pattern ensures rules fire first and their output feeds into the LLM context, so the LLM enhances rather than duplicates obvious decisions.

**Major components:**
1. **Zustand GameStore** -- Single source of truth for all user inputs, recommendations, loading states, and purchased item tracking. Slices pattern with Immer middleware.
2. **Hybrid Recommender** -- Pipeline orchestrator. Rules first, LLM second, merge results. 10-second timeout on LLM with rules-only fallback.
3. **Rules Engine** -- Deterministic item logic: counter items, starting item budgets, role-gated items, lane-specific adjustments. No API call.
4. **LLM Engine** -- Claude API integration with `output_config.format` for guaranteed structured JSON. Handles timing rationale, opportunity cost, playstyle integration, and situational decision trees.
5. **Context Builder** -- Assembles prompt context from SQLite data. Filters item catalog to ~30-50 relevant items (not all 200+). Translation layer between database models and LLM prompt.
6. **Data Layer** -- SQLAlchemy models (Heroes, Items, MatchupData) with synchronous SQLite sessions. Pre-fetched and cached, refreshed daily.
7. **External API Clients** -- httpx-based async clients for OpenDota REST and Stratz GraphQL. Data cached in SQLite, never fetched live during recommendation requests.

### Critical Pitfalls

1. **LLM hallucinating items/abilities from old patches** -- Pass complete item ID-to-name mapping in every prompt. Use `item_id` integer fields in structured output (not freetext names). Validate every ID against the database before returning to frontend. Include a system prompt constraint: "You may ONLY recommend items from the provided item list."

2. **Generic "always-good" recommendations instead of matchup-specific reasoning** -- Enrich prompt context with opponent hero abilities, damage types, and disable durations. System prompt must enforce: "Every reasoning field MUST mention at least one enemy hero by name AND at least one specific ability." Include 3-4 few-shot examples showing good vs. bad reasoning. Post-process to verify enemy hero names appear in reasoning text.

3. **Claude API latency killing mid-game usability** -- Hard 10-second timeout. If exceeded, return rules-only recommendations instantly with a note. Minimize input tokens to ~1500 by filtering items to relevant subset. Cache system prompt (static hero/item data). Pre-compute during draft phase (fire the first API call on hero selection, don't wait for explicit "Get Recommendations" click).

4. **OpenDota/Stratz rate limit exhaustion during data seeding** -- 124 heroes = ~15K matchup pairs. OpenDota free tier: 50K/month, 60/min. Batch and throttle with semaphore-limited async requests. Prioritize: seed constants first (2 calls), lazy-fetch matchup data on demand, pre-populate only top 20 popular heroes. Use bulk endpoints (`/heroStats` returns all heroes in one call).

5. **SQLite locking under Docker on Unraid** -- Store database on cache drive (SSD/NVMe with ext4/XFS), NOT array drive (FUSE-based). Enable WAL mode explicitly. Set PUID/PGID in Docker Compose. Test with actual Unraid deployment early -- don't assume local Docker behavior matches.

6. **Rigid recommendation schema forcing filler items** -- Make phases optional (not every game fills every phase). Include `skip_reason` fields. Support decision trees within any phase. Use array of typed phases rather than fixed named phases. Test schema with diverse scenarios (support with 3-4 items, carry rushing a single item, conditional branches).

## Implications for Roadmap

Based on research, the build order is constrained by data dependencies. The critical path is: data layer -> recommendation engine -> timeline UI. The frontend scaffold and backend engine can be developed in parallel but converge when the end-to-end flow connects.

### Phase 1: Foundation and Data Layer
**Rationale:** Everything depends on having hero, item, and matchup data available. The database schema must include `patch_version` from the start (Pitfall 2). The OpenDota client must have built-in rate limiting from the start (Pitfall 5). Docker Compose and SQLite WAL mode must be validated on Unraid early (Pitfall 6).
**Delivers:** Working backend with SQLite schema, seeded hero/item data from OpenDota, FastAPI shell with data endpoints, React/Vite scaffold with layout shell, HeroPicker component, favicon, theme/typography setup.
**Features addressed:** Hero picker with search, hero/item CDN images, dark theme with Dota aesthetic.
**Pitfalls addressed:** Post-patch data staleness (schema design), OpenDota rate limits (client design), SQLite locking (Docker/WAL config).

### Phase 2: Draft Input UI
**Rationale:** All draft inputs must exist before the recommendation engine has enough context to generate useful results. These are mostly simple UI components that write to the Zustand GameStore. Low risk, high user value.
**Delivers:** Complete draft input sidebar: RoleSelector, PlaystyleSelector, SideSelector, LaneSelector, OpponentPicker. All wired to Zustand GameStore.
**Features addressed:** Role selector, playstyle selector (differentiator), side selector (differentiator), lane selector, opponent picker.
**Pitfalls addressed:** None directly -- this phase is straightforward UI work.

### Phase 3: Recommendation Engine
**Rationale:** This is the highest-risk, highest-value phase. It contains the core product: the hybrid rules + LLM engine. This is where the system prompt must be crafted, the rules engine coded, the context builder tuned, and structured output validated. Budget extra time here.
**Delivers:** Working Rules Engine, Context Builder, LLM Engine, Hybrid Recommender orchestrator, POST /api/recommend endpoint, matchup data ingestion.
**Features addressed:** Rules-based starting items, Claude API integration (core differentiator), hybrid engine orchestrator, fallback mode.
**Pitfalls addressed:** LLM hallucinating items (validation layer), generic recommendations (system prompt + few-shot examples + context enrichment), Claude API latency (timeout + fallback), rigid schema (flexible phase design).

### Phase 4: Item Timeline UI and End-to-End Flow
**Rationale:** Connects frontend to backend. This is where the user first sees recommendations. The API client, Timeline, PhaseCard, and ItemRecommendation components all depend on Phase 2 (store with data) and Phase 3 (engine producing responses).
**Delivers:** API client layer, Timeline with PhaseCards and ItemRecommendation components, loading states, error handling, complete end-to-end flow: select hero -> fill inputs -> get recommendations -> see timeline with reasoning.
**Features addressed:** Item timeline UI with phase cards, reasoning tooltips per item, situational decision tree cards, loading states, item images with cost.

### Phase 5: Mid-Game Adaptation
**Rationale:** Requires the full draft-to-recommendation flow to be working (Phase 4). Adds the "living advisor" concept that further differentiates from competitors. Involves extending both the frontend (new input components, click-to-purchase) and backend (updated prompt context, phase-specific reasoning).
**Delivers:** Click-to-mark purchased items, lane result selector, damage profile input, enemy item tracker, re-evaluate button, phase-specific prompt builders.
**Features addressed:** Mid-game re-evaluation (differentiator), click-to-mark purchased, progressive information flow.
**Pitfalls addressed:** Claude API latency during re-evaluation (optimized prompt, timeout).

### Phase 6: Polish and Data Pipeline
**Rationale:** All features are functional. This phase hardens the system: automated data refresh, error handling throughout, performance optimization, and deployment readiness.
**Delivers:** Data refresh pipeline (daily cron), admin endpoints, error handling for all failure modes, loading skeletons/animations, debouncing, caching, responsive groundwork, Docker health checks.
**Features addressed:** Matchup data pipeline, data refresh scripts, performance optimization, phase progression UI.
**Pitfalls addressed:** Post-patch data staleness (automated refresh + staleness detection), patch version display.

### Phase Ordering Rationale

- **Phase 1 before everything:** The database schema, data seeding, and Docker configuration are prerequisites for all other work. Getting SQLite WAL mode working on Unraid early prevents a costly Phase 6 discovery.
- **Phase 2 and Phase 3 can partially overlap:** Frontend draft inputs and backend engine are independent until Phase 4 connects them. A solo developer should do Phase 3 first (higher risk, needs iteration time), then Phase 2 (lower risk, faster).
- **Phase 3 is the critical risk:** The system prompt, rules engine tuning, structured output schema, and context builder all require iteration. This is not a "code it once and move on" phase -- expect 2-3 rounds of prompt engineering refinement.
- **Phase 4 is the integration checkpoint:** If the end-to-end flow works here, the product is viable. Everything after Phase 4 is enhancement.
- **Phase 5 before Phase 6:** Mid-game adaptation is a key differentiator and should be validated before investing in polish. If the re-evaluation flow doesn't work well, Phase 6 polish won't save the product.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Recommendation Engine):** The system prompt design, few-shot example crafting, and rules engine coverage require domain-specific research. The OpenDota endpoint paths for item popularity and matchup data need verification against the live API. The structured output schema design needs testing with 10+ diverse hero/matchup scenarios before locking down.
- **Phase 5 (Mid-Game Adaptation):** The re-evaluation prompt context (how to communicate "what changed" to the LLM efficiently) and the damage profile input UX need exploration.

Phases with standard patterns (skip deeper research):
- **Phase 1 (Foundation):** Well-documented patterns for FastAPI + SQLAlchemy + SQLite, Docker Compose, Vite scaffold. The only non-standard element is Unraid-specific SQLite configuration.
- **Phase 2 (Draft Input UI):** Standard React component patterns. Zustand store setup is well-documented.
- **Phase 4 (Item Timeline UI):** Standard React rendering. TanStack Query mutation patterns are well-documented.
- **Phase 6 (Polish):** Standard optimization patterns (debounce, caching, error boundaries).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified against official sources. Versions current as of March 2026. Every library has stable releases and active maintenance. |
| Features | HIGH | Competitive landscape thoroughly analyzed (9 competitors). Feature gaps validated against multiple sources. MVP definition is clear and well-scoped. |
| Architecture | HIGH | Hybrid recommendation pattern validated by academic research and industry practice. Component boundaries are clean. Data flow is well-defined. |
| Pitfalls | HIGH | Cross-referenced multiple authoritative sources. SQLite/Docker/Unraid issues confirmed by real community reports. LLM hallucination rates backed by research papers. |

**Overall confidence:** HIGH

### Gaps to Address

- **OpenDota `/heroes/{id}/itemPopularity` endpoint:** Referenced in architecture research but not directly verified against the live API. Needs validation during Phase 1 data client implementation. Fallback: use Stratz GraphQL for item popularity data.
- **Stratz GraphQL schema specifics:** The exact query structure for matchup data filtered by bracket was not directly verified. Needs hands-on exploration during Phase 1. Stratz has API documentation but schema details require interactive testing.
- **Claude system prompt effectiveness:** The system prompt is the heart of the product, but its quality can only be validated empirically. Plan for 2-3 iterations of prompt engineering during Phase 3. The few-shot examples need to be crafted by someone with high-MMR Dota knowledge.
- **Tailwind v4 OKLCH color accuracy:** The CSS-first `@theme` configuration uses OKLCH color values mapped from the blueprint's hex colors (#00d4ff, #6aff97, #ff5555). The OKLCH equivalents need visual verification -- OKLCH and hex don't map 1:1 in all cases.
- **Unraid SQLite validation:** The SQLite WAL mode + Docker volume mount on Unraid is a known risk area. Must be tested on the actual deployment target during Phase 1, not deferred to Phase 6.

## Sources

### Primary (HIGH confidence)
- [React 19.2.1 Versions](https://react.dev/versions) -- Stable release, React Compiler
- [Vite 8.0 Announcement](https://vite.dev/blog/announcing-vite8) -- Rolldown-powered builds
- [Tailwind CSS v4.0](https://tailwindcss.com/blog/tailwindcss-v4) -- CSS-first config, Rust engine
- [FastAPI Documentation](https://fastapi.tiangolo.com/) -- SQL databases, dependency injection patterns
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) -- GA, JSON schema guarantee
- [Claude Sonnet 4.6 Pricing](https://platform.claude.com/docs/en/about-claude/pricing) -- $3/$15 per MTok
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) -- v0.86.0, async support
- [OpenDota API Documentation](https://docs.opendota.com/) -- REST endpoints, rate limits
- [Dota Plus Official Page](https://www.dota2.com/plus) -- Competitor feature set
- [Dota2ProTracker](https://dota2protracker.com/) -- Competitor reference (current patch 7.40c)
- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html) -- Filesystem requirements

### Secondary (MEDIUM confidence)
- [Stratz API](https://stratz.com/api) -- GraphQL API structure (schema not directly verified)
- [Dotabuff Adaptive Items](https://www.dotabuff.com/blog/2021-06-23-announcing-the-dotabuff-apps-new-adaptive-items-module) -- 2021 announcement, features may have evolved
- [OpenDota MCP Server](https://github.com/hkaanengin/opendota-mcp-server) -- Confirms endpoint availability
- [LLM Hallucination Research](https://arxiv.org/pdf/2509.22202) -- 26% rate with name similarity
- [Jellyfin Docker SQLite Issues on Unraid](https://forums.unraid.net/topic/190813-jellyfin-docker-sqlite-unable-to-open-database-file/) -- Real-world Unraid SQLite problems
- [Sequential Item Recommendation in Dota 2](https://arxiv.org/abs/2201.08724) -- Academic research on MOBA item recommendation

### Tertiary (LOW confidence)
- [Stratz GraphQL Schema](https://stratz.com/knowledge-base/API) -- Needs hands-on validation for bracket-filtered matchup queries
- [Spectral Hero Builds](https://builds.spectral.gg/) -- Competitor with basic "explain" feature, small audience

---
*Research completed: 2026-03-21*
*Ready for roadmap: yes*
