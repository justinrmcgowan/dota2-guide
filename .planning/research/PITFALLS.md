# Domain Pitfalls

**Domain:** Design system migration, in-memory caching, store subscription consolidation for existing Dota 2 item advisor
**Researched:** 2026-03-26
**Milestone:** v3.0 Design Overhaul & Performance

---

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or multi-day debugging sessions.

### Pitfall 1: Font Swap Causes Layout Thrashing (FOUT in Dense UI)

**What goes wrong:** Replacing Inter/JetBrains Mono with Newsreader/Manrope changes character widths, line heights, and font metrics. Dense UI elements (ItemCard gold costs, LiveStatsBar KDA numbers, HeroPicker search results, DamageProfileInput sliders) are sized to pixel precision with Inter. When Newsreader loads, FOUT (Flash of Unstyled Text) causes the fallback system font to render first, then the layout snaps when the web font arrives. Newsreader is a serif with dramatically different metrics than sans-serif fallbacks -- text that fit in 56px (`max-w-[56px]` in ItemCard) will overflow or wrap mid-word.

**Why it happens:** The DESIGN.md specifies Newsreader for display/headlines and Manrope for body -- both are Google Fonts that must be fetched at runtime. The current codebase hard-codes pixel widths (e.g., `w-12 h-12`, `max-w-[56px]`) and relies on Inter's metrics for visual alignment.

**Consequences:** Item names truncate incorrectly, gold cost labels shift position, phase card headers overflow their containers, and the entire sidebar layout may jump 4-8px when fonts load. During a live game with GSI active, this layout jump can cause misclicks on item cards.

**Prevention:**
1. Add `font-display: swap` in the `@font-face` rules and specify fallback fonts with matching metrics (`size-adjust`, `ascent-override`, `descent-override` properties) to minimize layout shift.
2. Preload both font files with `<link rel="preload" as="font">` in `index.html` so they arrive before first paint.
3. Replace all hard-coded pixel widths with relative units or min-width/max-width pairs that accommodate both font stacks.
4. Test with network throttling (Slow 3G) to observe the full FOUT flash before shipping.

**Detection:** Core Web Vitals CLS (Cumulative Layout Shift) score degrades. Visually, text "jumps" on first page load.

**Phase relevance:** Design system migration phase. Must be addressed before any other visual work lands.

---

### Pitfall 2: Rounding Radius Removal Breaks Purchased-Item Checkmark and Hero Portrait Masks

**What goes wrong:** DESIGN.md mandates `0px` corners everywhere ("Sharp corners are non-negotiable"). The current codebase uses `rounded-md` on ItemCard buttons, `rounded-full` on the purchased-item checkmark overlay, `rounded` on item images, and `rounded-lg` on the GetBuildButton. Blindly removing all border-radius will make the green checkmark circle into a green square, breaking the visual affordance that an item has been purchased. Hero portraits and item images rely on `rounded` to hide the harsh edges of the rectangular Steam CDN images.

**Why it happens:** The design spec is absolutist about 0px corners but does not address functional UI patterns that use roundedness for semantic meaning (checkmark = circle = completed). A find-and-replace removal of all `rounded-*` classes will break the purchased-item UX, which is one of the most frequently used interactions during a live game.

**Consequences:** Players during live games cannot visually distinguish purchased vs unpurchased items at a glance. The "golden circle with checkmark" is a strong visual signal; a "golden square with checkmark" reads as a badge or label, not as "completed."

**Prevention:**
1. Audit every `rounded-*` usage and categorize: decorative (convert to 0px per spec) vs. functional (keep or replace with alternative signal). The purchased checkmark and GSI status indicator dot are functional.
2. For functional roundedness, propose an alternative signal to the designer: e.g., a colored left-border accent strip (which the DESIGN.md itself suggests for hero/legendary items), opacity reduction, or a strikethrough effect.
3. Keep a `DESIGN_EXCEPTIONS.md` file documenting intentional deviations from the spec with rationale.

**Detection:** Visual regression testing on the item timeline with purchased items. Manually verify during a live game flow.

---

### Pitfall 3: In-Memory Cache Serves Stale Data After Pipeline Refresh

