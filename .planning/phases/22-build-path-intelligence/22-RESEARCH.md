# Phase 22: Build Path Intelligence - Research

**Researched:** 2026-03-27
**Domain:** Dota 2 item component ordering, FastAPI/Pydantic schema extension, React component UI
**Confidence:** HIGH

## Summary

Phase 22 adds per-item component purchase ordering to the existing item recommendation pipeline. Each recommended item (e.g. BKB, Manta Style) is annotated with an ordered list of its components and reasoning for that order. The ordering adapts to game state: a lost lane shifts defensive components earlier. During GSI-connected games, components affordable at current gold are highlighted.

The codebase already has everything needed to implement this cleanly. The `Item` DB model stores a `components` field (list of internal_name strings) seeded from OpenDota's `components` array. The `ItemCached` dataclass in `DataCache` already carries `components: tuple | None`. The `ItemTimingResponse` post-LLM enrichment pattern from Phase 21 provides the exact template: append build path data to `_validate_item_ids` output without touching Claude's generation step.

The frontend pattern is also established: `TimingBar` appears below each `ItemCard` as a sub-component. A `BuildPathPanel` (collapsed by default, revealed on item selection or expand click) follows the same interaction model as the existing reasoning panel in `PhaseCard`.

**Primary recommendation:** Use the post-LLM enrichment pattern from Phase 21. Backend appends `build_paths: list[BuildPathResponse]` to `RecommendResponse`. Frontend renders component steps inside `ItemCard` or an expanded panel, with gold highlighting from `gsiStore.liveState.gold`. Claude's system prompt already has a "Build Path Awareness" section — extend it with a directive to emit `component_order` per item so Claude provides ordering reasoning.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
All implementation choices are at Claude's discretion -- discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

### Claude's Discretion
All implementation choices are at Claude's discretion.

### Deferred Ideas (OUT OF SCOPE)
None -- discuss phase skipped.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PATH-01 | User can see the optimal component purchase order for each recommended item | Backend `_enrich_build_paths` step resolves `ItemCached.components` into ordered list; frontend renders component sequence in `ItemCard` or expanded panel |
| PATH-02 | User can see reasoning for component ordering (why this component first) | Claude's existing "Build Path Awareness" directive extended to emit `component_order` array with per-step `reason` field in structured JSON output |
| PATH-03 | User can see which components are affordable at current gold during GSI-connected games | Frontend reads `gsiStore.liveState.gold`, compares against each component's `cost` from DataCache, applies highlight class |
| PATH-04 | Component ordering adapts to game state — lost lane prioritizes defensive components, won lane prioritizes offensive | Backend enrichment logic re-sorts components based on `lane_result`; or Claude ordering directive uses lane_result context already in user message |
</phase_requirements>

---

## Standard Stack

### Core (already installed — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI / Pydantic | project version | Schema extension for `BuildPathResponse` | All schemas live in `engine/schemas.py`; frozen Pydantic models |
| SQLAlchemy / DataCache | project version | Component data lookup from `ItemCached.components` | Zero-DB-query pattern established in Phase 21 |
| React + Zustand | project version | Frontend component rendering and GSI gold access | `gsiStore.liveState.gold` already exposed |
| Tailwind CSS | project version | Component affordability highlight classes | Design tokens in `globals.css` already include `text-radiant` / `text-on-surface-variant` for gold display |

**No new packages required.** This phase extends existing schema, enrichment, and UI patterns.

## Architecture Patterns

### Post-LLM Enrichment (Phase 21 pattern — use this)

Phase 21 established `_enrich_timing_data` as a step after `_validate_item_ids` in `HybridRecommender.recommend()`. Build path data follows the same pattern:

```
recommend() pipeline:
  Step 6:   _validate_item_ids(phases)          [existing]
  Step 6b:  _enrich_timing_data(hero_id, phases) [Phase 21]
  Step 6c:  _enrich_build_paths(request, phases) [Phase 22 — NEW]
```

