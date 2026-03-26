# Project Research Summary

**Project:** Prismlab v3.0 — Design Overhaul & Performance
**Domain:** Design system migration, in-memory caching, store/hook consolidation, integration gap fixes
**Researched:** 2026-03-26
**Confidence:** HIGH

## Executive Summary

Prismlab v3.0 is a focused overhaul of an existing, shipping Dota 2 item advisor. It replaces the "spectral cyan" design language with a "Tactical Relic Editorial" aesthetic: obsidian surfaces, crimson/gold accents, Newsreader serif display type, Manrope body text, and 0px sharp corners throughout. Research confirms this is entirely achievable within the existing stack (React 19, Vite 8, Tailwind v4.2, FastAPI, SQLite) with zero net new dependencies. Two npm font packages are swapped and no backend packages are added. The `@theme` block in `globals.css` is the single highest-leverage file in the migration — rewriting it propagates the design change to every component simultaneously, after which a systematic component sweep replaces old class names with new ones across roughly 30 components.

The two performance work items are equally well-scoped. The backend currently makes 12-20 SQLite queries per recommendation request for hero and item data that only changes every 6 hours. A Python dict singleton (`DataCache`) loaded at startup eliminates those to 1-5 queries per request, with atomic reload after each pipeline cycle. On the frontend, two hooks (`useGsiSync` and `useAutoRefresh`) independently subscribe to `gsiStore` on every 1Hz GSI tick. Merging them into a single `useGameIntelligence` hook halves subscription overhead, enforces correct ordering (hero is set before event detection checks for it), and provides the natural insertion point for the new playstyle auto-suggest feature.

The primary execution risk is sequencing. The design migration touches every component file, the store consolidation touches all hooks and top-level `App.tsx`, and doing both simultaneously creates unmergeable diffs and undiagnosable regressions. Research is emphatic: finish behavioral changes (tech debt, store consolidation) before any visual migration begins. Cache work is backend-only and can run independently. The most dangerous technical pitfalls are stale-cache coherence after pipeline refresh — three cache layers must invalidate in the right order — and cross-store write cycles during hook consolidation, where Zustand's synchronous subscribe API can cascade if a subscription callback writes back to a subscribed store.

## Key Findings

### Recommended Stack

The existing stack requires no structural changes. The two font packages (`@fontsource/inter`, `@fontsource/jetbrains-mono`) are replaced with variable-font equivalents (`@fontsource-variable/newsreader`, `@fontsource-variable/manrope`). Variable fonts serve all weights from a single file, reducing the current 6 font CSS imports to 2 and gaining the `opsz` optical sizing axis required for Newsreader at display scale. Every other design system requirement — surface hierarchy, ambient glow shadows, backdrop blur, noise texture, ghost borders, 0px radius — maps directly to existing Tailwind v4 capabilities and requires only `@theme` configuration values, not new tooling.

The backend data cache uses Python's stdlib `dict` as a module-level singleton. This is the correct tool: single-process uvicorn, approximately 2MB of data, atomic refresh on a 6-hour schedule, and no need for per-key TTL eviction. Redis, `cachetools`, and `fastapi-cache` are all explicitly ruled out as over-engineering for this use case. The pattern is already proven twice in this codebase (`RulesEngine` lookup dicts and `ResponseCache`). Zustand's `.subscribe()` API for hook consolidation requires no new packages — the existing stores stay separate per Zustand's recommended separation of concerns, and only the subscription hooks collapse.

**Core technologies (v3.0 changes only):**
- `@fontsource-variable/newsreader` v5.2.10: Display/headline font — variable font with `opsz` axis, single file replaces multiple weight imports
- `@fontsource-variable/manrope` v5.2.8: Body/label/stat font — replaces Inter + JetBrains Mono, supports `tnum` feature setting for stat displays
- Tailwind v4.2 `@theme` block: All design tokens (surfaces, accents, shadows, typography, radius reset) — already in use, values and token names swapped
- Python stdlib `dict` singleton (`DataCache`): In-memory hero/item data cache — eliminates 8+ DB queries per recommendation request, zero new pip packages
- Zustand v5 `.subscribe()`: Single consolidated hook subscription — no new API, behavioral refactor only

