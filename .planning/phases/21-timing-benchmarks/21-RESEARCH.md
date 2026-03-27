# Phase 21: Timing Benchmarks - Research

**Researched:** 2026-03-27
**Domain:** Full-stack timing benchmark display (backend context builder + schema extensions, frontend TimingBar components, GSI live comparison)
**Confidence:** HIGH

## Summary

Phase 21 surfaces the item timing benchmark data established in Phase 19 through three layers: (1) a new `_build_timing_section()` method in the backend context builder that feeds timing data to Claude for reasoning, (2) new frontend components (TimingBar, TimingTooltip, LiveTimingMarker, WindowPassedOverlay, UrgencyBorder CSS) inside the existing ItemCard, and (3) GSI-connected live comparison showing "you are here" markers and "X gold away" text on the timing bars.

The implementation requires zero new packages on either frontend or backend. All timing data already exists in DataCache via `get_hero_timings(hero_id)` returning `dict[str, list[TimingBucket]]` keyed by item internal name. The TimingBucket dataclass already has `time`, `games`, `wins`, `confidence`, and a `win_rate` property. The key algorithmic work is (1) classifying time buckets into good/on-track/late zones with win-rate-based urgency detection, (2) extending the API response schema to carry per-item timing metadata to the frontend, and (3) building the TimingBar component with reactive GSI state. No new API endpoints are needed -- timing data rides on the existing `/api/recommend` response.

**Primary recommendation:** Implement backend first (zone classification logic, context builder section, schema extension, recommender enrichment), then frontend types and components, then GSI integration last. Each layer is independently testable.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Compact horizontal bar below each item in ItemCard, with good/on-track/late zones colored green->yellow->red. Win rate shown on hover tooltip. Fits existing ItemCard layout without restructuring.
- **D-02:** Items with steep win-rate falloff (timing-critical) get a pulsing accent border using the crimson color from DESIGN.md. Non-urgent items stay neutral. Visually separates TIME-02 urgency from normal items.
- **D-03:** Confidence level (strong/moderate/weak from Phase 19 D-07) appears in tooltip only on hover over the timing bar, not inline. Keeps UI clean.
- **D-04:** All items with timing data are shown, per Phase 19 D-07 (no data hidden). Weak confidence items show with muted/reduced-opacity styling on the timing bar.
- **D-05:** New `_build_timing_section()` method in context_builder, appended after item catalog in the user message. Format per item: "BKB: good <20min (58% WR), on-track 20-25min (52%), late >25min (41%)". Approximately 200 tokens for 5-8 items.
- **D-06:** Timing data sent only for the hero's popular items (items that appear in the hero's timing benchmark data from DataCache). Filtered to items with sufficient sample size. Avoids noise from irrelevant items.
- **D-07:** Claude references timing naturally in reasoning with specific numbers. System prompt directive (already in place at lines 49-57) guides this. No forced format -- Claude cites percentages like "BKB before 25 minutes has a 58% win rate vs. 41% after 30."
- **D-08:** A marker on the timing bar shows "you are here" based on current game clock from GSI. Gold comparison shown as "X gold away" text below the bar. Updates via existing GSI WebSocket pipeline.
- **D-09:** When game clock passes the "late" threshold for an item, the timing bar greys out with a "window passed" label. Item stays recommended but urgency signal shifts. Does NOT remove the item.
- **D-10:** Timing comparison shows on ALL unpurchased items, not just the next one. Already-purchased items (click-to-mark) don't show timing. Consistent with existing interaction pattern.

### Claude's Discretion
- How to derive good/on-track/late ranges from TimingBucket data (percentile thresholds, win-rate inflection points)
- How to detect "steep win-rate falloff" for urgency classification (threshold for what counts as steep)
- TimingBar component structure and animation approach for the pulsing urgency border
- How the "you are here" marker updates reactively with GSI game clock
- API response schema extension for timing data (new field on ItemRecommendation or separate timing object)

