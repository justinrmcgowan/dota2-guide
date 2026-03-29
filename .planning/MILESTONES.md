# Milestones

## v5.0 Supreme Companion (Shipped: 2026-03-29)

**Phases completed:** 30 phases, 73 plans, 147 tasks

**Key accomplishments:**

- Dota 2 GSI receiver endpoint with Pydantic payload models, in-memory state manager parsing all D-13 fields, and VDF config file generator
- WebSocket ConnectionManager with 1Hz throttled broadcast loop and Nginx /gsi + /ws proxy configuration with 24-hour idle timeout
- WebSocket hook with exponential-backoff reconnect, Zustand GSI store with tri-state status tracking, header status indicator (green/gray/red dot), and settings slide-over panel with GSI config file download
- Neutral tier calculation, GSI inventory-to-recommendation matching, and rAF counting animation hook -- all TDD with 31 tests
- Cross-store GSI synchronization hook with auto hero/role detection, item auto-marking, and animated gold/GPM/NW/KDA stats bar
- MM:SS game clock in header with neutral item tier highlighting (active ring, past dim, next-tier countdown) driven by GSI game clock
- Extended GSI backend to parse roshan_state and tower counts from buildings data, created pure laneBenchmarks and triggerDetection utility modules with 59 tests total
- Extended GsiLiveState with Roshan/tower fields and created refreshStore with 120s cooldown, queue-latest-only event buffer, and toast notification state
- useAutoRefresh hook detecting 5 GSI event types with 120s cooldown, queue-latest-only, lane auto-detect at 10:00, toast notifications, and cooldown countdown UI
- Claude Vision endpoint with DB-anchored prompt, fuzzy hero/item name matching, and nginx 10MB upload config
- TypeScript types, Zustand screenshotStore with edit actions, API client parseScreenshot method, gameStore bulk action, and global clipboard paste hook
- Screenshot parser modal with confirmation editing, global paste activation, and Apply to Build integration writing parsed opponents and items to gameStore
- Per-IP rate limiter, SHA-256 response cache, FallbackReason error categorization, and system prompt item ID hardening
- Migrated rules engine from hardcoded 74-entry HERO_NAMES dict to DB-backed async lookups and added 6 new deterministic rules for obvious item recommendations
- Backend damage profile sum and playstyle-role validators with frontend auto-rebalancing sliders, reason-specific fallback banners, and friendly 429/422 handling
- HERO_PLAYSTYLE_MAP with ~120 hero+role entries and TriggerEvent deduplicated to single source in triggerDetection.ts
- Consolidated useGsiSync + useAutoRefresh into single useGameIntelligence hook with playstyle auto-suggest via HERO_PLAYSTYLE_MAP
- DataCache singleton with frozen HeroCached/ItemCached dataclasses and 12 zero-DB lookup methods; RulesEngine refactored to consume DataCache via constructor injection
- Eliminated 12-20 DB queries per recommendation request by wiring DataCache into context builder, recommender validation, and API routes with coordinated three-layer cache invalidation
- Newsreader + Manrope variable fonts installed, @theme block replaced with full DESIGN.md obsidian surface hierarchy, crimson/gold/slate accents, ambient glow shadows, and 0px radius overrides
- Obsidian surface hierarchy applied across App/Header/Sidebar/MainPanel shell; all 11 draft-input components and constants migrated from cyan-accent to crimson/gold primary/secondary tokens with Blade and Sacrificial Table patterns
- 12 components migrated to DESIGN.md tokens: Monolith card pattern with gold accent strips on timeline, Blade button and Tactical HUD on game-state panel, No-Line Rule enforced throughout
- Blood-glass overlays with ambient crimson glow on all floating elements (modals, panels, toasts, banners) using surface-container-highest and backdrop-blur-md
- Parchment noise texture overlay via SVG feTurbulence, deprecated bridge tokens removed, full visual audit confirms zero old token references across all components
- End-to-end enemy KDA/level pipeline from screenshot parser through gameStore to Claude's recommendation reasoning with threat annotations
- Commit:
- 1. [Rule 1 - Minor Deviation] On-track win rate in tooltip
- BuildPathSteps.tsx (new file):
- One-liner:
- WinConditionBadge component displaying allied (gold) and enemy (dire-red) archetype pills above ItemTimeline strategy text, with opacity-based confidence encoding and full enemy team wiring via all_opponents.
- Zustand persist audio store + speak() TTS utility with Chrome keepalive + Audio Coaching toggle and volume slider in SettingsPanel
- Stratz GraphQL client (primary) and OpenDota fallback for live match draft fetching, unified behind GET /api/live-match/{account_id} endpoint
- Steam ID configuration in Settings, useLiveDraft polling hook with GSI-triggered auto-population of allies/opponents/side/hero/role from live match API
- Elgato Stream Deck plugin project scaffolded with SDKVersion 2 manifest declaring 6 action UUIDs, BackendConnection singleton with exponential-backoff reconnect to ws://<host>:8420/ws, and buildable TypeScript entry point
- 6 SingletonAction classes with SVG renderers wired to live Dota 2 GSI data via BackendConnection, compiling cleanly with zero TypeScript errors
- Normalized match logging schema (MatchLog + MatchItem + MatchRecommendation) with POST ingestion, paginated history, and aggregate accuracy metrics
- MatchLogPayload types, api.logMatch() client, and end-of-game snapshot-before-clear logic in useGameIntelligence
- MatchHistory page with sortable table, expandable rows showing item builds + recommendation tracking, hero/result/mode filters, and aggregate accuracy stat cards