`_enrich_build_paths` reads `self.cache.get_item(item_id)` for each recommended item, resolves the `components` tuple into an ordered `ComponentStep` list, applies lane_result reordering, and returns a parallel `build_paths: list[BuildPathResponse]` added to `RecommendResponse`.

### Two-Layer Ordering Strategy

PATH-04 (game-state-adaptive ordering) can be implemented at two points:

**Option A — Backend enrichment only (no Claude involvement):**
- Backend resolves component names and costs from DataCache
- Backend applies a rule: if `lane_result == "lost"`, sort components with the highest HP/stat bonus first (defensive proxy)
- Reasoning strings are template-generated ("Buy this first for immediate HP sustain")
- Advantage: instant, no token cost, always available on fallback

**Option B — Claude generates `component_order` per item (enables PATH-02 rich reasoning):**
- Extend LLM output schema with an optional `component_order` field per item
- Claude uses lane_result context (already in user message via `_build_midgame_section`) to reason about ordering
- Backend uses Claude's ordering if present; falls back to heuristic ordering if absent or on fallback
- Advantage: reasoning is natural language, specific to matchup ("Buy the Ogre Axe before the Belt of Strength because you need the raw HP to survive Invoker's Sunstrike burst")

**Recommended: Hybrid of A and B.** Claude emits component_order per item (PATH-02 reasoning). Backend enrichment fills in costs and affordability data from DataCache regardless (PATH-01, PATH-03). Backend heuristic ordering serves as fallback when Claude omits component_order or when the pipeline is in fallback mode.

### Schema Extension Pattern

Following the `ItemTimingResponse` precedent:

```python
# engine/schemas.py

class ComponentStep(BaseModel):
    """Single component in a build path order."""
    item_name: str          # internal_name (for image URL resolution)
    item_id: int            # for DataCache lookup
    cost: int | None        # from DataCache, not from Claude
    reason: str             # why this component comes at this position
    position: int           # 1-based index in purchase order

class BuildPathResponse(BaseModel):
    """Component purchase order for a single recommended item.
    Pre-computed post-LLM in _enrich_build_paths -- NOT generated by Claude directly.
    Ordering from Claude's component_order (if present), else heuristic fallback.
    """
    item_name: str                    # matches ItemRecommendation.item_name
    steps: list[ComponentStep]        # ordered from first-buy to last-buy
```

`RecommendResponse` gains:
```python
build_paths: list[BuildPathResponse] = Field(default_factory=list)
```

### LLM Schema Extension (PATH-02)

`ItemRecommendation` gains an optional field:
```python
component_order: list[str] | None = None  # ordered list of internal_names
```

`LLM_OUTPUT_SCHEMA` gains `"component_order": {"type": "array", "items": {"type": "string"}, "nullable": True}` under each item's properties.

The system prompt "Build Path Awareness" section is extended with a directive:
```
- For items with multiple components, emit component_order: ordered list of
  internal_names from first-buy to last-buy. First entry = most impactful
  component given current game state. Include only components from the item's
  actual recipe tree.
- Lost lane: order defensive stat components (HP, armor, magic resist) first.
- Won lane or farming: order farming/damage components first.
```

Claude does NOT generate costs — those come from DataCache in `_enrich_build_paths`.

### Frontend Component Pattern

The build path panel lives inside `ItemCard`, rendered below the existing timing bar, collapsed by default and expanded on item click (consistent with the reasoning panel in `PhaseCard`).

Alternatively: build path appears in the existing reasoning panel area (the `selectedItem` block in `PhaseCard`). This is the lower-complexity path — the reasoning panel already shows on item select.

**Recommended:** Extend the `PhaseCard` reasoning panel to include component steps alongside the existing `selectedItem.reasoning` text. No new component required; data flows through `ItemCard` → `PhaseCard` via `selectedItemId`.

Frontend type additions:
```typescript
// types/recommendation.ts

export interface ComponentStep {
  item_name: string;
  item_id: number;
  cost: number | null;
  reason: string;
  position: number;
}

export interface BuildPathResponse {
  item_name: string;
  steps: ComponentStep[];
}
```