### Deferred Ideas (OUT OF SCOPE)
- Per-match timing comparison (requires Steam login + match history -- Out of Scope per REQUIREMENTS.md)
- Prescriptive exact-minute targets (Out of Scope -- false precision)
- Timing-aware re-evaluation weighting (ADVINT-02 in Future Requirements)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TIME-01 | User can see timing benchmarks (good/average/late window with win rate gradients) on each recommended item | Backend: Zone classification algorithm derives good/on-track/late from TimingBucket data. API schema extension carries timing data in RecommendResponse. Frontend: TimingBar component renders three-zone horizontal bar with proportional widths. |
| TIME-02 | User can see urgency indicators distinguishing timing-sensitive items (steep win rate falloff) from flexible items | Backend: Urgency detection compares good-zone vs late-zone win rates. Frontend: UrgencyBorder CSS animation pulses crimson glow on timing-critical ItemCards. Reduced-motion fallback is static border. |
| TIME-03 | Claude's reasoning references specific timing benchmarks when explaining item urgency | Backend: `_build_timing_section()` in context_builder formats timing data for Claude. System prompt "Timing Benchmarks" directive (already at lines 49-57) guides Claude to reference specific numbers. No system prompt changes needed. |
| TIME-04 | User can see live comparison of current gold/clock against timing benchmarks during GSI-connected games | Frontend: LiveTimingMarker positioned on TimingBar via GSI game_clock. "X gold away" text computed from GSI gold minus item cost. WindowPassedOverlay greys out bar when clock exceeds late threshold. All data from existing gsiStore. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Frontend:** React 19 + Vite + TypeScript + Tailwind v4 + Zustand (state)
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **AI Engine:** Claude API (Haiku) for item reasoning
- **Dark theme** with spectral cyan, Radiant teal, Dire red -- now overridden by DESIGN.md "Tactical Relic Editorial" (obsidian, crimson, gold)
- **0px corners** -- non-negotiable per DESIGN.md
- **No 1px borders** -- tonal layering only
- **Structured JSON output** from Claude API
- **Hybrid engine:** Rules first, Claude for reasoning. Always fallback.
- All code under `prismlab/` subdirectory

## Standard Stack

### Core (No New Packages)

| Library | Version | Purpose | Already In Use |
|---------|---------|---------|----------------|
| React | 19.2.4 | Component framework for TimingBar/TimingTooltip | Yes |
| Zustand | 5.0.12 | State management (gsiStore for live data) | Yes |
| Tailwind CSS | 4.2.2 | Styling with @theme tokens | Yes |
| Vitest | 4.1.0 | Frontend test framework | Yes |
| FastAPI | existing | API response schema changes | Yes |
| Pydantic | existing | Schema validation for timing response fields | Yes |

### Supporting (No New Packages)

| Library | Purpose | Already In Use |
|---------|---------|----------------|
| @testing-library/react | 16.3.2 | Component testing | Yes |
| pytest | existing | Backend context_builder and schema tests | Yes |

**Installation:** No new packages. Zero changes to `package.json` or `requirements.txt`.

**Confidence:** HIGH -- all libraries already validated in production across v1-v4 phases.

## Architecture Patterns

### Files Modified

```
prismlab/backend/
  engine/
    context_builder.py      # +_build_timing_section() method, +build() integration
    schemas.py              # +ItemTimingResponse model, +timing_data field on RecommendResponse
    recommender.py          # +timing data enrichment step in recommend() pipeline

prismlab/frontend/
  src/
    components/timeline/
      TimingBar.tsx          # NEW: Timing bar with zones, marker, tooltip
      ItemCard.tsx           # MODIFIED: Accept timing props, render TimingBar, urgency class
      PhaseCard.tsx          # MODIFIED: Pass timing data + GSI state to ItemCards
      ItemTimeline.tsx       # MODIFIED: Subscribe to GSI, pass data down
    types/
      recommendation.ts     # +TimingBucketUI, +ItemTimingData interfaces, +timing_data on response
    styles/
      globals.css            # +pulse-urgency keyframes animation
```

### Pattern 1: Zone Classification Algorithm (Backend)

**What:** Derives good/on-track/late zones from raw TimingBucket data using win-rate inflection points.

