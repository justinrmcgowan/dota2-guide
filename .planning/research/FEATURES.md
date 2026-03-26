# Feature Research: v3.0 Design Overhaul & Performance

**Domain:** Design system migration (Tailwind v4 retheme), in-memory data caching, store/hook consolidation, integration gap fixes
**Researched:** 2026-03-26
**Confidence:** HIGH (Tailwind v4 @theme already in use, caching patterns well-understood, codebase fully audited)

## Feature Landscape

### Table Stakes (Must Ship for the Milestone to Matter)

Features that must land for v3.0 to feel like a coherent release rather than random patches.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| "Tactical Relic Editorial" full retheme | The entire v3.0 milestone is defined by this. Shipping partial retheme leaves a Frankenstein UI -- half obsidian monolith, half cyan SaaS. Users notice inconsistency more than ugliness | HIGH | Tailwind v4 @theme in globals.css (already exists), Google Fonts (Newsreader + Manrope), all ~30 frontend components | Current globals.css uses oklch cyan/radiant/dire palette with Inter + JetBrains Mono fonts. New system: obsidian #131313 base, crimson #B22222 primary, gold #FFDB3C secondary, Newsreader display + Manrope body. Every component touches color classes. See "Migration Strategy" section below |
| In-memory hero/item data cache | Currently the recommend hot path hits SQLite 6-8 times per request: hero lookup, opponent lookups, item catalog, neutral items, item popularity, item validation. With auto-refresh firing every 2 min during live games, this is unnecessary I/O. Hero and item data changes once per 6h refresh cycle | MEDIUM | Backend lifespan startup, refresh pipeline, context_builder.py, recommender.py, matchup_service.py, heroes.py route, items.py route, screenshot.py route | Load all heroes and items into module-level dicts at startup. Invalidate and reload after refresh_all_data() completes. Every DB query for Hero/Item on the hot path gets replaced with dict lookup. Matchup data stays in SQLite (it is per-pair, large, and fetched on-demand) |
| Store subscription consolidation (useGsiSync + useAutoRefresh) | Both hooks independently subscribe to gsiStore via `.subscribe()` in separate useEffects. Both fire on every GSI tick (1Hz). Both read from gameStore and recommendationStore. This creates duplicate subscription overhead and makes the data flow hard to reason about | MEDIUM | useGsiSync.ts, useAutoRefresh.ts, App.tsx | Merge into single useGsiOrchestrator hook with one gsiStore.subscribe() call that handles hero detection, item auto-marking, lane detection, and event-trigger detection in a single pass. Reduces subscription count from 3 to 1 (the third is the recommendationStore subscription in useAutoRefresh) |
| TriggerEvent type deduplication | TriggerEvent interface is defined identically in both triggerDetection.ts (line 17) and refreshStore.ts (line 3). This is a maintenance hazard -- if one is updated without the other, runtime bugs appear | LOW | triggerDetection.ts, refreshStore.ts | Single source of truth: export from triggerDetection.ts, import in refreshStore.ts. One-line fix plus import update |
| refresh_lookups() session safety | refresh_all_data() calls `_rules.refresh_lookups(session)` using the same session that just committed the refresh. If the session is in a bad state after the commit (edge case with async SQLAlchemy + SQLite), the rules engine gets stale data | LOW | refresh.py, rules.py | Fix: open a fresh async_session() for the refresh_lookups call, or call init_lookups() with its own session. The current pattern works 99% of the time but is architecturally wrong |

### Differentiators (Improve the Product Beyond Maintenance)