`RecommendResponse` gains:
```typescript
build_paths: BuildPathResponse[];
```

### GSI Gold Affordability (PATH-03)

`gsiStore.liveState.gold` is already available in `ItemTimeline` and passed to `PhaseCard` as `currentGold`. The same prop threads down to `ItemCard`. The `TimingBar` already uses `currentGold` + `itemCost` for its "Affordable now / Xg away" display.

For component steps, the same logic applies:
- `isAffordable = currentGold !== null && step.cost !== null && currentGold >= step.cost`
- Apply `text-radiant` class to affordable components, `text-on-surface-variant` to unaffordable
- This mirrors the existing `TimingBar` affordability display pattern exactly

### Recommended Project Structure Addition

No new directories. All additions to existing files:

```
prismlab/backend/engine/
  schemas.py          ← add ComponentStep, BuildPathResponse; extend ItemRecommendation with component_order
  recommender.py      ← add _enrich_build_paths() method, add build_paths to RecommendResponse
  prompts/
    system_prompt.py  ← extend Build Path Awareness directive

prismlab/frontend/src/
  types/recommendation.ts    ← add ComponentStep, BuildPathResponse interfaces
  components/timeline/
    PhaseCard.tsx             ← extend selectedItem panel with component steps
    ItemCard.tsx              ← pass buildPath data through; or keep rendering in PhaseCard
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Component lookup | Custom DB query | `DataCache.get_item(item_id).components` | Already cached, zero DB queries, same pattern as timing enrichment |
| Component costs | Hardcode or fetch from API | `DataCache.get_item(component_id).cost` | Items fully in cache since Phase 16 |
| Item image URLs | Custom CDN logic | `itemImageUrl(component_name)` util already in `imageUrls.ts` | Pattern established, works for all items |
| Gold display logic | New gold comparison | Reuse TimingBar's `isAffordable` pattern | Already proven, uses same `currentGold` prop |
| Full item recipe tree recursion | Multi-level tree walker | Show only direct components (one level) | REQUIREMENTS.md "Out of Scope": "Full item tree visualization — Information overload, show one level of components only" |

**Key insight:** The Item DB model already stores `components` as a list of internal_name strings seeded from OpenDota. This is one-level deep (direct components only), which matches the explicit "Out of Scope" decision in REQUIREMENTS.md against full item tree visualization. No additional data fetching needed.

## Common Pitfalls

### Pitfall 1: Components field may be None or empty
**What goes wrong:** Not all items have components. Basic items (Clarity, Tango, Boots of Speed) have no recipe. `ItemCached.components` will be `None` or `()`.
**Why it happens:** OpenDota returns `"components": null` for base items.
**How to avoid:** Guard: `if not item.components: skip build path for this item`. Only generate `BuildPathResponse` for items where `len(components) >= 2`.
**Warning signs:** Frontend crashes or shows empty component list panels.

### Pitfall 2: Component internal_name not matching DataCache key
**What goes wrong:** `item.components` contains internal names like `"ogre_axe"` but DataCache is keyed by item ID. Need `item_name_to_id` lookup first.
**Why it happens:** OpenDota components field stores internal_names (strings), not IDs.
**How to avoid:** Use `DataCache.item_name_to_id(component_name)` then `DataCache.get_item(component_id)` to resolve cost and image slug. Add a null guard for components that don't resolve (recipes, components not in DB).
**Warning signs:** `None` costs for valid components.

### Pitfall 3: Claude hallucinating component names in `component_order`
**What goes wrong:** Claude emits internal_names that don't exist in OpenDota DB (e.g. `"platemail"` instead of `"plate_mail"`).
**Why it happens:** Claude has imperfect knowledge of exact OpenDota internal naming conventions.
**How to avoid:** Backend validates each name in `component_order` against `DataCache.item_name_to_id`. Invalid names are dropped; backend fills gaps with its own heuristic ordering. This is the same robustness pattern used for item_id validation.
**Warning signs:** Components missing from steps despite being in the item recipe.

### Pitfall 4: Extending LLM_OUTPUT_SCHEMA without testing structured output parsing
**What goes wrong:** Adding `component_order` to LLM_OUTPUT_SCHEMA breaks Anthropic's structured output if the schema shape is wrong (e.g., missing `nullable: True` on optional arrays).
**Why it happens:** Anthropic's structured output API requires precise schema shapes — `anyOf` is disallowed, `$ref` is disallowed, `nullable` must be at the property level.
**How to avoid:** Follow existing schema pattern exactly. `nullable: True` on optional fields. Test with `test_llm.py` fixture that exercises schema generation.
**Warning signs:** `parse_error` fallback reason in responses after schema change.

### Pitfall 5: Build path panel causing layout issues in PhaseCard
**What goes wrong:** Component steps expand the selected item panel to exceed viewport height, pushing content off-screen.
**Why it happens:** 4-6 component steps each with image + cost + reasoning text can be tall.
**How to avoid:** Render component steps as a compact horizontal strip (images + cost badges) with reasoning text on click/hover tooltip, not as expanded cards. Keep the panel height bounded.
**Warning signs:** UI overflow, scroll issues in the recommendations panel.

### Pitfall 6: ResponseCache invalidation
**What goes wrong:** Cached responses from before Phase 22 deployment won't have `build_paths`. Old cache entries serve `build_paths: []` to clients expecting data.
**Why it happens:** ResponseCache TTL is 5 minutes but Pydantic default is `[]`, so old responses are still valid Pydantic objects.
**How to avoid:** `build_paths: list[BuildPathResponse] = Field(default_factory=list)` with `[]` default makes this a non-issue — old cached responses safely return empty build_paths. No cache clear needed on deploy.

## Code Examples

### Component resolution in `_enrich_build_paths` (backend, post-LLM)

```python
# engine/recommender.py