### Expected Features

**Must have (table stakes — defines the milestone):**
- "Tactical Relic Editorial" full retheme — incomplete migration leaves a visual Frankenstein; all ~30 components must be updated; `@theme` token swap in `globals.css` handles ~60% of the visual change instantly
- In-memory hero/item data cache — eliminates 6-8 unnecessary SQLite queries per recommendation; measurable latency reduction during live games with 2-minute auto-refresh cycling
- Store subscription consolidation (`useGsiSync` + `useAutoRefresh` -> `useGameIntelligence`) — halves 1Hz GSI subscription overhead and fixes a latent ordering bug where auto-refresh can fire before hero detection completes

**Should have (high value, low implementation cost):**
- TriggerEvent type deduplication — identical interface defined in two files; one-line fix, an active maintenance hazard if deferred
- `refresh_lookups()` session safety fix — using the same SQLAlchemy AsyncSession for upsert and lookup reload violates the "AsyncSession per task" contract; two-line fix
- Playstyle auto-suggest on GSI hero+role detection — three lines inside the consolidated hook; removes a mandatory manual step during live games
- Parchment noise texture and blood-glass overlays — CSS-only additions; elevates the aesthetic from dark theme to the intended editorial artifact

**Defer to v3.x point release:**
- Screenshot KDA feed-through — feeds parsed enemy KDA/level into Claude context for snowball/deficit itemization reasoning; requires coordinated schema changes across `RecommendRequest`, `gameStore`, `ScreenshotParser`, and `context_builder`; high value but disproportionate coordination cost to include in the same release as the design overhaul

### Architecture Approach

The three main work streams are structurally independent and can be sequenced without merge conflicts, provided behavioral changes (store consolidation, tech debt) are completed before the design migration sweep. Cache work is entirely backend and can be reviewed independently from any frontend work. The design migration is frontend-only (one CSS file plus ~30 component class updates). The store consolidation is hooks and stores only, with no component class changes involved. This independence is the central scheduling insight for the roadmap.

**Major components:**
1. `globals.css @theme block` — single source of truth for all design tokens; rewriting it propagates the full visual change globally; the most leveraged file in v3.0
2. `DataCache` at `backend/data/cache.py` (new) — singleton holding all heroes and items as frozen dataclasses; serves `ContextBuilder`, `Recommender`, `RulesEngine`, and API routes; invalidates atomically after each data pipeline cycle; eliminates the `RulesEngine.init_lookups()` and `refresh_lookups()` methods entirely
3. `useGameIntelligence` at `src/hooks/useGameIntelligence.ts` (new) — replaces `useGsiSync` and `useAutoRefresh`; single subscription callback with explicit step ordering: hero detection, role inference, playstyle suggest, item marking, game state guard, lane detection, event trigger, refresh dispatch

### Critical Pitfalls

1. **Three-cache coherence after pipeline refresh** — After `refresh_all_data()` completes, all three cache layers must invalidate in order: DataCache reloads from a fresh DB session, RulesEngine reads from DataCache (no separate reload step needed), ResponseCache clears entirely. Skipping any step or using the pipeline's existing session for the reload causes stale data. Prevention: explicit ordered reload sequence in `refresh.py`; DataCache always creates its own `AsyncSession` and never accepts the pipeline's session.

2. **Cross-store subscription cascade in consolidated hook** — Writing to Store B from inside a Store A subscription callback triggers Store B subscribers synchronously within the same microtask. `fireRefresh()` writes to `recommendationStore`; if the consolidated hook also subscribes to `recommendationStore` in the same callback path, a render loop results. Prevention: keep `gsiStore` subscription and `recommendationStore` subscription as separate `useEffect` blocks even within the same hook file; use `getState()` to read from a store without subscribing.

3. **Font swap causes layout thrash on dense UI elements** — Newsreader has dramatically different metrics than Inter. Elements with hard-coded pixel widths (e.g., `max-w-[56px]` on ItemCard gold costs) will overflow when Newsreader loads. FOUT from a CDN round-trip amplifies this. Prevention: self-host fonts via `@fontsource-variable/*` packages (no external CDN dependency at Docker runtime); add `font-display: swap` with `size-adjust` fallback metrics; preload font files in `index.html`; test with network throttling before shipping.