**When to use:** When processing timing data for API response and context builder.

**Approach:**

The TimingBucket data from OpenDota comes as time-bucketed entries (typically 10min, 15min, 20min, 25min, 30min, 35min, 40min intervals). Each bucket has games, wins, and a derived win_rate. The zone classification needs to:

1. Sort buckets by time ascending (they already are from OpenDota)
2. Find the inflection point where win rate starts declining meaningfully
3. Classify into three zones:
   - **Good:** Buckets where win rate is within 2% of peak win rate
   - **On-track:** Buckets where win rate is below peak but still above the overall average
   - **Late:** Buckets where win rate is below the overall average

```python
# Recommended approach: percentile-based zone classification
def classify_timing_zones(
    buckets: list[TimingBucket],
) -> dict[str, Any]:
    """Classify timing buckets into good/on-track/late zones.

    Returns zone ranges, aggregate win rates, and urgency flag.
    """
    if not buckets or len(buckets) < 2:
        return None

    # Weight by games for meaningful averages
    total_games = sum(b.games for b in buckets)
    if total_games == 0:
        return None

    weighted_avg_wr = sum(b.win_rate * b.games for b in buckets) / total_games
    peak_wr = max(b.win_rate for b in buckets)

    good_buckets = []
    ontrack_buckets = []
    late_buckets = []

    for b in buckets:
        if b.win_rate >= peak_wr - 0.02:  # Within 2% of peak
            good_buckets.append(b)
        elif b.win_rate >= weighted_avg_wr:
            ontrack_buckets.append(b)
        else:
            late_buckets.append(b)

    # Urgency: steep falloff = good zone WR - late zone WR > 10 percentage points
    good_avg_wr = (
        sum(b.win_rate * b.games for b in good_buckets) /
        sum(b.games for b in good_buckets)
    ) if good_buckets else 0.0
    late_avg_wr = (
        sum(b.win_rate * b.games for b in late_buckets) /
        sum(b.games for b in late_buckets)
    ) if late_buckets else 0.0
    is_urgent = (good_avg_wr - late_avg_wr) > 0.10  # 10pp threshold

    return {
        "good_range": _format_range(good_buckets),
        "ontrack_range": _format_range(ontrack_buckets),
        "late_range": _format_range(late_buckets),
        "good_win_rate": round(good_avg_wr, 3),
        "late_win_rate": round(late_avg_wr, 3),
        "is_urgent": is_urgent,
        "confidence": _aggregate_confidence(buckets),
        "total_games": total_games,
        "buckets_classified": [
            {
                "time": b.time,
                "games": b.games,
                "win_rate": round(b.win_rate, 3),
                "confidence": b.confidence,
                "zone": (
                    "good" if b in good_buckets else
                    "ontrack" if b in ontrack_buckets else
                    "late"
                ),
            }
            for b in buckets
        ],
    }
```