**What goes wrong:** The plan is to load hero/item data into memory at startup and serve from cache instead of hitting SQLite. But the existing `refresh_all_data()` pipeline runs every 6 hours via APScheduler, upserting new hero/item data into the DB. If the in-memory cache is not explicitly invalidated after a pipeline refresh, the API serves stale hero stats, item costs, and matchup data until the next server restart. Worse: the `RulesEngine` already has its own `init_lookups()` cache (hero name/ID maps, item name/ID maps) that refreshes separately -- introducing a second cache layer creates two independent invalidation paths that must stay synchronized.

**Why it happens:** The codebase already has a subtle form of this bug: `refresh.py` line 122 calls `_rules.refresh_lookups(session)` at the end of the pipeline, but uses the same session that just did the bulk upsert. The rules engine refresh is coupled to the refresh pipeline. A new in-memory data cache would be a third independent cache alongside the rules engine lookups and the `ResponseCache` (which has its own TTL). Three caches, three invalidation timelines.

**Consequences:** Hero stats change after a Dota patch, the pipeline fetches new data, but the in-memory cache still serves old stats to the context builder. Claude receives stale hero data, producing recommendations based on outdated armor/damage values. The ResponseCache (5-min TTL) may also cache responses built from stale data. Users see incorrect gold costs in the UI if item prices changed.

**Prevention:**
1. Create a single `DataCache` class that owns ALL in-memory data (heroes, items, neutral items, item name maps). The `RulesEngine` should read from this cache, not maintain its own.
2. Wire `refresh_all_data()` to call `data_cache.reload()` after successful commit, using a fresh session (not the same session that did the upsert -- see Pitfall 4).
3. Clear `ResponseCache` when `DataCache` reloads -- stale recommendation responses are built from stale data.
4. Add a `/admin/cache-status` endpoint that reports cache age and entry count for debugging.

**Detection:** After a data pipeline run, compare `GET /api/heroes` response with DB contents. If they diverge, the cache is stale.

---

### Pitfall 4: Session Sharing Between Pipeline Refresh and Cache Reload

**What goes wrong:** The current `refresh_all_data()` calls `_rules.refresh_lookups(session)` with the same session that performed bulk upserts. This is the known tech debt item "refresh_lookups() session safety fix" from PROJECT.md. If the in-memory cache reload also reuses this session, and the session is in a partially committed or rolled-back state, the cache loads corrupt or incomplete data. With async SQLAlchemy, sharing an `AsyncSession` across tasks is explicitly unsupported -- the documentation states "AsyncSession per task."

**Why it happens:** The `async_session` factory creates sessions with `expire_on_commit=False` (already correctly configured), but the refresh pipeline creates a single session via `async with async_session() as session:` and passes it to multiple callsites. If `_rules.refresh_lookups()` triggers a lazy load or the new cache reload does a `select()`, it reuses the same connection, which may still be mid-transaction.

**Consequences:** Intermittent `InvalidRequestError` or `DetachedInstanceError` from SQLAlchemy. In the worst case, the cache loads a mix of old and new data if the upsert transaction hasn't fully committed when the reload fires.

**Prevention:**
1. Cache reload MUST create its own fresh `AsyncSession`, never accept the pipeline's session.
2. Structure the pipeline as: `upsert -> commit -> (new session) reload cache -> (new session) reload rules`.
3. Use an explicit event/callback pattern: `refresh_all_data()` emits a "refresh_complete" signal, and the cache subscribes to it with its own session lifecycle.

**Detection:** Run the refresh pipeline under load (concurrent recommendation requests). If any request gets a `DetachedInstanceError`, session sharing is the cause.

---

### Pitfall 5: Cross-Store Subscription Cascade Creates Infinite Re-render Loop

**What goes wrong:** `useGsiSync` subscribes to `gsiStore` and writes to both `gameStore` and `recommendationStore`. `useAutoRefresh` independently subscribes to `gsiStore` and writes to `recommendationStore`, `refreshStore`, and `gameStore`. When consolidating these into a single hook or merging their subscription logic, a careless implementation can create a cycle: GSI update -> write gameStore -> gameStore subscriber fires -> reads gsiStore -> triggers another GSI handler -> writes recommendationStore -> repeat. Zustand's `subscribe()` fires synchronously during `set()`, so a write-to-store inside a subscription handler of another store can cascade within the same microtask.