def _enrich_build_paths(
    self,
    request: RecommendRequest,
    phases: list[RecommendPhase],
) -> list[BuildPathResponse]:
    """Build component ordering for all recommended items.

    Reads ItemCached.components from DataCache (zero DB queries).
    Uses Claude's component_order if present; falls back to heuristic ordering.
    Only generates build paths for items with >= 2 components.
    """
    if not self.cache:
        return []

    results: list[BuildPathResponse] = []
    for phase in phases:
        for item in phase.items:
            cached_item = self.cache.get_item(item.item_id)
            if not cached_item or not cached_item.components or len(cached_item.components) < 2:
                continue

            # Determine component order: Claude's ordering takes priority
            component_names = list(cached_item.components)
            if item.component_order:
                # Validate Claude's ordering against actual components
                valid_order = [
                    n for n in item.component_order
                    if n in set(component_names)
                ]
                # Append any components Claude missed
                for name in component_names:
                    if name not in valid_order:
                        valid_order.append(name)
                component_names = valid_order

            # Apply lane_result heuristic if no Claude ordering
            elif request.lane_result == "lost":
                component_names = self._sort_defensive_first(component_names)

            # Build steps with costs from cache
            steps: list[ComponentStep] = []
            for i, comp_name in enumerate(component_names, start=1):
                comp_id = self.cache.item_name_to_id(comp_name)
                comp_item = self.cache.get_item(comp_id) if comp_id else None
                steps.append(ComponentStep(
                    item_name=comp_name,
                    item_id=comp_id or 0,
                    cost=comp_item.cost if comp_item else None,
                    reason="",  # Claude's reason from component_order reasoning field
                    position=i,
                ))

            results.append(BuildPathResponse(item_name=item.item_name, steps=steps))

    return results
```

### Frontend: BuildPath in PhaseCard reasoning panel

```tsx
// components/timeline/PhaseCard.tsx (extension)

