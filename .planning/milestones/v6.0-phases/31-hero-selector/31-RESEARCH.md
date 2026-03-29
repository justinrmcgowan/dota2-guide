# Phase 31: Hero Selector - Research

**Researched:** 2026-03-29
**Domain:** Draft hero suggestion — backend scoring API + frontend inline panel
**Confidence:** HIGH

## Summary

Phase 31 adds a "Suggest Hero" flow to the draft input panel. Before locking in their hero, the user can request a ranked list of hero candidates filtered to their selected role/position and scored by ally synergy, enemy counter-value, and predicted win rate (using Phase 30's matrices). The user can then click a suggestion to populate the "Your Hero" field and proceed to the recommendation flow.

The core scoring logic lives entirely on the backend as a new POST `/api/suggest-hero` endpoint. The synergy and counter matrices are already loaded in `DataCache._matrices` at startup. Role filtering uses the `HERO_PLAYSTYLE_MAP` (frontend utility, keyed `"{hero_id}-{role}"`) as the ground truth for hero-role viability — heroes in the map for the requested role pass the filter. The UI integration point is an inline expansion below the "Your Hero" section in the Sidebar, toggled by a "Suggest Hero" button that appears when no hero is selected and role/lane are set.

The key engineering risk is that `matrices.json` is a placeholder in the repo (all empty arrays). The scoring engine must degrade gracefully when matrices are absent — falling back to alphabetical ordering — rather than erroring. The `_win_predictor_ready` flag on `DataCache` is the check gate for matrix availability.

**Primary recommendation:** New dedicated `/api/suggest-hero` endpoint on the backend, inline expansion panel in the Sidebar frontend. No modal needed — the sidebar already has the full draft context and the inline pattern matches the existing AllyPicker/OpponentPicker expand-on-click pattern exactly.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — discuss phase was skipped per workflow.skip_discuss setting.

### Claude's Discretion
All implementation choices are at Claude's discretion. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key context from Phase 30:
- WinPredictor class exists with predict() method returning win probability
- Synergy/counter matrices loaded in DataCache (matrices.json with hero_id_to_index, synergy[], counter[])
- XGBoost models per MMR bracket available via DataCache
- Phase 31 consumes the matrices computed by Phase 30's training pipeline

### Deferred Ideas (OUT OF SCOPE)
None — discuss phase skipped.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HERO-01 | Given a partial draft (0-9 heroes), user's role (Pos 1-5), and lane, the system suggests top N hero picks ranked by predicted win rate | Scoring formula uses DataCache matrices; backend scores all heroes not already in draft, ranks by composite score |
| HERO-02 | Hero suggestions factor in synergy with already-picked allies and counter-value against already-picked enemies | `matrices[bracket].synergy[a][b]` and `matrices[bracket].counter[a][b]` are the direct data sources; scoring formula defined in Architecture Patterns |
| HERO-03 | Suggestions are filtered by role/lane viability (heroes that can play the selected position) | `HERO_PLAYSTYLE_MAP` (frontend) and its Python equivalent (backend) provide position-to-hero filtering; heroes without entries for requested role are excluded |
| HERO-04 | Hero suggestion UI integrates into the existing draft input flow as an optional "Suggest Hero" step before recommendations | Inline expansion below "Your Hero" in Sidebar.tsx; matches existing AllyPicker expand-on-click pattern |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | Existing | New `/api/suggest-hero` endpoint | Already used — no new dependency |
| Pydantic | Existing | SuggestHeroRequest/Response schema | Already used throughout engine/schemas.py |
| DataCache | Existing | Access to `_matrices` (synergy/counter) and `_heroes` | Phase 30 loaded matrices at startup |
| React + Zustand | Existing | Inline suggestion panel with hero list | Already used in all draft components |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| HERO_PLAYSTYLE_MAP | Existing (heroPlaystyles.ts) | Position filtering source of truth | Backend needs a Python mirror of this map |
| useHeroes() hook | Existing | Hero data for rendering suggestion cards | Already used in HeroPicker; reusable |
| HeroPortrait | Existing | Render each suggested hero | Already used in HeroPicker dropdown |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline expand in Sidebar | Modal dialog | Modal adds complexity, breaks the "sidebar-only" input flow; inline matches AllyPicker pattern already in the codebase |
| Backend scoring | Frontend scoring (fetch matrices.json) | Frontend scoring would require downloading the full ~10MB+ real matrices file; backend is correct location for data-intensive scoring |
| HERO_PLAYSTYLE_MAP for role filter | hero.roles[] from OpenDota | OpenDota `roles` field is editorial tags ("Carry", "Support") — NOT positions. `HERO_PLAYSTYLE_MAP` is the curated hero-position mapping already used for playstyle auto-detection |

**Installation:** No new packages required.

## Architecture Patterns

### Recommended Project Structure
```
prismlab/backend/engine/
├── hero_selector.py        # NEW: HeroSelector class with score_candidates()
prismlab/backend/engine/schemas.py
    SuggestHeroRequest      # NEW Pydantic model
    SuggestHeroResponse     # NEW Pydantic model
    HeroSuggestion          # NEW Pydantic model (single ranked candidate)
prismlab/backend/api/routes/
├── suggest_hero.py         # NEW: POST /api/suggest-hero route
prismlab/backend/main.py    # EDIT: include suggest_hero router

prismlab/frontend/src/
├── api/client.ts           # EDIT: add suggestHero() method
├── types/hero.ts           # EDIT: add HeroSuggestion type (or new file)
├── stores/gameStore.ts     # EDIT: add heroSuggestions state + actions
├── components/draft/
│   ├── HeroSuggestPanel.tsx  # NEW: ranked suggestion list component
│   └── SuggestHeroButton.tsx # NEW: trigger button
prismlab/frontend/src/components/layout/
└── Sidebar.tsx             # EDIT: wire in HeroSuggestPanel below "Your Hero"
```

### Pattern 1: Backend Scoring Formula
**What:** Score each candidate hero using synergy + counter + individual win rate signals from the matrices, then sort descending.

**Formula (per candidate hero C):**
```
synergy_score = mean(synergy[C_idx][A_idx] for A in allies if matrix cell != None)
counter_score = mean(counter[C_idx][E_idx] - 0.5 for E in enemies if matrix cell != None)
    # counter[a][b] = win rate of a vs b; subtract 0.5 to center around 0
individual_wr = individual win rate from matrix baseline (if available) else 0.5
composite = (synergy_score * 0.4) + (counter_score * 0.4) + (individual_wr - 0.5) * 0.2
```

When matrices are absent (placeholder or empty): `composite = 0.0` for all candidates — sort is then alphabetical by hero name to ensure deterministic output.

**When to use:** Always when `/api/suggest-hero` is called.

**Example:**
```python
# Source: matrices structure defined in train_win_predictor.py (Step 6-7)
def score_candidates(
    candidate_ids: list[int],
    ally_ids: list[int],
    enemy_ids: list[int],
    bracket_data: dict,  # DataCache._matrices[bracket]
) -> dict[int, float]:
    hero_id_to_index = {int(k): v for k, v in bracket_data.get("hero_id_to_index", {}).items()}
    synergy = bracket_data.get("synergy", [])
    counter = bracket_data.get("counter", [])
    scores = {}
    for hid in candidate_ids:
        c_idx = hero_id_to_index.get(hid)
        if c_idx is None or not synergy or not counter:
            scores[hid] = 0.0
            continue
        syn_vals = [synergy[c_idx][hero_id_to_index[a]] for a in ally_ids
                    if hero_id_to_index.get(a) is not None
                    and synergy[c_idx][hero_id_to_index[a]] is not None]
        ctr_vals = [counter[c_idx][hero_id_to_index[e]] - 0.5 for e in enemy_ids
                    if hero_id_to_index.get(e) is not None
                    and counter[c_idx][hero_id_to_index[e]] is not None]
        syn = sum(syn_vals) / len(syn_vals) if syn_vals else 0.0
        ctr = sum(ctr_vals) / len(ctr_vals) if ctr_vals else 0.0
        scores[hid] = syn * 0.4 + ctr * 0.4  # individual_wr enrichment optional
    return scores
```

### Pattern 2: Role Filtering via HERO_PLAYSTYLE_MAP
**What:** The HERO_PLAYSTYLE_MAP (`heroPlaystyles.ts`) maps `"{hero_id}-{role}"` → playstyle string. Heroes that have an entry for the requested role are viable; all others are excluded from suggestions.

**Python mirror pattern:**
```python
# Source: heroPlaystyles.ts — transcribe to backend/engine/hero_selector.py
HERO_ROLE_VIABLE: dict[int, set[int]] = {}
# keyed by role (1-5), values are sets of hero_ids viable for that role
# Derived from HERO_PLAYSTYLE_MAP keys: "1-1" → hero_id=1 viable for role=1
```

The Python mirror must be kept in sync with `heroPlaystyles.ts`. The source of truth is the TypeScript file; the Python copy is a static transcription. Document this sync requirement as a comment in the backend file.

**When to use:** Role filter step before scoring — exclude heroes not in `HERO_ROLE_VIABLE[requested_role]`.

### Pattern 3: Frontend Inline Expansion
**What:** SuggestHeroPanel appears below "Your Hero" when no hero is selected and role/lane are set. A "Suggest Hero" button triggers the panel. Selecting a hero from the panel calls `selectHero(hero)` on gameStore, collapsing the panel.

**Integration in Sidebar.tsx:**
```tsx
// Below the HeroPicker block, after "Your Hero" heading
{!selectedHero && role !== null && (
  <SuggestHeroPanel onSelect={selectHero} excludedHeroIds={excludedIds} />
)}
```

**When to use:** Whenever user has not yet selected their hero but has a role.

### Pattern 4: Request/Response Schema
**New Pydantic models (add to engine/schemas.py):**
```python
class SuggestHeroRequest(BaseModel):
    role: int = Field(ge=1, le=5)
    ally_ids: list[int] = Field(default_factory=list, max_length=4)
    enemy_ids: list[int] = Field(default_factory=list, max_length=5)
    excluded_hero_ids: list[int] = Field(default_factory=list)  # already in draft
    top_n: int = Field(default=10, ge=1, le=30)
    bracket: int = Field(default=2, ge=1, le=4)  # default Archon-Legend (same as WinPredictor)

class HeroSuggestion(BaseModel):
    hero_id: int
    hero_name: str
    internal_name: str
    icon_url: str | None
    score: float           # composite score for UI display or debug
    synergy_score: float   # breakdown for tooltip
    counter_score: float   # breakdown for tooltip

class SuggestHeroResponse(BaseModel):
    suggestions: list[HeroSuggestion]
    matrices_available: bool  # False when placeholder matrices in place
```

### Pattern 5: API Client Extension
```typescript
// Add to api/client.ts
suggestHero: (req: SuggestHeroRequest) =>
  postJson<SuggestHeroRequest, SuggestHeroResponse>("/suggest-hero", req),
```

### Anti-Patterns to Avoid
- **Using hero.roles[] for position filtering:** OpenDota's `roles` field contains editorial tags like `"Carry"`, `"Support"`, `"Nuker"` — these do NOT map 1:1 to positions 1-5. Anti-Mage has `["Carry", "Escape"]` but no explicit "position 1" tag. Use `HERO_PLAYSTYLE_MAP` instead.
- **Calling WinPredictor.predict() per candidate:** predict() requires a full 10-hero draft. With a partial draft it returns None. Do not use it for per-candidate scoring — use the matrices directly.
- **Downloading full matrices to frontend:** The real matrices file will be large (N×N floats for 126+ heroes, 4 brackets). Keep scoring server-side.
- **Blocking the event loop with scoring:** All DataCache reads are synchronous dict/list reads — no I/O. Scoring 120+ heroes is fast enough to run inline in the async endpoint without a thread pool. Benchmark first; if >100ms, offload via `asyncio.to_thread`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hero search/filtering in suggestion UI | Custom search box | Reuse HeroPicker's filtered results as the starting point; HeroSuggestPanel is a ranked list, not a search box | HeroPicker already handles fuzzy search, excludedHeroIds, empty-state; suggestion list just needs a ranked display |
| Hero icon URLs | Custom URL builder | Use existing `heroIconUrl(heroSlugFromInternal(internal_name))` from `imageUrls.ts` | Already used in HeroSlot and HeroPortrait; Steam CDN pattern is established |
| Bracket detection | Parse MMR from somewhere | Default to bracket 2 (Archon-Legend) — same decision as WinPredictor (logged in STATE.md) | Consistent with existing Phase 30 decision |

**Key insight:** The scoring engine is the only net-new algorithmic work. All UI rendering, hero lookup, and API plumbing can reuse existing patterns.

## Common Pitfalls

### Pitfall 1: Matrices Placeholder Returns Empty Arrays
**What goes wrong:** `matrices.json` in the repo is a placeholder with `"synergy": []` and `"counter": []`. If the scorer indexes into empty lists, it will raise an `IndexError` instead of gracefully returning zero scores.
**Why it happens:** Phase 30 committed placeholder artifacts so the runtime integration could be coded before real training data exists.
**How to avoid:** Check `len(synergy) > 0` before any indexing. The `matrices_available: bool` flag in the response lets the frontend show a "matrices not trained yet" notice.
**Warning signs:** `IndexError` in suggest-hero endpoint on first deployment.

### Pitfall 2: hero_id_to_index Keys Are Strings in JSON
**What goes wrong:** `matrices.json` stores keys as strings (`"1"`, `"2"`) not integers. Direct `hero_id_to_index[hero_id]` with an integer key misses.
**Why it happens:** JSON object keys are always strings. The training script stores `{str(k): v for k, v in hero_id_to_index.items()}`.
**How to avoid:** Mirror the pattern in `win_predictor.py`: `{int(k): v for k, v in raw_mapping.items()}` before any lookups.
**Warning signs:** All candidates get score 0.0 despite matrices being populated.

### Pitfall 3: HERO_PLAYSTYLE_MAP Does Not Cover All Heroes
**What goes wrong:** Many heroes have no entry in `HERO_PLAYSTYLE_MAP` for certain roles. If the filter is applied too strictly, the suggestion list is very short (e.g., Pos 5 may only have 20 heroes listed).
**Why it happens:** The map was built incrementally and focuses on popular/meta picks.
**How to avoid:** Use a two-tier approach: primary candidates (heroes in HERO_PLAYSTYLE_MAP for the role), secondary pool (heroes with matching OpenDota `roles` tag heuristic OR all heroes if primary pool < 5). This gives a reasonable list even when the map is sparse. Alternatively, accept a short list — better to show 10 highly curated suggestions than 120 unfiltered ones.
**Warning signs:** Empty or near-empty suggestion list for Pos 4/5 edge cases.

### Pitfall 4: counter[a][b] Semantics
**What goes wrong:** Treating `counter[a][b] = 1.0` as "a counters b perfectly" when it means "a wins 100% of games when b is on the opposing team." Centering around 0.5 is required for the score to be meaningful.
**Why it happens:** Raw counter values are win rates (0.0–1.0), not counter deltas.
**How to avoid:** Subtract 0.5 from counter values: `counter_score = counter[c][e] - 0.5`. A value of +0.1 means candidate c wins 60% vs enemy e.
**Warning signs:** All counter scores being positive (around 0.5) instead of centered near 0.

### Pitfall 5: Inline Panel Conflicts With HeroPicker Open State
**What goes wrong:** When SuggestHeroPanel is visible and user starts typing in the HeroPicker (which sits above it), both are open simultaneously and compete for vertical space.
**Why it happens:** HeroPicker manages its own dropdown state via local `isOpen` state.
**How to avoid:** SuggestHeroPanel should auto-close when HeroPicker's input is focused. Use a shared `isSuggestOpen` state flag in the component or Sidebar-local state. When HeroPicker receives focus, set `isSuggestOpen(false)`.
**Warning signs:** Sidebar overflow/scroll during combined open state.

## Code Examples

### Backend Scoring Scaffold
```python
# Source: train_win_predictor.py compute_synergy_matrix / compute_counter_matrix
# Matrix shapes: synergy[n_heroes][n_heroes] list of list of float|None (symmetric)
# counter[n_heroes][n_heroes] list of list of float|None (asymmetric)

def get_bracket_matrices(cache: DataCache, bracket: int) -> tuple[list, list, dict]:
    """Return (synergy, counter, hero_id_to_index) for the given bracket.

    All three are empty/empty/empty when placeholder matrices are in place.
    """
    bracket_data = cache._matrices.get(bracket, {})
    raw_mapping = bracket_data.get("hero_id_to_index", {})
    hero_id_to_index = {int(k): v for k, v in raw_mapping.items()}
    synergy = bracket_data.get("synergy", [])
    counter = bracket_data.get("counter", [])
    return synergy, counter, hero_id_to_index
```

### Frontend SuggestHeroPanel Integration Point (Sidebar.tsx)
```tsx
// Source: existing Sidebar.tsx pattern — animated reveal used for PlaystyleSelector
{!selectedHero && role !== null && (
  <div className={`transition-all duration-200 ease-out overflow-hidden ${
    showSuggestions ? "max-h-96 opacity-100 mt-2" : "max-h-0 opacity-0"
  }`}>
    <HeroSuggestPanel
      role={role}
      allyIds={allies.filter(Boolean).map(h => h!.id)}
      enemyIds={opponents.filter(Boolean).map(h => h!.id)}
      excludedHeroIds={excludedIds}
      onSelect={(hero) => { selectHero(hero); setShowSuggestions(false); }}
    />
  </div>
)}
```

### API Client Extension
```typescript
// Source: client.ts postJson pattern
export interface SuggestHeroRequest {
  role: number;
  ally_ids: number[];
  enemy_ids: number[];
  excluded_hero_ids: number[];
  top_n?: number;
  bracket?: number;
}

export interface HeroSuggestion {
  hero_id: number;
  hero_name: string;
  internal_name: string;
  icon_url: string | null;
  score: number;
  synergy_score: number;
  counter_score: number;
}

export interface SuggestHeroResponse {
  suggestions: HeroSuggestion[];
  matrices_available: boolean;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hero selection = manual search only | Hero selection + ranked ML suggestions | Phase 31 | User can discover counter-picks/synergies without knowing the meta |
| `WinPredictor.predict()` requires full draft | Matrix-level scoring works with partial drafts | Phase 31 design | Enables hero suggestion before draft is complete |

**Deprecated/outdated:**
- `MatchupData` DB table: Seeded but never populated with real data (legacy Phase 1 schema). The Phase 30 `matrices.json` replaces this for synergy/counter data. Do not use `MatchupData` in Phase 31.

## Open Questions

1. **Should lane influence scoring?**
   - What we know: The matrices don't have lane-segmented data. Counter values are game-wide.
   - What's unclear: Lane viability (e.g., Axe on safe lane is suboptimal) could be a filter dimension.
   - Recommendation: Use HERO_PLAYSTYLE_MAP for both role AND lane viability inference — if a hero appears in the map for the role, treat them as lane-viable. Lane context is informational in the UI, not a hard filter at this stage.

2. **How many suggestions to show?**
   - What we know: Top 10 is a reasonable default per HERO-01 ("top N").
   - What's unclear: Whether to show score numbers or only relative ranking.
   - Recommendation: Show top 10. Display scores as percentage bars or rank numbers for transparency. Hide raw floats.

3. **Bracket selection: user-configurable or hardcoded default?**
   - What we know: STATE.md decision: bracket_2 (Archon-Legend) is the default for WinPredictor.
   - What's unclear: Whether the user's MMR is known.
   - Recommendation: Default bracket 2. No settings UI change needed for Phase 31.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — Phase 31 uses existing DataCache/matrices infrastructure from Phase 30 with no new tools, services, or runtimes required).

## Sources

### Primary (HIGH confidence)
- `prismlab/backend/engine/win_predictor.py` — WinPredictor.predict(), build_feature_vector(), hero_id_to_index int() cast pattern
- `prismlab/backend/scripts/train_win_predictor.py` — matrix schemas: synergy[a][b] = delta from baseline, counter[a][b] = raw win rate
- `prismlab/backend/data/cache.py` — DataCache._matrices structure, _win_predictor_ready flag, load_win_predictor() pattern
- `prismlab/frontend/src/utils/heroPlaystyles.ts` — HERO_PLAYSTYLE_MAP as role viability source of truth
- `prismlab/frontend/src/utils/constants.ts` — PLAYSTYLE_OPTIONS, ROLE_OPTIONS
- `prismlab/frontend/src/components/layout/Sidebar.tsx` — integration point location
- `prismlab/frontend/src/components/draft/AllyPicker.tsx` — inline expand pattern to replicate
- `prismlab/frontend/src/components/draft/HeroPicker.tsx` — hero list rendering with excludedHeroIds
- `prismlab/backend/engine/schemas.py` — RecommendRequest/Response patterns to follow for new schemas
- `prismlab/backend/api/routes/recommend.py` — route + singleton pattern to replicate
- `.planning/STATE.md` — bracket_2 default decision, placeholder matrices decision

### Secondary (MEDIUM confidence)
- `prismlab/backend/models/matrices.json` — confirmed placeholder structure; real structure verified from training script

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — entirely existing codebase, no new dependencies
- Architecture: HIGH — matrix structure fully understood from training script source; scoring formula derived from how synergy/counter matrices are defined
- Pitfalls: HIGH — confirmed from Phase 30 research decisions (string key casting, placeholder handling) and direct inspection of matrix code
- Role filtering: HIGH — HERO_PLAYSTYLE_MAP is the established source of truth; OpenDota roles limitation confirmed by seed.py inspection

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable codebase; only invalidates if matrices format changes on patch retrain)