**Why it happens:** Both hooks currently work because they are isolated -- each has its own `useEffect` with its own subscription and cleanup. When consolidating, the temptation is to merge them into a single `gsiStore.subscribe()` callback. But `useAutoRefresh.fireRefresh()` calls `recStore.clearResults()`, `recStore.setLoading(true)`, and eventually `recStore.setData()` -- all of which trigger `recommendationStore` subscribers. If the consolidated hook also subscribes to `recommendationStore` (as `useAutoRefresh` does for the "manual recommend completes" detection), you get cascading synchronous updates.

**Consequences:** React render loop. Browser tab freezes. During a live game, the UI becomes unresponsive exactly when it should be updating.

**Prevention:**
1. Keep the `gsiStore` subscription and the `recommendationStore` subscription as separate `useEffect` blocks, even if they live in the same hook file. Consolidation should be about co-location, not about merging subscriptions into one callback.
2. Use `queueMicrotask()` or `setTimeout(fn, 0)` to batch cross-store writes, breaking the synchronous cascade chain.
3. Never subscribe to Store B from within a subscription callback of Store A if the callback writes to Store B. Read Store B's state via `getState()` instead.
4. Add a guard flag (`isProcessingGsi`) to prevent re-entrant execution of the consolidated handler.

**Detection:** React DevTools Profiler shows rapidly increasing render count. Browser performance monitor shows 100% CPU on the tab.

---

## Moderate Pitfalls

### Pitfall 6: Color Token Rename Causes Invisible Text and Broken Hover States