4. **Color token removal causes silent invisible text** — Tailwind v4 purges utilities for tokens not in `@theme` at build time without any compile error. Removing `--color-cyan-accent` before all components are migrated renders `text-cyan-accent` as no-match (transparent) silently. Prevention: two-stage migration — add all new tokens alongside old ones first; grep confirms zero old-token references; only then remove old tokens.

5. **Cache startup ordering on cold deploy** — If `DataCache.load()` fires before `seed_if_empty()` completes, the cache loads empty dicts and the first recommendation request sends Claude a prompt with "Hero #X" and "Item #Y" instead of real names. Prevention: strict lifespan sequence in `main.py`: `create_tables -> seed_if_empty -> data_cache.load -> RulesEngine(cache=data_cache) -> start_scheduler`; add a readiness gate to the `/health` endpoint.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Tech Debt and Store Consolidation
**Rationale:** Behavioral changes must come first. Store consolidation, TriggerEvent dedup, and the session safety fix are small, testable, behavior-preserving changes. Completing them before the design migration means hook logic is stable and well-tested before ~30 component files change simultaneously. Debugging a Zustand render loop inside a half-migrated UI is significantly harder than debugging it in isolation against known-good visuals.
**Delivers:** Single `useGameIntelligence` hook replacing `useGsiSync` and `useAutoRefresh`; TriggerEvent as a single source of truth; safe session handling in the refresh pipeline; playstyle auto-suggest (3 lines, natural insertion point within the consolidated hook)
**Addresses features:** Store consolidation, TriggerEvent dedup, session safety, playstyle auto-suggest
**Avoids:** Cross-store cascade render loop (Pitfall 5), TriggerEvent double-fire amplification during consolidation (Pitfall 11), intermediate-state flicker from batched hero+role+playstyle writes (Pitfall 15)

### Phase 2: Backend Data Cache
**Rationale:** Entirely backend with no frontend surface area; can run in parallel with Phase 1 if two developers are available, or sequentially as a focused diff. The cache architectural change — injecting `DataCache` into `RulesEngine`, `ContextBuilder`, and `Recommender` — is significant enough to deserve its own phase and review cycle rather than being buried in a hook or design migration PR.
**Delivers:** `DataCache` singleton with frozen dataclass hero/item storage; `RulesEngine` simplified (no `init_lookups`/`refresh_lookups` methods); context builder and recommender read from cache; DB queries per recommendation reduced from 12-20 to 1-5; `/api/heroes` and `/api/items` routes serve from cache
**Uses:** Python stdlib dict, frozen dataclasses, async SQLAlchemy (fresh session per task per SQLAlchemy docs)
**Implements:** DataCache architecture component; correct refresh lifecycle ordering across three cache layers
**Avoids:** Stale cache after pipeline refresh (Pitfall 3), session sharing between pipeline and reload (Pitfall 4), empty cache on cold start (Pitfall 8), context builder bypassing cache and negating the performance gain (Pitfall 10)

### Phase 3: Design System Migration
**Rationale:** Comes last because it touches every component file. With Phase 1 (hooks stable and tested) and Phase 2 (backend stable) complete, the design migration is a pure visual change with no behavioral risk. The `@theme` token swap in `globals.css` is the single highest-leverage change — one file edit, instant global effect. The subsequent component sweep is mechanical class-name substitution and low cognitive load.
**Delivers:** Full "Tactical Relic Editorial" visual identity; Newsreader/Manrope fonts self-hosted; obsidian surface hierarchy (7 tones); crimson/gold accent system; 0px corners throughout (with documented exceptions); parchment noise texture on body; blood-glass overlays on modals; gold-leaf accent strips on item cards; ambient glow shadows on floated elements
**Build order within phase:** Install fonts -> rewrite `globals.css` -> `App.tsx` root container -> layout shell (Header, Sidebar, MainPanel) -> interactive primitives (GetBuildButton, pickers) -> content components (ItemCard, PhaseCard, NeutralItemsSection) -> modals and overlays (ScreenshotParser, SettingsPanel) -> status indicators (GsiStatusIndicator, GameClock, AutoRefreshToast, LiveStatsBar) -> `constants.ts` color strings
**Avoids:** Invisible text from premature token removal (Pitfall 6), layout thrash from font swap (Pitfall 1), functional roundedness broken by blanket 0px enforcement (Pitfall 2), wrong surface-level nesting making elements invisible (Pitfall 7), backdrop-blur frame drops on 1Hz-updated elements (Pitfall 13)