**Confidence:** HIGH -- the algorithm is straightforward. The 2% peak threshold and 10pp urgency threshold are reasonable defaults (Claude's discretion per CONTEXT.md). These can be tuned later if needed.

### Pattern 2: Schema Extension (Backend)

**What:** New Pydantic model for timing data alongside RecommendResponse.

**Approach:** Add timing data as a separate dict on RecommendResponse rather than modifying ItemRecommendation. This keeps the LLM output schema unchanged (Claude does not generate timing data -- it is appended post-LLM by the recommender).

```python
# In schemas.py
class ItemTimingResponse(BaseModel):
    """Per-item timing benchmark data for frontend display."""
    item_name: str                    # internal_name (matches ItemRecommendation.item_name)
    buckets: list[dict]               # [{time, games, win_rate, confidence, zone}, ...]
    is_urgent: bool                   # Steep win-rate falloff detected
    good_range: str                   # "< 20 min" (pre-formatted)
    ontrack_range: str                # "20-25 min"
    late_range: str                   # "> 25 min"
    good_win_rate: float              # 0-1 float
    late_win_rate: float              # 0-1 float
    confidence: str                   # "strong" | "moderate" | "weak" (aggregate)
    total_games: int                  # Sample size for tooltip

# Extend RecommendResponse
class RecommendResponse(BaseModel):
    # ... existing fields ...
    timing_data: list[ItemTimingResponse] = Field(default_factory=list)
```

**Why separate from ItemRecommendation:** The LLM does not produce timing data. Adding it to ItemRecommendation would require modifying the LLM output schema (breaking prompt caching) or post-processing the LLM output. A separate list on the response, keyed by item_name, is cleaner and does not touch the LLM pipeline at all.

**Confidence:** HIGH -- follows existing pattern where neutral_items is a separate field on RecommendResponse.

### Pattern 3: Context Builder Timing Section (Backend)

**What:** New `_build_timing_section()` method assembling timing data for Claude's user message.

**When to use:** In `build()` method, after the item catalog section, before the final instruction.

```python
def _build_timing_section(self, hero_id: int) -> str:
    """Build timing benchmark section for Claude context.

    Format: "BKB: good <20min (58% WR), on-track 20-25min (52%), late >25min (41%)"
    ~200 tokens for 5-8 items. Only includes items with timing data.
    """
    timings = self.cache.get_hero_timings(hero_id)
    if not timings:
        return ""

    lines = []
    for item_name, buckets in timings.items():
        classified = classify_timing_zones(buckets)
        if classified is None:
            continue

        display_name = item_name.replace("_", " ").title()
        good_wr = round(classified["good_win_rate"] * 100)
        late_wr = round(classified["late_win_rate"] * 100)

        line = (
            f"{display_name}: good {classified['good_range']} ({good_wr}% WR), "
            f"on-track {classified['ontrack_range']}, "
            f"late {classified['late_range']} ({late_wr}% WR)"
        )
        if classified["is_urgent"]:
            line += " [TIMING-CRITICAL]"
        lines.append(line)

    if not lines:
        return ""
    return "\n".join(lines)
```

**Confidence:** HIGH -- follows identical pattern to `_build_neutral_catalog()` and other `_build_*` methods.

### Pattern 4: TimingBar Component (Frontend)

**What:** React component rendering the segmented timing bar.

**Structure:** Single `TimingBar.tsx` file containing the bar, tooltip, marker, and window-passed overlay as sub-elements (not separate component files -- they share too much state to warrant splitting).

```typescript
// TimingBar.tsx
interface TimingBarProps {
  buckets: TimingBucketUI[];
  confidence: "strong" | "moderate" | "weak";
  isUrgent: boolean;
  isPurchased: boolean;
  currentGameClock: number | null;
  currentGold: number | null;
  itemCost: number | null;
}

// Opacity based on confidence level
const CONFIDENCE_OPACITY = {
  strong: "opacity-100",
  moderate: "opacity-70",
  weak: "opacity-40",
} as const;
```

**Confidence:** HIGH -- follows existing component patterns in the codebase.

### Pattern 5: GSI Integration (Frontend)

**What:** Live timing comparison using existing gsiStore data.

**Approach:** PhaseCard (or ItemTimeline) subscribes to gsiStore selectors for `game_clock` and `gold`, then passes these values as props through to TimingBar. No new store needed -- this matches the pattern in GameClock.tsx and NeutralItemSection.

```typescript
// In PhaseCard.tsx or ItemTimeline.tsx
const gsiStatus = useGsiStore((s) => s.gsiStatus);
const gameClock = useGsiStore((s) => s.liveState?.game_clock ?? null);
const gold = useGsiStore((s) => s.liveState?.gold ?? null);
const isGsiConnected = gsiStatus === "connected";

// Pass to each ItemCard
<ItemCard
  ...existingProps
  timingData={getTimingForItem(item.item_name)}
  currentGameClock={isGsiConnected ? gameClock : null}
  currentGold={isGsiConnected ? gold : null}
/>
```

**Confidence:** HIGH -- follows existing GSI patterns in ItemTimeline (currentTier) and GameClock.

### Anti-Patterns to Avoid

- **Modifying LLM output schema for timing data:** Timing data is population-level statistics from OpenDota, NOT generated by Claude. Adding it to LLMRecommendation would break prompt caching and create a circular dependency. Keep it as a separate enrichment step in the recommender.
- **Creating a new Zustand store for timing data:** The timing data flows through the recommendation response, not a separate data stream. Adding a store would create sync issues between recommendations and their timing data.
- **Fetching timing data in a separate API call:** One more round-trip slows down the UX. The data is already in DataCache; enrichment is a synchronous dict lookup in the recommender.
- **Inline styles for zone colors:** Must use Tailwind classes referencing @theme tokens declared in globals.css. The timing-specific colors (radiant green, secondary-fixed-dim gold, primary-container crimson) are already defined in the theme.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tooltip positioning | Custom absolute positioning math | CSS `position: absolute` with parent `position: relative` + fixed width centered | Tooltip is always above bar, no edge-case repositioning needed for desktop-first layout |
| Animation system | JS-based animation loop | CSS `@keyframes` + `animation` property | CSS animations are GPU-accelerated, respect prefers-reduced-motion, zero JS overhead |
| GSI data access | Custom WebSocket listener | Existing `useGsiStore` selectors | Already handles connection state, reconnection, and type safety |
| Win rate computation | Frontend calculation from raw buckets | Backend pre-computation in zone classification | Frontend receives pre-classified zones with aggregate win rates -- no raw computation needed |

**Key insight:** The backend should do all the heavy lifting (zone classification, urgency detection, range formatting) and send pre-computed display-ready data. The frontend is a pure presentation layer that maps data to visual elements. This keeps the frontend thin and testable with mock data.

## Common Pitfalls

### Pitfall 1: TimingBucket time field is in seconds, not minutes

**What goes wrong:** Display shows "good < 1200" instead of "good < 20 min".

**Why it happens:** OpenDota `/scenarios/itemTimings` returns `time` as seconds (600, 900, 1200, 1500...). The TimingBucket dataclass stores this as-is.

**How to avoid:** The zone classification function must convert seconds to minutes for all display strings. Frontend receives pre-formatted strings ("< 20 min") from backend.

**Warning signs:** Timing ranges showing unreasonably large numbers.

### Pitfall 2: Items with insufficient data producing meaningless zones

**What goes wrong:** An item with 2 buckets and 15 total games gets classified into 3 zones, each with tiny sample sizes.

**Why it happens:** Rare item purchases on unpopular heroes produce very few timing buckets.

**How to avoid:** The zone classification function should return `None` when total games are below a threshold (e.g., < 50 total games across all buckets or fewer than 2 non-empty buckets). The frontend gracefully handles null timing data by not rendering the TimingBar.

**Warning signs:** TimingBars appearing on every item including niche situational picks with very low pick rates.

### Pitfall 3: Timing data keyed by internal_name mismatch

**What goes wrong:** Backend has timing data for "bkb" but the recommend response uses "black_king_bar" as item_name, causing a lookup miss.

**Why it happens:** OpenDota timing endpoint uses its own item name keys (e.g., "bfury", "ethereal_blade") which may differ from the internal_name in the items table (e.g., "battlefury", "ethereal_blade"). The recommender's `_validate_item_ids` step normalizes item_name to the slug from the items table.

**How to avoid:** When building timing data for the response, look up timing data using the OpenDota item name from the raw timing cache, but key the response by the validated item slug (internal_name). Need a mapping between OpenDota timing keys and internal item names. The DataCache already stores timings keyed by OpenDota item name -- may need a reverse lookup.

**Warning signs:** Timing data present in cache but not appearing on frontend items.

### Pitfall 4: GSI game_clock includes pre-horn time (negative values)

**What goes wrong:** "You are here" marker shows at the left edge with negative position during the pre-game phase.

**Why it happens:** GSI `game_clock` can be negative before the horn (strategy phase). The LiveTimingMarker calculates position as `(gameClock / maxTime) * 100%`.

**How to avoid:** Clamp the marker position to 0-100% range. Negative game_clock should position the marker at 0%. Values exceeding the max bucket time should position at 100%.

**Warning signs:** Marker appearing outside the bar bounds or at nonsensical positions.

### Pitfall 5: ResponseCache serving stale timing data after enrichment changes

**What goes wrong:** A cached response from before timing enrichment was deployed returns without timing_data field, frontend receives `undefined`.

**Why it happens:** ResponseCache uses request hash as key. The same request after code deployment hits the cache and returns the old response format.

**How to avoid:** The `timing_data` field has `default_factory=list` (empty list), so Pydantic deserialization of old cached responses will produce an empty list, not undefined. However, even correct code-path responses will be cached without timing data until the cache TTL (5min) expires. This is acceptable -- timing data appears on the next uncached request.

**Warning signs:** Timing bars not appearing immediately after deployment, then appearing 5 minutes later.

### Pitfall 6: Urgency border conflicting with existing border-l-2 on ItemCard

**What goes wrong:** The pulsing box-shadow urgency effect clashes visually with the existing `border-l-2 border-l-secondary-fixed` accent on the ItemCard.

**Why it happens:** ItemCard already uses a left border for priority indication (core = gold, situational = muted). Adding a full-perimeter glow on top creates visual noise.

**How to avoid:** The urgency glow is a `box-shadow` (not a border), so it does not conflict with the existing `border-l-2`. The shadow renders outside the border box. Per UI-SPEC, the urgency effect is a subtle pulsing `box-shadow: 0 0 12px rgba(178, 34, 34, 0.15)` at peak. This coexists cleanly with the left border accent.

**Warning signs:** Double visual indicators that confuse rather than clarify.

## Code Examples

### Backend: Zone Classification Utility

```python
# Source: Derived from CONTEXT.md D-05 format and TimingBucket dataclass
def _format_time_range(buckets: list[TimingBucket]) -> str:
    """Format a list of buckets into a display time range."""
    if not buckets:
        return ""
    min_time = min(b.time for b in buckets) // 60  # seconds to minutes
    max_time = max(b.time for b in buckets) // 60
    if min_time == max_time:
        return f"~{min_time} min"
    return f"{min_time}-{max_time} min"
```

### Backend: Recommender Enrichment Step

```python
# Source: Follows pattern of _validate_item_ids in recommender.py
def _enrich_timing_data(
    self, hero_id: int, phases: list[RecommendPhase]
) -> list[ItemTimingResponse]:
    """Build timing response data for all recommended items.

    Looks up timing benchmarks from DataCache, classifies zones,
    and returns pre-computed display data for the frontend.
    """
    timings = self.cache.get_hero_timings(hero_id)
    if not timings:
        return []

    # Collect all recommended item internal_names
    recommended_items = set()
    for phase in phases:
        for item in phase.items:
            recommended_items.add(item.item_name)  # Already normalized to internal_name by _validate_item_ids

    results = []
    for item_name in recommended_items:
        buckets = timings.get(item_name)
        if not buckets:
            continue
        classified = classify_timing_zones(buckets)
        if classified is None:
            continue
        results.append(ItemTimingResponse(
            item_name=item_name,
            **classified,
        ))
    return results
```

### Frontend: TimingBar Marker Position

```typescript
// Source: 21-UI-SPEC.md LiveTimingMarker specification
function getMarkerPosition(
  currentSeconds: number,
  buckets: TimingBucketUI[],
): number {
  if (buckets.length === 0) return 0;
  const maxTime = Math.max(...buckets.map((b) => b.time));
  if (maxTime <= 0) return 0;
  const ratio = currentSeconds / maxTime;
  return Math.min(Math.max(ratio * 100, 0), 100); // Clamp 0-100%
}
```

### Frontend: Urgency Pulse Animation (CSS)

```css
/* Source: 21-UI-SPEC.md UrgencyBorder specification */
@keyframes pulse-urgency {
  0%, 100% { box-shadow: 0 0 0px rgba(178, 34, 34, 0); }
  50% { box-shadow: 0 0 12px rgba(178, 34, 34, 0.15); }
}

.timing-urgent {
  animation: pulse-urgency 2s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .timing-urgent {
    animation: none;
    border-left: 1px solid var(--color-primary-container);
  }
}
```

### Backend: Context Builder Timing Section Format

```python
# Source: CONTEXT.md D-05 format specification
# Example output for Anti-Mage:
# ## Item Timing Benchmarks
# Battle Fury: good <20 min (58% WR), on-track 20-25 min (52%), late >25 min (41%) [TIMING-CRITICAL]
# Manta Style: good <25 min (55% WR), on-track 25-30 min (51%), late >30 min (48%)
# Black King Bar: good <25 min (57% WR), on-track 25-30 min (53%), late >30 min (44%) [TIMING-CRITICAL]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static item phase labels ("0-10 min") | Win-rate-backed timing benchmarks with urgency signals | Phase 21 (this phase) | Items show data-driven timing windows instead of arbitrary phase labels |
| All items treated with equal urgency | Timing-critical items visually separated with urgency indicators | Phase 21 (this phase) | Players prioritize time-sensitive purchases |
| No in-game timing feedback | GSI-connected live "you are here" marker | Phase 21 (this phase) | Players see real-time progress against timing benchmarks |

## Open Questions

1. **OpenDota item name to internal_name mapping**
   - What we know: DataCache stores timing data keyed by OpenDota's item names (e.g., "bfury"). The recommender normalizes item_name to internal_name from the items table (e.g., "battlefury"). These may not always match.
   - What's unclear: Whether all OpenDota timing item keys match internal_name exactly. Most do, but some may differ.
   - Recommendation: During timing enrichment, try both the item's internal_name and common OpenDota aliases. Build a small mapping dict if mismatches are found. The existing DataCache has `_item_name_to_id` keyed by internal_name -- can iterate to find matches. **LOW risk** -- most item names match, and mismatches only mean that specific item won't show timing data (graceful degradation).

2. **Urgency threshold tuning**
   - What we know: A 10 percentage point difference between good-zone and late-zone win rates is proposed as the urgency threshold.
   - What's unclear: Whether 10pp is the right threshold for Dota 2 timing-sensitive items. BKB and Battlefury typically show 15-20pp drops; flexible items like Aghanim's Scepter show 3-5pp drops.
   - Recommendation: Start with 10pp. This is Claude's discretion per CONTEXT.md. Can be tuned based on testing with real data. A lower threshold (8pp) would flag more items; a higher threshold (15pp) would be more selective.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (BE) | pytest (existing) |
| Framework (FE) | vitest 4.1.0 + @testing-library/react |
| Config file (BE) | No pytest.ini -- pytest auto-discovers `tests/` directory |
| Config file (FE) | `prismlab/frontend/vitest.config.ts` |
| Quick run (BE) | `cd prismlab/backend && python -m pytest tests/test_context_builder.py -x` |
| Quick run (FE) | `cd prismlab/frontend && npx vitest run src/components/timeline/TimingBar.test.tsx` |
| Full suite (BE) | `cd prismlab/backend && python -m pytest tests/ -x` |
| Full suite (FE) | `cd prismlab/frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TIME-01 | Zone classification produces good/on-track/late with win rates | unit (BE) | `python -m pytest tests/test_timing_zones.py -x` | Wave 0 |
| TIME-01 | TimingBar renders three-zone segments | unit (FE) | `npx vitest run src/components/timeline/TimingBar.test.tsx` | Wave 0 |
| TIME-01 | RecommendResponse includes timing_data field | unit (BE) | `python -m pytest tests/test_recommender.py::test_timing_enrichment -x` | Wave 0 |
| TIME-02 | Urgency detection flags items with steep falloff | unit (BE) | `python -m pytest tests/test_timing_zones.py::test_urgency_detection -x` | Wave 0 |
| TIME-02 | UrgencyBorder animation applied to urgent items | unit (FE) | `npx vitest run src/components/timeline/TimingBar.test.tsx` | Wave 0 |
| TIME-03 | _build_timing_section formats timing data for Claude | unit (BE) | `python -m pytest tests/test_context_builder.py::TestBuildTimingSection -x` | Wave 0 |
| TIME-03 | build() includes timing section in user message | unit (BE) | `python -m pytest tests/test_context_builder.py::TestBuildTimingSection::test_build_includes_timing -x` | Wave 0 |
| TIME-04 | LiveTimingMarker positioned correctly from game clock | unit (FE) | `npx vitest run src/components/timeline/TimingBar.test.tsx` | Wave 0 |
| TIME-04 | "X gold away" text displayed when GSI connected | unit (FE) | `npx vitest run src/components/timeline/TimingBar.test.tsx` | Wave 0 |
| TIME-04 | Window passed overlay shown when clock exceeds late threshold | unit (FE) | `npx vitest run src/components/timeline/TimingBar.test.tsx` | Wave 0 |

### Sampling Rate
- **Per task commit:** Backend: `python -m pytest tests/ -x --timeout=10` / Frontend: `npx vitest run`
- **Per wave merge:** Full suite both backend and frontend
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `prismlab/backend/tests/test_timing_zones.py` -- zone classification unit tests (covers TIME-01, TIME-02)
- [ ] `prismlab/frontend/src/components/timeline/TimingBar.test.tsx` -- TimingBar component tests (covers TIME-01, TIME-02, TIME-04)
- [ ] Backend test for `_build_timing_section` in `test_context_builder.py` (covers TIME-03) -- can be added to existing file

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `prismlab/backend/data/cache.py` -- TimingBucket dataclass, DataCache.get_hero_timings(), set_hero_timings()
- Codebase inspection: `prismlab/backend/data/matchup_service.py` -- get_or_fetch_hero_timings(), _parse_timings_json(), _refresh_hero_timings()
- Codebase inspection: `prismlab/backend/engine/context_builder.py` -- existing _build_* pattern, full build() method structure
- Codebase inspection: `prismlab/backend/engine/schemas.py` -- current RecommendResponse, ItemRecommendation, LLM_OUTPUT_SCHEMA
- Codebase inspection: `prismlab/backend/engine/recommender.py` -- HybridRecommender.recommend() pipeline with enrichment step pattern
- Codebase inspection: `prismlab/frontend/src/components/timeline/ItemCard.tsx` -- current component structure and props
- Codebase inspection: `prismlab/frontend/src/components/timeline/PhaseCard.tsx` -- current ItemCard rendering and GSI patterns
- Codebase inspection: `prismlab/frontend/src/stores/gsiStore.ts` -- GsiLiveState with game_clock and gold fields
- Codebase inspection: `prismlab/frontend/src/types/recommendation.ts` -- current TypeScript interfaces
- Codebase inspection: `prismlab/frontend/src/styles/globals.css` -- @theme tokens including radiant, primary-container, secondary-fixed-dim
- Phase 21 UI-SPEC: `.planning/phases/21-timing-benchmarks/21-UI-SPEC.md` -- complete visual specification
- Phase 21 CONTEXT: `.planning/phases/21-timing-benchmarks/21-CONTEXT.md` -- locked decisions D-01 through D-10
- Phase 19 CONTEXT: `.planning/phases/19-data-foundation-prompt-architecture/19-CONTEXT.md` -- TimingBucket design, D-07 confidence levels
- Phase 19 RESEARCH: `.planning/phases/19-data-foundation-prompt-architecture/19-RESEARCH.md` -- OpenDota timing endpoint details

### Secondary (MEDIUM confidence)
- OpenDota `/scenarios/itemTimings` endpoint structure (verified live in Phase 19 research)

### Tertiary (LOW confidence)
- Urgency threshold (10pp) -- reasonable estimate, no Dota-specific validation data available. Flagged for tuning.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new packages, all existing libraries
- Architecture: HIGH -- follows established patterns in context_builder, recommender, and component structure. All integration points verified by reading actual code.
- Pitfalls: HIGH -- all identified from actual codebase inspection (OpenDota data format, name mismatches, GSI edge cases)
- Zone classification algorithm: MEDIUM -- the algorithm is sound but threshold values (2% peak, 10pp urgency) need validation with real data
- UI-SPEC compliance: HIGH -- UI-SPEC is thorough and all design tokens exist in globals.css

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable -- no external dependency changes expected)