**What goes wrong:** The current `globals.css` defines `--color-cyan-accent`, `--color-radiant`, `--color-dire`, `--color-bg-primary`, `--color-bg-secondary`, `--color-bg-elevated`. Components reference these as Tailwind classes (`bg-cyan-accent`, `text-cyan-accent`, `bg-bg-primary`, etc.). The DESIGN.md introduces completely different tokens: `surface` (#131313), `surface-container-low` (#1C1B1B), `primary_container` (#B22222), `secondary` (#FFDB3C), `on_surface` (#E5E2E1). If the old tokens are removed before all components are migrated, any component still referencing `bg-cyan-accent` gets Tailwind's default (transparent/no match), rendering text invisible against the dark background.

**Why it happens:** Tailwind v4 treats `@theme` variables as the source of truth for utility generation. Removing `--color-cyan-accent` from `@theme` means `text-cyan-accent` no longer generates a CSS class. There is no compile-time error; the class simply stops working silently.

**Prevention:**
1. Migrate in two stages: Stage 1 adds all new tokens alongside old ones (both coexist in `@theme`). Stage 2 removes old tokens after all components are migrated and grepping confirms zero references.
2. Before Stage 2, run `grep -r "cyan-accent\|bg-primary\|bg-secondary\|bg-elevated" prismlab/frontend/src/` to find stragglers.
3. Add a comment block in `globals.css` marking deprecated tokens: `/* DEPRECATED: remove after all components migrated */`.

**Detection:** Visual inspection on every page. Look specifically for invisible text (white-on-white or transparent-on-dark).

---

### Pitfall 7: Elevation System Change Creates "Floating in Void" Effect

**What goes wrong:** DESIGN.md forbids traditional drop shadows and mandates "Ambient Glows" -- 5% opacity crimson aura with 32px blur. The current UI uses no explicit shadows (dark theme on dark backgrounds), but relies on `bg-bg-elevated` background contrast to create visual hierarchy. The new "tonal stacking" approach requires carefully nesting surface levels: `surface` -> `surface-container-low` -> `surface-container-high`. If the nesting order is wrong (e.g., a `surface-container-high` card inside a `surface-container-high` parent), elements become invisible against their background.

**Why it happens:** The DESIGN.md describes a physical "stack of stone" metaphor with 6+ surface levels. In practice, developers choose the wrong surface level for a given context because the naming (`lowest`, `low`, `container`, `high`, `highest`, `bright`) is relative and easy to confuse. The sidebar, item timeline, phase cards, and floating modals (screenshot parser, settings panel) each need a specific surface level in the hierarchy.

**Prevention:**
1. Create a mapping document: Component -> Surface Level. E.g., Sidebar = `surface-container-lowest`, MainPanel = `surface`, PhaseCard = `surface-container-low`, Modal = `surface-container-highest`.
2. Build a visual test page (`/dev/surfaces`) that shows all surface levels stacked, ensuring each is distinguishable from its neighbors.
3. Start implementation from the outermost layout containers (App -> Sidebar + MainPanel -> Header) inward, so the surface hierarchy is established before child components are styled.

**Detection:** Screenshots compared side-by-side at each migration step. Any element that "disappears" into its background is a surface-level ordering error.

---

### Pitfall 8: Cache Stampede on Startup When Both Hero and Item Caches Load Simultaneously

**What goes wrong:** If the in-memory cache loads heroes and items from the DB at startup, and the DB hasn't been seeded yet (first run), the cache loads empty data. Then `seed_if_empty()` populates the DB, but the cache is never reloaded. The rules engine calls `init_lookups()` separately, creating a window where the cache is empty but the rules engine has data (or vice versa).

**Why it happens:** The current startup sequence in `main.py` is: (1) create tables, (2) seed, (3) init rules lookups, (4) start scheduler. Adding cache loading anywhere in this sequence creates ordering dependencies. If cache loads at step 2.5 (between seed and rules init), it works. If it loads at step 1.5 (before seed), it gets empty data.

**Consequences:** First recommendation request after a cold start hits the cache, gets empty hero/item data, and the context builder sends Claude a prompt with "Hero #X" and "Item #Y" instead of real names. The recommendation quality is severely degraded.

**Prevention:**
1. Cache loading MUST happen after seeding completes. Add it as an explicit step in the lifespan function: `create tables -> seed -> load cache -> init rules from cache (not DB) -> start scheduler`.
2. Add a health check: `/health` should return `"ready": false` until cache is populated. The frontend should show a loading state until health returns ready.
3. Consider making the cache object the single source of truth that both rules engine and context builder read from, eliminating the separate `init_lookups()` path entirely.

**Detection:** Deploy with empty DB, hit `/api/recommend` immediately after startup. If hero names show as "Hero #X", the cache loaded before seeding.

---

### Pitfall 9: The "No-Line Rule" Breaks Accessibility and Keyboard Focus Indicators

**What goes wrong:** DESIGN.md says "Do not use 1px solid borders to define sections" and "If a container needs a perimeter, use the `outline_variant` at 15% opacity. It should be felt, not seen." But keyboard focus indicators (`:focus-visible` rings) ARE borders/outlines that must be clearly visible for accessibility. The current codebase uses `ring-1 ring-cyan-accent` for selected items and `focus:ring-2` patterns. Removing these to comply with the "no-line rule" makes the app inaccessible to keyboard users.

**Why it happens:** Design specs often focus on visual aesthetics without considering accessibility states. The "felt, not seen" guidance directly conflicts with WCAG 2.1 Success Criterion 2.4.7 (Focus Visible), which requires a visible focus indicator.

**Consequences:** Keyboard navigation becomes impossible. Screen reader users lose all visual feedback. This is both a usability and compliance issue.

**Prevention:**
1. Explicitly exempt `:focus-visible` states from the no-line rule. Focus indicators should use `outline_variant` (#5A403E) at full opacity (not 15%) or the `secondary_fixed` gold (#FFE16D) to ensure visibility.
2. Document this exemption in the component guidelines: "All interactive elements MUST have a visible `:focus-visible` indicator."
3. Test with keyboard-only navigation (Tab through the entire flow: hero picker -> role -> playstyle -> side -> lane -> opponents -> Get Build -> item cards).

**Detection:** Tab through the app. If you cannot tell which element is focused, the focus indicators are broken.

---

### Pitfall 10: Context Builder DB Queries Bypass Cache, Negating Performance Gains

**What goes wrong:** The context builder (`context_builder.py`) makes 6+ DB queries per recommendation request: hero lookup, opponent hero lookups, matchup data, item catalog, item popularity, neutral items, and item name resolution (multiple `select(Item)` calls). Adding an in-memory cache for the `/api/heroes` and `/api/items` endpoints but forgetting to wire the context builder to use the same cache means the hot path (recommendation engine) still hits SQLite on every request.

**Why it happens:** The context builder takes `db: AsyncSession` as a parameter and calls `self._get_hero()`, `get_relevant_items()`, `get_neutral_items_by_tier()`, `get_hero_item_popularity()`, and `_extract_top_items()` -- all of which do direct `select()` queries. The hero/item API routes are separate code paths. Adding cache to the routes does not affect the context builder.

**Consequences:** The stated goal ("eliminate DB queries on hot path") is only partially achieved. The recommendation endpoint, which is the most latency-sensitive path, still hammers SQLite. The hero/item list endpoints (which are already fast and only called once on page load) get the cache, while the path that matters most does not.

**Prevention:**
1. Design the cache API as a service layer, not a route-level decorator. The `DataCache` should expose `get_hero(id)`, `get_all_items()`, `get_neutral_items_by_tier()` methods that the context builder calls instead of querying the DB.
2. Refactor `ContextBuilder.__init__()` to accept a `DataCache` instance alongside the `OpenDotaClient`.
3. `get_relevant_items()` and `get_neutral_items_by_tier()` in `matchup_service.py` should read from cache, not from `db`.
4. Matchup data and item popularity are per-hero and already have their own stale-while-revalidate pattern -- these can stay DB-backed since they are fetched on-demand.

**Detection:** Add logging to `DataCache.get_hero()` and `db.execute(select(Hero))`. If both fire during the same `/api/recommend` request, the context builder is bypassing the cache.

---

### Pitfall 11: TriggerEvent Dedup Bug Amplified by Subscription Consolidation

**What goes wrong:** PROJECT.md lists "TriggerEvent dedup" as existing tech debt. The current `useAutoRefresh` detects events (death, gold swing, tower kill, roshan kill, phase transition) from GSI data diffs. If the same GSI update triggers multiple events (e.g., player dies AND a tower falls in the same tick), only the first event from `detectTriggers()` is processed. During subscription consolidation, if the trigger detection logic is restructured, the dedup behavior may accidentally allow duplicate events through, firing two rapid `fireRefresh()` calls that both bypass cooldown (since cooldown is set inside `fireRefresh`, the second call may read `cooldownEndRef.current` before the first call updates it).

**Why it happens:** `detectTriggers()` returns a single `TriggerEvent | null`, so the current code is implicitly deduplicated. If refactored to return an array of events (to fix the dedup bug properly), the `fireRefresh()` call must be guarded against concurrent execution.

**Consequences:** Two recommendation requests fire within milliseconds of each other. The Claude API gets hit twice, doubling cost. The second response overwrites the first, possibly with different recommendations, causing the item timeline to "flash" between two states.

**Prevention:**
1. If `detectTriggers` is refactored to return multiple events, pick the highest-priority event (death > roshan > tower > gold_swing > phase_transition) and fire only once.
2. Add an `isRefreshing` guard that prevents `fireRefresh()` from being called while a previous refresh is in-flight. Check `recStore.isLoading` at the top of `fireRefresh()` (this guard already exists but must be preserved during consolidation).
3. Set cooldown BEFORE the async API call, not after -- this is already correct in the current code but easy to reorder during refactoring.

**Detection:** In the browser console, log every `fireRefresh()` call with a timestamp. If two calls appear within 100ms, dedup is broken.

---

## Minor Pitfalls

### Pitfall 12: Google Fonts CDN Blocked by Strict CSP or Adblockers

**What goes wrong:** Newsreader and Manrope are Google Fonts. Some corporate networks, privacy-focused browsers, and adblockers block `fonts.googleapis.com` and `fonts.gstatic.com`. If fonts fail to load, the UI falls back to system fonts, but the DESIGN.md's careful typography hierarchy (Newsreader display vs. Manrope body) collapses into a single system font, losing the editorial aesthetic entirely.

**Prevention:** Self-host the font files. Download Newsreader and Manrope WOFF2 files and serve them from the Vite static assets directory. This also eliminates the FOUT flash from an external network request.

---

### Pitfall 13: The "Blood-Glass" Backdrop-Filter Effect Causes Performance Issues on Low-End Hardware

**What goes wrong:** DESIGN.md specifies `backdrop-blur` of 12px with 20-40% opacity `primary_container` (#B22222) for tactical overlays. `backdrop-filter: blur(12px)` is GPU-intensive. If applied to elements that update frequently (like the LiveStatsBar or the AutoRefreshToast which appears during cooldown), it causes frame drops during the 1Hz GSI update cycle.

**Prevention:** Only apply backdrop-blur to static or rarely-updated elements (modals, settings panel). For frequently-updated elements like toasts and live stats, use solid backgrounds with opacity instead.

---

### Pitfall 14: `on_surface` Color (#E5E2E1) Insufficient Contrast Against `surface-container-highest` (#353534)

**What goes wrong:** DESIGN.md specifies `on_surface` (#E5E2E1) as the primary text color and says "Don't use 100% white." But #E5E2E1 on #353534 has a contrast ratio of approximately 4.1:1, which barely meets WCAG AA for normal text (4.5:1 required) and fails for small text. In the dense item timeline with `body-sm` captions, this is below the accessibility threshold.

**Prevention:** Use `on_surface` (#E5E2E1) only on darker surfaces (`surface` #131313, `surface-container-lowest` #0E0E0E). On lighter surfaces like `surface-container-highest` (#353534), use pure white or near-white. Define a `on_surface_high_contrast` token for this purpose.

**Detection:** Run an automated contrast checker (e.g., axe-core) against the rendered UI.

---

### Pitfall 15: Playstyle Auto-Suggest Creates Hidden Store Write During GSI Subscription

**What goes wrong:** The v3.0 milestone includes "auto-suggest playstyle when GSI detects hero+role." This means the consolidated GSI subscription hook will write to `gameStore.setPlaystyle()` in addition to `selectHero()` and `setRole()`. But `setRole()` already has logic that clears playstyle if the current one is invalid for the new role (see `gameStore.ts` lines 98-103). If `setRole()` clears playstyle and then `setPlaystyle()` sets a new one in the same synchronous block, the intermediate state (playstyle=null) may briefly trigger a re-render that hides the playstyle selector, then shows it again with the auto-suggested value -- causing a visual flicker.

**Prevention:** Batch the hero+role+playstyle writes into a single `set()` call: `set({ selectedHero: hero, role: inferredRole, playstyle: suggestedPlaystyle })`. This avoids intermediate states and re-renders.

---

### Pitfall 16: ResponseCache Not Cleared When Design Changes Affect Recommendation Display

**What goes wrong:** The `ResponseCache` caches full `RecommendResponse` objects for 5 minutes. This is fine for data, but if the frontend starts expecting new response fields (e.g., for new display formatting), cached responses from before the backend update will lack those fields. During a rolling deploy where the frontend updates before the backend, the cached responses will cause rendering errors.

**Prevention:** During any deployment that changes the `RecommendResponse` schema, clear the cache or restart the backend container. Add a schema version field to the cache key so old-format responses are never served.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Design token migration | Invisible text from removed color tokens (P6) | Two-stage migration: add new tokens first, remove old after full grep confirms zero references |
| Font loading | Layout shift from Newsreader/Manrope swap (P1) | Self-host fonts with preload, use size-adjust for fallback matching |
| 0px corners enforcement | Broken purchased-item checkmark UX (P2) | Audit functional vs decorative roundedness, propose alternative signals |
| Elevation system | Wrong surface-level nesting (P7) | Create component-to-surface mapping document, build visual test page |
| In-memory cache creation | Stale data after pipeline refresh (P3) | Single DataCache class with explicit reload, wire to pipeline completion |
| Cache startup ordering | Empty cache on first run (P8) | Load cache after seed, add health check readiness gate |
| Cache scope | Context builder bypasses cache (P10) | Design cache as service layer, inject into context builder |
| Session safety | Shared session between pipeline and cache (P4) | New session per task, never pass pipeline session to cache reload |
| Store subscription merge | Infinite re-render loop from cross-store writes (P5) | Keep subscriptions separate even if co-located, guard against re-entry |
| TriggerEvent dedup fix | Double-fire during consolidation (P11) | Priority-pick single event, preserve isLoading guard |
| Playstyle auto-suggest | Flicker from intermediate state (P15) | Batch hero+role+playstyle into single set() call |
| Accessibility | Focus indicators removed by no-line rule (P9) | Exempt :focus-visible from design constraints |
| Backdrop blur | Frame drops on 1Hz GSI updates (P13) | Only apply blur to static elements |
| Contrast | Small text fails WCAG AA on light surfaces (P14) | Define high-contrast text token for elevated surfaces |

---

## Integration Pitfalls (Cross-Cutting Concerns)

### The Three-Cache Coherence Problem

The v3.0 codebase will have three independent cache layers:
1. **DataCache** (new) -- in-memory hero/item data
2. **RulesEngine lookups** (existing) -- hero name/ID and item name/ID maps
3. **ResponseCache** (existing) -- full recommendation responses, 5-min TTL

All three must invalidate in the correct order after a data pipeline refresh:
1. DataCache reloads from DB (fresh session)
2. RulesEngine rebuilds its maps FROM DataCache (not from DB directly)
3. ResponseCache is fully cleared (old responses contain old data)

If any step is skipped or out of order, the system serves inconsistent data. The current code already has a mild form of this: `ResponseCache` is never cleared after a pipeline refresh, so cached responses can contain hero data up to 5 minutes older than the DB.

### Design Migration + Store Consolidation Ordering

The design system migration touches every `.tsx` component file. The store subscription consolidation touches hooks that are imported by top-level components (`App.tsx`). If both are done in the same phase, merge conflicts between branches become severe and review is nearly impossible.

**Recommendation:** Complete store consolidation and tech debt cleanup FIRST (smaller, behavior-preserving changes that are easy to test), THEN do the design system migration (large, visual-only changes that are easy to review). This ordering also means the store behavior is stable and well-tested before the visual layer changes, reducing the number of variables when debugging visual regressions.

---

## Sources

- [Tailwind CSS v4 Migration Best Practices](https://www.digitalapplied.com/blog/tailwind-css-v4-2026-migration-best-practices)
- [Debugging Tailwind CSS 4 Common Mistakes](https://medium.com/@sureshdotariya/debugging-tailwind-css-4-in-2025-common-mistakes-and-how-to-fix-them-b022e6cb0a63)
- [Tailwind CSS v4 @theme Documentation](https://tailwindcss.com/docs/theme)
- [How to Implement Cache Invalidation in FastAPI](https://oneuptime.com/blog/post/2026-02-02-fastapi-cache-invalidation/view)
- [FastAPI Mistakes That Kill Performance](https://dev.to/igorbenav/fastapi-mistakes-that-kill-your-performance-2b8k)
- [How to Avoid Caching in SQLAlchemy: Fix Stale Data Issues](https://www.pythontutorials.net/blog/how-to-avoid-caching-in-sqlalchemy/)
- [SQLAlchemy expire_on_commit Discussion](https://github.com/sqlalchemy/sqlalchemy/discussions/11495)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Zustand Store Update and Race Conditions](https://github.com/pmndrs/zustand/discussions/2034)
- [subscribeWithSelector Fires on Every Update](https://github.com/pmndrs/zustand/discussions/2103)
- [Visual Breaking Change in Design Systems](https://medium.com/eightshapes-llc/visual-breaking-change-in-design-systems-1e9109fac9c4)
- [Font Loading: FOIT and FOUT](https://dev.to/ibn_abubakre/font-loading-strategies-foit-and-fout-393b)
- [Cache in Asynchronous Python Applications](https://medium.com/the-pandadoc-tech-blog/cache-in-asynchronous-python-applications-aa83157af712)