---

## v3.0 Design Overhaul & Performance (Shipped: 2026-03-27)

**Phases completed:** 4 phases, 10 plans, 19 tasks

**Key accomplishments:**

- HERO_PLAYSTYLE_MAP with ~120 hero+role entries and TriggerEvent deduplicated to single source in triggerDetection.ts
- Consolidated useGsiSync + useAutoRefresh into single useGameIntelligence hook with playstyle auto-suggest via HERO_PLAYSTYLE_MAP
- DataCache singleton with frozen HeroCached/ItemCached dataclasses and 12 zero-DB lookup methods; RulesEngine refactored to consume DataCache via constructor injection
- Eliminated 12-20 DB queries per recommendation request by wiring DataCache into context builder, recommender validation, and API routes with coordinated three-layer cache invalidation
- Newsreader + Manrope variable fonts installed, @theme block replaced with full DESIGN.md obsidian surface hierarchy, crimson/gold/slate accents, ambient glow shadows, and 0px radius overrides
- Obsidian surface hierarchy applied across App/Header/Sidebar/MainPanel shell; all 11 draft-input components and constants migrated from cyan-accent to crimson/gold primary/secondary tokens with Blade and Sacrificial Table patterns
- 12 components migrated to DESIGN.md tokens: Monolith card pattern with gold accent strips on timeline, Blade button and Tactical HUD on game-state panel, No-Line Rule enforced throughout
- Blood-glass overlays with ambient crimson glow on all floating elements (modals, panels, toasts, banners) using surface-container-highest and backdrop-blur-md
- Parchment noise texture overlay via SVG feTurbulence, deprecated bridge tokens removed, full visual audit confirms zero old token references across all components
- End-to-end enemy KDA/level pipeline from screenshot parser through gameStore to Claude's recommendation reasoning with threat annotations

---

## v2.0 Live Game Intelligence (Shipped: 2026-03-26)

**Phases completed:** 5 phases, 15 plans, 32 tasks

**Key accomplishments:**

- Dota 2 GSI receiver endpoint with Pydantic payload models, in-memory state manager parsing all D-13 fields, and VDF config file generator
- WebSocket ConnectionManager with 1Hz throttled broadcast loop and Nginx /gsi + /ws proxy configuration with 24-hour idle timeout
- WebSocket hook with exponential-backoff reconnect, Zustand GSI store with tri-state status tracking, header status indicator (green/gray/red dot), and settings slide-over panel with GSI config file download
- Neutral tier calculation, GSI inventory-to-recommendation matching, and rAF counting animation hook -- all TDD with 31 tests
- Cross-store GSI synchronization hook with auto hero/role detection, item auto-marking, and animated gold/GPM/NW/KDA stats bar
- MM:SS game clock in header with neutral item tier highlighting (active ring, past dim, next-tier countdown) driven by GSI game clock
- Extended GSI backend to parse roshan_state and tower counts from buildings data, created pure laneBenchmarks and triggerDetection utility modules with 59 tests total
- Extended GsiLiveState with Roshan/tower fields and created refreshStore with 120s cooldown, queue-latest-only event buffer, and toast notification state
- useAutoRefresh hook detecting 5 GSI event types with 120s cooldown, queue-latest-only, lane auto-detect at 10:00, toast notifications, and cooldown countdown UI
- Claude Vision endpoint with DB-anchored prompt, fuzzy hero/item name matching, and nginx 10MB upload config
- TypeScript types, Zustand screenshotStore with edit actions, API client parseScreenshot method, gameStore bulk action, and global clipboard paste hook
- Screenshot parser modal with confirmation editing, global paste activation, and Apply to Build integration writing parsed opponents and items to gameStore
- Per-IP rate limiter, SHA-256 response cache, FallbackReason error categorization, and system prompt item ID hardening
- Migrated rules engine from hardcoded 74-entry HERO_NAMES dict to DB-backed async lookups and added 6 new deterministic rules for obvious item recommendations
- Backend damage profile sum and playstyle-role validators with frontend auto-rebalancing sliders, reason-specific fallback banners, and friendly 429/422 handling

---

## v1.1 Allied Synergy & Neutral Items (Shipped: 2026-03-23)

**Phases completed:** 3 phases, 6 plans, 12 tasks

**Key accomplishments:**

- Removed 3 dead API methods, wired /admin/ through Nginx proxy, added auto-dismiss error toasts and concise empty state text
- 32 unit tests added for recommendationStore (Zustand) and context_builder (Python) covering all store actions, toggle behaviors, midgame formatting, and full prompt assembly
- Allied hero names and popular item builds wired into Claude user message via _build_ally_lines() with OpenDota popularity data
- Team Coordination section with aura dedup, combo awareness, and gap filling rules added to Claude system prompt with ally-aware reasoning example
- Neutral item data pipeline wired end-to-end: seed fix, tier query, schema extension, context catalog, system prompt rules, and recommender passthrough with 14 new tests
- NeutralItemSection component rendering all 5 tiers with ranked picks, per-item reasoning, and Steam CDN images below the purchasable item timeline

---

## v1.0 MVP (Shipped: 2026-03-21)

**Phases completed:** 6 phases, 14 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---