### Phase 4: Screenshot KDA Feed-Through (deferred point release)
**Rationale:** The only cross-stack schema change in v3.0. Deferred because it requires coordinated changes across `RecommendRequest`, `gameStore`, `ScreenshotParser`, `context_builder`, and the recommendation hook — touching the full data path simultaneously. The value is real (richer Claude context for snowball/deficit itemization: "Enemy PA is 8-1-3 and level 16 — she is snowballing, prioritize defensive items") but the coordination cost is disproportionate to include in the same release as the design overhaul and cache refactor.
**Delivers:** `RecommendRequest.enemy_hero_stats` optional field; `gameStore.enemyHeroStats` and `setEnemyHeroStats` action; `ScreenshotParser` Apply action writes parsed stats to game store; "Enemy Status" section in `context_builder` (kills/deaths/assists/level per enemy hero); richer Claude reasoning about enemy economic state and timing windows

### Phase Ordering Rationale

- Behavioral-first, visual-last: the design migration creates the largest diff volume in the codebase; having stable, tested behavior underneath prevents visual regressions from masking logic bugs, and keeps the design review focused on aesthetics rather than debugging
- Cache work is backend-isolated: no frontend surface area means it can be reviewed and deployed independently without understanding design context
- TriggerEvent dedup is a hard prerequisite for safe store consolidation: the consolidation refactors the exact code path that uses this type, and having two definitions during that refactor would introduce ambiguity
- Playstyle auto-suggest belongs in Phase 1 because it requires the consolidated hook's explicit step ordering to work correctly; inserting it into the existing dual-subscription architecture would be placing it in the wrong hook
- Screenshot KDA is isolated in Phase 4 because it requires simultaneous changes to both the backend request schema and frontend state shape; earlier phases can be reviewed without understanding the full cross-stack flow

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Store Consolidation):** The exact subscription callback structure for `useGameIntelligence` requires careful design review to avoid the cascade pitfall. Existing tests for `useGsiSync` and `useAutoRefresh` need a migration plan since some test cases may not map 1:1 to the consolidated hook's combined behavior.
- **Phase 3 (Design Migration):** The DESIGN.md specification for surface-level assignment per component (which of the 7 surface tiers each UI element gets) must be resolved before implementation starts. PITFALLS.md recommends producing a component-to-surface mapping document as a prerequisite to the migration sweep.

Phases with standard patterns (skip research-phase):
- **Phase 2 (Backend Cache):** Architecture fully specified in ARCHITECTURE.md with concrete class signatures, frozen dataclass definitions, file-level integration points, and startup lifecycle. No open unknowns.
- **Phase 4 (Screenshot KDA):** Data flow fully mapped in FEATURES.md with schema field names, store action names, and context builder section format. Standard schema-extension pattern with no novel integrations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All packages verified on npm registry. Tailwind v4 `@theme` capabilities verified against official docs. Python dict cache pattern proven twice in this codebase already. No speculative dependencies. |
| Features | HIGH | Codebase fully audited — feature list is based on direct code inspection, not domain speculation. Complexity estimates and LOC counts are grounded in actual file structure and existing component sizes. |
| Architecture | HIGH | Integration points fully specified with file names, function signatures, and method-level change descriptions. Build order within each phase is explicit. No hand-wavy "then we integrate" steps. |
| Pitfalls | HIGH | Most pitfalls are derived from the actual codebase (known tech debt from PROJECT.md, existing code patterns) rather than generic domain research. The Zustand cascade and SQLAlchemy session pitfalls are confirmed by official documentation and existing issue reports. |

**Overall confidence:** HIGH

### Gaps to Address