Features that actively improve the user experience beyond just "cleaning up."

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| Auto-suggest playstyle when GSI detects hero+role | Currently GSI auto-detects hero and infers role via inferRole(), but playstyle stays null. The user must manually select playstyle before recommendations work. During a live game, every click matters. Auto-suggesting the most common playstyle for that hero+role removes one friction point | LOW | useGsiSync.ts, gameStore.ts, PLAYSTYLE_OPTIONS constant | After GSI sets hero and role, auto-set playstyle to the first option for that role from PLAYSTYLE_OPTIONS. The user set their preference to "Aggressive" in PROJECT.md context -- could also use a stored preference per hero. Implementation: 3-5 lines in the GSI sync hero detection block |
| Feed KDA/level from screenshots into recommendation context | Screenshots already parse kills, deaths, assists, and level per hero (ParsedHero has these fields). But the data is currently display-only in the confirmation UI. Feeding enemy KDA/level into the Claude prompt gives much richer recommendation context: "Enemy PA is 8-1-3 and level 16 -- she is snowballing, you need defensive items NOW" | MEDIUM | schemas.py (RecommendRequest), context_builder.py, screenshotStore.ts, ScreenshotParser.tsx, gameStore.ts | Requires: (1) new optional field on RecommendRequest for enemy_hero_stats, (2) gameStore field to hold parsed enemy stats, (3) ScreenshotParser "Apply" action writes stats to gameStore, (4) context_builder builds "Enemy Status" section from stats. The Claude prompt already handles mid-game context well -- this is additive |
| Design system "parchment texture" noise overlay | DESIGN.md explicitly calls for "low-opacity noise overlay or subtle grain texture to prevent the UI from feeling sterile." This is a small visual touch that elevates the entire experience from "dark theme" to "editorial artifact." Differentiates from every other Dota tool | LOW | New CSS pseudo-element or small SVG noise asset on body/root | A repeating SVG noise pattern at 3-5% opacity over the #131313 background. No JS needed -- pure CSS. ~2KB SVG asset. Performant because it's a single compositing layer |
| "Blood-glass" tactical overlays | DESIGN.md specifies: primary_container (#B22222) with 20-40% opacity and backdrop-blur 12px for tactical overlays. This creates a premium, atmospheric feel for modals, toast notifications, and the screenshot parser overlay | LOW | SettingsPanel.tsx, AutoRefreshToast.tsx, ScreenshotParser.tsx, ErrorBanner.tsx | CSS-only change on 3-4 overlay/modal components. backdrop-filter: blur(12px) is well-supported in modern browsers. Performance: GPU-composited, no layout thrash |
| Gold-leaf accent strips on hero/item cards | DESIGN.md: "If the card represents a Hero or Legendary item, apply a 2px left-side accent strip of secondary_fixed (#FFE16D)." Visual hierarchy improvement that makes important items pop | LOW | PhaseCard.tsx, ItemCard.tsx, NeutralItemSection.tsx | CSS border-left addition. Conditional: only on core/luxury priority items. Trivial implementation |

### Anti-Features (Do NOT Build in v3.0)

| Feature | Why It Seems Useful | Why Avoid | What to Do Instead |
|---------|--------------------|-----------|--------------------|
| Component library extraction (Storybook/design system package) | "We have a design system spec, let's build a proper component library" | Over-engineering for a single-app project with ~30 components. Storybook adds build complexity, maintenance burden, and slows development velocity for zero multi-project benefit | Keep components co-located in src/components/. The DESIGN.md IS the design system documentation. Components follow its rules directly |
| CSS-in-JS migration (styled-components, Emotion) | "Design tokens should live in JS for type safety" | Tailwind v4 @theme already provides CSS-native design tokens with utility class generation. CSS-in-JS adds runtime overhead, bundle size, and fights Tailwind's compilation model | Continue using Tailwind v4 @theme for tokens. Use CSS custom properties for any dynamic values |
| Dark/light theme toggle | "Professional apps need theme switching" | DESIGN.md is explicitly dark-only ("infinite obsidian void"). A light theme would require a completely separate color system, contradict the creative direction, and add significant testing surface | Single dark theme. The obsidian aesthetic IS the brand |
| Redis/Memcached for caching | "In-memory dict won't scale" | This is a single-user desktop app deployed on a personal Unraid server. Total hero count is ~130, total items ~250. A Python dict holds this trivially. Redis adds container complexity and a network hop for no benefit | Module-level Python dict, invalidated on refresh cycle. Total memory: ~200KB |
| Animated page transitions (Framer Motion / React Spring) | "The editorial design needs cinematic transitions" | Adds 30-50KB bundle, complex animation orchestration, and interferes with the app's primary use case (quick reference during a live game). Users alt-tab to check items -- they need instant rendering, not page transitions | CSS transitions for hover states and panel reveals (already in use). No page-level animation |
| Micro-frontend architecture for design system | "Isolate the old theme from the new theme during migration" | The app has ~30 components in a single Vite build. Micro-frontends add routing complexity, build pipeline changes, and module federation config for a migration that takes days, not months | Component-by-component migration within the single Vite app. Use a Tailwind v4 @theme swap to toggle all design tokens at once |

## Migration Strategy: Design System Retheme

The DESIGN.md retheme is the largest feature in v3.0. The correct migration approach depends on the codebase structure.

### Why Component-by-Component is WRONG for This Project

Research shows component-by-component migration works best for apps with 200+ components, multi-team ownership, or month-long migration timelines (source: frontendmastery.com). Prismlab has ~30 components, one developer, and a migration that involves swapping CSS custom properties rather than changing frameworks.

### Why Token Swap + Component Pass is RIGHT

**Step 1: Swap @theme tokens in globals.css (1 change, affects everything)**

The current globals.css already uses Tailwind v4 @theme. The migration is:
- Replace `--color-cyan-accent` with crimson/gold tokens from DESIGN.md
- Replace `--color-bg-primary/secondary/elevated` with obsidian surface hierarchy
- Replace `--font-body` (Inter) with Manrope, add `--font-display` (Newsreader)
- Add surface hierarchy tokens: surface, surface-dim, surface-container-low/high/highest
- Add the full DESIGN.md color palette as custom properties

After this single file change, every Tailwind utility class referencing these tokens updates globally. This handles ~60% of the visual migration instantly.

**Step 2: Component audit pass (systematic, not incremental)**

Walk through each component and:
- Replace hardcoded color classes (e.g., `text-cyan-accent` becomes `text-primary`, `bg-bg-secondary` becomes `bg-surface-container-low`)
- Remove all `rounded-lg` and `rounded` classes (DESIGN.md mandates 0px corners)
- Remove all `border` classes that create visible borders (DESIGN.md "No-Line Rule")
- Add Newsreader font to headlines (`font-display`)
- Add gold-leaf accent strips where appropriate

**Step 3: Add new design elements**
- Parchment noise texture on body
- Blood-glass overlays on modals/toasts
- Ambient glow shadows (crimson tint, 5% opacity, 32px blur)
- Ghost borders on interactive elements (outline_variant at 15% opacity)

### Font Loading Strategy

Both Newsreader and Manrope are variable fonts on Google Fonts. Variable fonts store all weights in a single file, reducing HTTP requests.

**Recommended approach:**
1. Self-host via `@fontsource/newsreader` and `@fontsource/manrope` npm packages (eliminates Google Fonts network dependency, critical for Unraid deployment)
2. Load Newsreader 400/700 weights only (display text: regular + bold)
3. Load Manrope 400/500/600/700 weights (body text needs more weight range)
4. Use `font-display: swap` to prevent FOIT (flash of invisible text)
5. Preload the two main weight files in index.html

Total font payload: ~80KB (both variable font files combined). Acceptable for desktop-first app.

## In-Memory Cache Architecture

### What Gets Cached

| Data | Current Location | Size | Refresh Frequency | Cache Strategy |
|------|-----------------|------|-------------------|----------------|
| All heroes (~130) | SQLite Hero table, queried per-request | ~50KB as dicts | Every 6h (refresh pipeline) | Module-level dict[int, Hero], keyed by hero_id |
| All items (~250) | SQLite Item table, queried per-request | ~100KB as dicts | Every 6h (refresh pipeline) | Module-level dict[int, Item], keyed by item_id |
| Hero name lookups | RulesEngine._hero_name_to_id etc. | ~10KB | Already cached at startup | Already done -- model for new caches |
| Matchup data | SQLite MatchupData table | ~50KB per hero pair | On-demand, stale-while-revalidate | KEEP IN SQLITE -- per-pair, large total, on-demand fetching is correct |
| Item popularity | SQLite HeroItemPopularity table | ~5KB per hero | On-demand, stale-while-revalidate | KEEP IN SQLITE -- per-hero, fetched on-demand |

### Hot Path DB Queries Eliminated

Per recommendation request, the following DB queries are replaced with dict lookups:

1. `context_builder._get_hero()` -- called 1 + N times (player hero + each opponent/ally) -- SELECT Hero WHERE id = ?
2. `context_builder._build_popularity_section()` -- SELECT all Items (full table scan to build name map)
3. `context_builder._extract_top_items()` -- SELECT all Items (another full scan for ally build names)
4. `matchup_service.get_relevant_items()` -- SELECT Items WHERE not recipe, not neutral, cost > 0
5. `matchup_service.get_neutral_items_by_tier()` -- SELECT Items WHERE is_neutral AND tier IS NOT NULL
6. `recommender._validate_item_ids()` -- SELECT Item.id, Item.cost, Item.internal_name (full scan)
7. `heroes.list_heroes()` -- SELECT all Heroes ordered by name (frontend hero picker)
8. `items.list_items()` -- SELECT all Items ordered by name (frontend API)

Queries 1-6 fire on every `/api/recommend` call. With auto-refresh during live games (every 2 min), that is 6-8 SQLite queries that could be pure Python dict lookups.

### Implementation Pattern

```python
# data/cache.py -- new module
class DataCache:
    """In-memory cache for hero and item data. Loaded at startup, refreshed on pipeline cycle."""

    def __init__(self):
        self._heroes: dict[int, Hero] = {}
        self._items: dict[int, Item] = {}
        self._items_by_name: dict[str, Item] = {}
        self._loaded = False

    async def load(self, session: AsyncSession):
        """Load all heroes and items from DB into memory."""
        ...

    def get_hero(self, hero_id: int) -> Hero | None: ...
    def get_item(self, item_id: int) -> Item | None: ...
    def all_heroes(self) -> list[Hero]: ...
    def all_items(self) -> list[Item]: ...
    def relevant_items(self, role: int) -> list[dict]: ...
    def neutral_items_by_tier(self) -> dict[int, list[dict]]: ...

# Singleton
data_cache = DataCache()
```

Load in lifespan after seed_if_empty(). Reload after refresh_all_data(). Pass to ContextBuilder, Recommender, routes via dependency injection or direct import.

## Store Subscription Consolidation

### Current Problem

```
App.tsx
  useGsiSync(heroes)      -> subscribes to gsiStore (1 subscription)
  useAutoRefresh()         -> subscribes to gsiStore (1 subscription)
                           -> subscribes to recommendationStore (1 subscription)
                           -> runs 1Hz setInterval
```

Both hooks subscribe to gsiStore independently. On every GSI tick (1Hz):
- useGsiSync fires: checks hero detection, checks item matching
- useAutoRefresh fires: checks game events, checks lane detection, checks cooldown

Both read from gameStore and recommendationStore inside their callbacks, creating implicit cross-store dependencies.

### Consolidated Design

```
App.tsx
  useGsiOrchestrator(heroes) -> single gsiStore subscription (1 subscription)
                              -> single recommendationStore subscription (1 subscription)
                              -> single 1Hz setInterval
```

Single subscription callback handles:
1. Hero auto-detection (from useGsiSync)
2. Item auto-marking (from useGsiSync)
3. Playstyle auto-suggestion (NEW -- from v3.0 feature)
4. Lane result auto-detection (from useAutoRefresh)
5. Event trigger detection (from useAutoRefresh)
6. Cooldown management (from useAutoRefresh)

Benefits:
- One subscription instead of two -- halves the callback overhead per tick
- Single data flow path -- easier to debug
- Natural place to add playstyle auto-suggest without a third subscription
- The recommendationStore subscription (for manual recommend cooldown tracking) stays separate since it triggers on a different store

### Playstyle Auto-Suggest Integration

When GSI detects a hero and infers a role, the consolidated hook also sets playstyle:

```typescript
// Inside the hero detection block:
if (role !== null) {
  useGameStore.getState().setRole(role);
  // Auto-suggest first playstyle for this role
  const defaultPlaystyle = PLAYSTYLE_OPTIONS[role]?.[0];
  if (defaultPlaystyle) {
    useGameStore.getState().setPlaystyle(defaultPlaystyle);
  }
}
```

This is 3 lines of code but eliminates a manual step during live games.

## Screenshot KDA Feed-Through

### Current State

The screenshot parser extracts KDA and level per enemy hero (ParsedHero.kills/deaths/assists/level). The confirmation UI displays these values. When the user clicks "Apply," the items are written to gameStore.enemyItemsSpotted. But KDA/level data is discarded.

### Required Changes

1. **RecommendRequest schema** -- add optional `enemy_hero_stats` field:
   ```python
   enemy_hero_stats: list[dict] | None = None
   # e.g. [{"hero_name": "Anti-Mage", "kills": 8, "deaths": 1, "assists": 3, "level": 16}]
   ```

2. **gameStore** -- add `enemyHeroStats` field and `setEnemyHeroStats` action

3. **ScreenshotParser "Apply" action** -- write parsed hero stats to gameStore.enemyHeroStats

4. **context_builder** -- build "Enemy Status" section when enemy_hero_stats is present:
   ```
   ## Enemy Status (from scoreboard)
   - Anti-Mage: 8/1/3, Level 16 (snowballing, high farm priority)
   - Lion: 2/5/7, Level 11 (behind, likely limited to support items)
   ```

5. **useRecommendation + useAutoRefresh** -- include enemyHeroStats in request payload

### Impact on Recommendations

This gives Claude significantly more context. Current prompt only knows "enemy has BKB." With KDA data, Claude can reason about:
- Snowballing enemies (high K/low D) -> prioritize defensive items
- Feeding enemies (low K/high D) -> can afford greedier build
- Level disparity -> timing window analysis
- Enemy team's economic state -> predict what items they can afford

## Feature Dependencies

```
@theme Token Swap (globals.css)
    |
    v
Component Audit Pass (all ~30 components)
    |
    +-- Parchment Texture (CSS-only, on body)
    +-- Blood-Glass Overlays (CSS-only, on modals)
    +-- Gold-Leaf Accent Strips (CSS-only, on cards)
    +-- Ambient Glow Shadows (CSS-only, on floats)
    +-- 0px Corner Enforcement (remove all rounded-*)
    +-- Newsreader/Manrope Font Integration (npm + CSS)

In-Memory Data Cache (data/cache.py)
    |
    +-- Replace context_builder DB queries
    +-- Replace recommender._validate_item_ids DB query
    +-- Replace heroes.list_heroes DB query
    +-- Replace items.list_items DB query
    +-- Replace matchup_service helper DB queries
    +-- Wire into lifespan startup + refresh pipeline

Store Consolidation (useGsiOrchestrator)
    |
    +-- Merge useGsiSync logic
    +-- Merge useAutoRefresh logic
    +-- Add playstyle auto-suggest (NEW)
    |
    +-- TriggerEvent type dedup (prerequisite cleanup)

Screenshot KDA Feed-Through
    |
    +-- RecommendRequest schema update (backend)
    +-- gameStore field addition (frontend)
    +-- ScreenshotParser Apply action update (frontend)
    +-- context_builder Enemy Status section (backend)
    +-- useRecommendation payload update (frontend)
```

Note: The design retheme and in-memory cache are fully independent workstreams. They can be developed in parallel. Store consolidation depends on TriggerEvent dedup (trivial prerequisite). Screenshot KDA requires both frontend and backend changes but has no dependency on other v3.0 features.

## MVP Recommendation

### Must-ship (defines the milestone):
1. **@theme token swap + component audit** -- This IS v3.0. Ship the design system or the milestone has no identity.
2. **In-memory data cache** -- Eliminates 6-8 unnecessary DB queries per recommendation. Measurable perf win during live games.
3. **Store consolidation** -- Architectural cleanup that makes the playstyle auto-suggest possible and halves subscription overhead.

### Should-ship (high value, low cost):
4. **TriggerEvent dedup** -- One-line fix. No reason to defer.
5. **refresh_lookups session safety** -- Two-line fix. No reason to defer.
6. **Playstyle auto-suggest** -- Three lines inside the consolidated hook. Huge UX win during live games.
7. **Parchment texture + blood-glass overlays** -- CSS-only. Elevates the design from "dark theme" to "editorial artifact."

### Can-defer (higher complexity, lower urgency):
8. **Screenshot KDA feed-through** -- Useful but requires schema changes across the stack. Can ship in a point release.

## Complexity Estimates

| Feature | Frontend LOC | Backend LOC | Test LOC | Risk |
|---------|-------------|-------------|----------|------|
| @theme token swap | ~30 (globals.css) | 0 | 0 | LOW -- single file change |
| Component audit pass | ~400 (class changes across 30 files) | 0 | ~50 (snapshot updates) | MEDIUM -- tedious but mechanical |
| Font integration | ~20 (CSS + npm) | 0 | 0 | LOW |
| Parchment texture | ~10 (CSS) | 0 | 0 | LOW |
| Blood-glass overlays | ~30 (CSS on 4 components) | 0 | 0 | LOW |
| In-memory data cache | 0 | ~150 (new module + wiring) | ~80 | MEDIUM -- must verify cache invalidation works |
| Store consolidation | ~200 (merge 2 hooks) | 0 | ~100 (migrate existing tests) | MEDIUM -- complex logic merge |
| TriggerEvent dedup | ~5 | 0 | 0 | TRIVIAL |
| Session safety fix | 0 | ~10 | ~20 | LOW |
| Playstyle auto-suggest | ~10 | 0 | ~30 | LOW |
| Screenshot KDA feed | ~50 | ~60 | ~80 | MEDIUM -- cross-stack schema change |

**Total estimated:** ~750 frontend LOC, ~220 backend LOC, ~360 test LOC.

## Sources

### Design System Migration
- [Tailwind CSS v4 Migration Best Practices (2026)](https://www.digitalapplied.com/blog/tailwind-css-v4-2026-migration-best-practices)
- [Tailwind CSS v4 Theme Variables (Official Docs)](https://tailwindcss.com/docs/theme)
- [Design Tokens in Tailwind v4 + CSS Variables (2026)](https://www.maviklabs.com/blog/design-tokens-tailwind-v4-2026)
- [Frontend Migration Guide](https://frontendmastery.com/posts/frontend-migration-guide/)
- [Tailwind CSS v4.0 Announcement](https://tailwindcss.com/blog/tailwindcss-v4)

### Font Loading
- [Newsreader on Google Fonts](https://fonts.google.com/specimen/Newsreader)
- [Manrope on Google Fonts](https://fonts.google.com/specimen/Manrope)
- [@fontsource/newsreader on npm](https://www.npmjs.com/package/@fontsource/newsreader)

### Caching Patterns
- [FastAPI Application Events & Startup Logic](https://www.fastapiinteractive.com/fastapi-advanced-patterns/09-events-and-signals/theory)
- [FastAPI Response Caching Patterns](https://www.fastapiinteractive.com/fastapi-advanced-patterns/07-caching-patterns)

### Zustand Store Patterns
- [Working with Zustand (TkDodo)](https://tkdodo.eu/blog/working-with-zustand)
- [Zustand Architecture Patterns at Scale](https://brainhub.eu/library/zustand-architecture-patterns-at-scale)
- [Cross-Store Reactivity Discussion (#1586)](https://github.com/pmndrs/zustand/discussions/1586)
- [Multiple Stores vs Single Store Discussion (#2496)](https://github.com/pmndrs/zustand/discussions/2496)