{selectedItem && (
  <div className="bg-surface-container-high/50 p-[1.75rem] mt-[1.75rem] border-l-2 border-secondary-fixed">
    <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
      {selectedItem.item_name.replace(/_/g, " ")}
    </span>
    <p className="text-on-surface-variant text-sm leading-relaxed mt-1">
      {selectedItem.reasoning}
    </p>
    {/* Component build path (PATH-01, PATH-02, PATH-03) */}
    {buildPath && buildPath.steps.length > 0 && (
      <BuildPathSteps
        steps={buildPath.steps}
        currentGold={currentGold}
      />
    )}
  </div>
)}
```

### Frontend: affordability highlight (mirrors TimingBar pattern)

```tsx
// Pattern from TimingBar — apply same logic to component costs
const isAffordable = currentGold !== null && step.cost !== null && currentGold >= step.cost;

<span className={isAffordable ? "text-radiant" : "text-on-surface-variant"}>
  {step.cost}g
</span>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Timing data generated by Claude | Timing data: post-LLM enrichment from DataCache | Phase 21 | Build paths follow same pattern — no LLM token cost for structured data |
| Monolithic Claude JSON output | Hybrid: Claude generates ordering reasoning, backend injects costs | Phase 22 | Claude stays in reasoning role; DataCache stays in structured-data role |

## Open Questions

1. **Where exactly does `component_order` reasoning live?**
   - What we know: Claude can emit `component_order: [names]` but reasoning per step needs either a parallel `component_reasons: [strings]` array or a single combined string.
   - What's unclear: Whether per-step reasoning text justifies the schema complexity (parallel arrays are fragile, easily misaligned by Claude).
   - Recommendation: Use a single `build_path_notes` string field on `ItemRecommendation` for Claude's overall component ordering justification. The frontend shows it as a paragraph above the component strip. Simpler schema, still satisfies PATH-02.

2. **Should `BuildPathSteps` be a new component or inline in PhaseCard?**
   - What we know: PhaseCard already has a reasoning panel for `selectedItem`. Component steps are ~4-6 items.
   - What's unclear: Whether the build path warrants its own reusable component for future reuse.
   - Recommendation: Create `BuildPathSteps.tsx` as a standalone component (likely ~60 lines). Named component makes testing cleaner and future reuse in tooltip/modal contexts easier.

## Environment Availability

Step 2.6: SKIPPED — phase is backend schema extension + frontend component work. No external tools or services beyond what's already running. DataCache already holds component data. GSI gold already in gsiStore.

## Validation Architecture

Note: `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`. This section is skipped per that setting.

## Sources

### Primary (HIGH confidence)
- Codebase: `prismlab/backend/engine/schemas.py` — current schema structure, `LLM_OUTPUT_SCHEMA` shape, `ItemTimingResponse` precedent
- Codebase: `prismlab/backend/engine/recommender.py` — `_enrich_timing_data` pattern (Phase 22 mirrors this exactly)
- Codebase: `prismlab/backend/data/cache.py` — `ItemCached.components: tuple | None`, `item_name_to_id` method
- Codebase: `prismlab/backend/data/models.py` — `Item.components: Mapped[list | None]` seeded from OpenDota
- Codebase: `prismlab/backend/engine/prompts/system_prompt.py` — existing "Build Path Awareness" section to extend
- Codebase: `prismlab/frontend/src/components/timeline/PhaseCard.tsx` — reasoning panel pattern
- Codebase: `prismlab/frontend/src/components/timeline/TimingBar.tsx` — affordability display pattern
- Codebase: `prismlab/frontend/src/stores/gsiStore.ts` — `liveState.gold` already exposed
- `REQUIREMENTS.md` — "Out of Scope: Full item tree visualization — Information overload — show one level of components only"

### Secondary (MEDIUM confidence)
- OpenDota constants `/items` endpoint returns `"components": ["internal_name_1", ...]` — one level deep, confirmed by existing seed.py code that stores `info.get("components")` directly

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all patterns verified in existing codebase
- Architecture: HIGH — post-LLM enrichment pattern proven in Phase 21; component data already in DataCache
- Pitfalls: HIGH — all pitfalls derived from reading actual code paths (null guards, schema shape, cache TTL)

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable codebase, no external API dependency changes expected)