- **Component-to-surface mapping:** PITFALLS.md flags that assigning the wrong surface tier to a component causes elements to become invisible against their background. This mapping (Sidebar -> `surface-container-lowest`, MainPanel -> `surface`, PhaseCard -> `surface-container-low`, Modal -> `surface-container-highest`, etc.) must be explicitly resolved before Phase 3 begins. Produce this as a short planning artifact before writing any component code.
- **Functional roundedness exceptions:** DESIGN.md mandates 0px corners but the purchased-item checkmark and GSI status indicator dot use `rounded-full` for semantic meaning (circle = completed). These exceptions need to be catalogued before the component sweep so they are not accidentally removed. PITFALLS.md recommends a `DESIGN_EXCEPTIONS.md` file documenting each intentional deviation with rationale.
- **WCAG contrast on elevated surfaces:** `on_surface` (#E5E2E1) on `surface-container-highest` (#353534) is approximately 4.1:1, which fails WCAG AA for small text (requires 4.5:1). An `on-surface-high-contrast` token should be defined for text on the highest surface tiers. Must be resolved before Phase 3 ships dense data components like ItemCard captions.
- **Playstyle hero mapping completeness:** The `suggestPlaystyle()` utility requires a `HERO_PLAYSTYLE_MAP` covering common heroes (~50-80 entries per ARCHITECTURE.md). This is data authoring work, not code work, and is not captured in the LOC estimates. Allocate explicit time for it within Phase 1.

## Sources

### Primary (HIGH confidence)
- [Tailwind v4 Theme Variables](https://tailwindcss.com/docs/theme) — `@theme` directive, `--color-*`, `--font-*`, `--shadow-*`, `--radius-*` namespaces, companion `--font-*--font-variation-settings` syntax
- [Tailwind v4 Font Family](https://tailwindcss.com/docs/font-family) — `--font-*` custom font pattern and `@font-face` integration
- [Tailwind v4 Box Shadow](https://tailwindcss.com/docs/box-shadow) — custom `--shadow-*` definitions, shadow-color composition
- [Tailwind v4 Backdrop Filter](https://tailwindcss.com/docs/backdrop-filter-blur) — confirms `backdrop-blur-md` = 12px
- [@fontsource-variable/newsreader on npm](https://www.npmjs.com/package/@fontsource-variable/newsreader) — v5.2.10 confirmed via `npm info`
- [@fontsource-variable/manrope on npm](https://www.npmjs.com/package/@fontsource-variable/manrope) — v5.2.8 confirmed via `npm info`
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) — AsyncSession per-task requirement; `expire_on_commit=False` behavior
- [Zustand GitHub](https://github.com/pmndrs/zustand) — store separation patterns; `.subscribe()` synchronous firing behavior

### Secondary (MEDIUM confidence)
- [FastAPI Caching Discussion #3044](https://github.com/fastapi/fastapi/issues/3044) — confirms dict-based caching is safe in single-process FastAPI
- [CSS Grainy Gradients (CSS-Tricks)](https://css-tricks.com/grainy-gradients/) — SVG `feTurbulence` noise texture approach for parchment effect
- [Frontend Migration Guide (frontendmastery.com)](https://frontendmastery.com/posts/frontend-migration-guide/) — component-by-component vs token-swap migration strategy analysis; confirms token-swap is correct for <50 component codebases
- [Zustand Cross-Store Reactivity Discussion #1586](https://github.com/pmndrs/zustand/discussions/1586) — subscription cascade risk pattern
- [Font Loading: FOIT and FOUT](https://dev.to/ibn_abubakre/font-loading-strategies-foit-and-fout-393b) — `font-display: swap` and `size-adjust` fallback font metric matching
- [How to Implement Cache Invalidation in FastAPI](https://oneuptime.com/blog/post/2026-02-02-fastapi-cache-invalidation/view) — ordering guarantees for multi-layer cache invalidation

### Tertiary (LOW confidence)
- [Tailwind CSS v4 Migration Best Practices (2026)](https://www.digitalapplied.com/blog/tailwind-css-v4-2026-migration-best-practices) — confirms two-stage token migration approach; single blog source

---
*Research completed: 2026-03-26*
*Ready for roadmap: yes*
