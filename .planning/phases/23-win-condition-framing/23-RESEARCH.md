# Phase 23: Win Condition Framing - Research

**Researched:** 2026-03-27
**Domain:** Dota 2 draft archetype classification, Claude prompt engineering, backend context builder, frontend strategy display
**Confidence:** HIGH

## Summary

Phase 23 adds team-level win condition framing on top of the existing hybrid recommendation engine. The system already has Claude's system prompt stub for "Win Condition Framing" and the backend data model already accepts `allies: list[int]` in the RecommendRequest. The missing pieces are: (1) a backend classifier that maps the 10-hero draft (allied team + enemy team) to macro archetypes, (2) a `## Team Strategy` context section in the user message that Claude reads per its existing directive, and (3) frontend display of the win condition statement anchored above the item timeline.

The implementation follows a well-established pattern in this codebase: backend computes a data enrichment step, appends it to the Claude user message, and the frontend renders a new summary block. Phases 20–22 all used this exact pattern (counter ability tags, timing benchmarks, build path notes). Win condition framing is the fourth enrichment of this type.

The STATE.md blocker for this phase — "WCON-04 requires full enemy team data — current schema only sends lane_opponents" — is addressed by the existing `RecommendRequest.allies` field (already sending up to 4 ally IDs) and the existing `opponents` array in the Zustand store (5 slots). The missing link is wiring the full `opponents` array (not just `laneOpponents`) into the request for the purpose of enemy archetype classification.

**Primary recommendation:** Implement a pure-Python `WinConditionClassifier` that maps hero role distributions to archetypes. Feed its output into `ContextBuilder.build()` as a new `## Team Strategy` context section. The system prompt's existing "Win Condition Framing" directive will activate automatically when this section is present — no system prompt changes required. Add a `WinConditionBadge` component to `ItemTimeline.tsx` that renders above the strategy paragraph.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

### Claude's Discretion
All implementation choices are at Claude's discretion.

### Deferred Ideas (OUT OF SCOPE)
None — discuss phase skipped.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WCON-01 | System classifies 10-hero drafts into macro strategy archetypes (teamfight, split-push, pick-off, deathball, late-game scale) | WinConditionClassifier maps hero roles/tags to archetypes using DataCache hero data. Hero roles tuple already stored in HeroCached.roles. |
| WCON-02 | Win condition statement anchors overall_strategy and frames all item recommendations | `## Team Strategy` section in user message activates existing system prompt directive. overall_strategy from Claude is already rendered in ItemTimeline.tsx. |
| WCON-03 | Item priorities adjust based on win condition — early win condition deprioritizes luxury items; scaling teams get extended build paths | System prompt directive already contains this logic. The classifier produces confidence + archetype + enemy archetype which Claude consumes. |
| WCON-04 | System assesses enemy team's win condition and recommends counter-strategy items | Full enemy team (all 5 opponents) needs to be classified. RecommendRequest already has `allies` (4 slots); opponents slot needs expansion from `lane_opponents` only to full `opponents` array for classification. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.12 | 3.12 | Backend classifier | Project standard |
| Pydantic BaseModel | v2 (already in use) | WinConditionResult dataclass | Matches all other schemas in engine/schemas.py |
| React 18 + TypeScript | already in use | WinConditionBadge component | Project standard |
| Zustand | already in use | Store extension if needed | Project standard |
| Tailwind CSS v4 | already in use | Badge styling | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| DataCache | in-memory singleton | Hero role lookups for classifier | All hero data reads must use DataCache, zero DB queries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Python rule classifier | OpenDota meta API | API adds latency and external dependency; hero roles are already in DataCache |
| New API field for win condition | Embed in existing `## Team Strategy` user message section | Embedding in context follows Phase 19–22 pattern; new fields increase schema complexity |

**Installation:** No new packages required.

## Architecture Patterns

### Recommended Project Structure
New files needed:
```
prismlab/backend/engine/
├── win_condition.py      # WinConditionClassifier — new file
├── context_builder.py    # Add _build_team_strategy_section() — edit
├── schemas.py            # Add WinConditionResult pydantic model — edit
└── recommender.py        # Pass full opponents list to context builder — edit

prismlab/frontend/src/
├── components/timeline/
│   ├── WinConditionBadge.tsx   # New component: archetype pill + confidence
│   └── ItemTimeline.tsx        # Add WinConditionBadge above strategy text — edit
├── types/
│   └── recommendation.ts       # Add win_condition field to RecommendResponse — edit
└── api/
    └── client.ts               # No change needed (win_condition flows in RecommendResponse)
```

### Pattern 1: Backend Enrichment (follows Phase 20–22 pattern)
**What:** Compute structured data post-rules but before Claude, embed as a labeled section in the user message. Claude activates relevant directive section when it detects the header.
**When to use:** Any new context type that needs to reach Claude without modifying the system prompt.
**Example from Phase 21 (timing benchmarks):**
```python
# In context_builder.py
timing_section = self._build_timing_section(request.hero_id)
if timing_section:
    sections.append(f"## Item Timing Benchmarks\n{timing_section}")
```
Win condition follows identical structure:
```python
# In context_builder.py
strategy_section = self._build_team_strategy_section(request)
if strategy_section:
    sections.append(f"## Team Strategy\n{strategy_section}")
```

### Pattern 2: WinConditionClassifier — Role Distribution Scoring
**What:** Map each hero's `roles` tuple to archetype vote weights. Sum across allied team, normalize, pick archetype with highest score. Repeat for enemy team.
**When to use:** WCON-01 classification, called from ContextBuilder._build_team_strategy_section().

Archetype definitions based on Dota 2 role conventions:

| Archetype | Signal Heroes / Roles |
|-----------|----------------------|
| `teamfight` | Roles include "Disabler", "Nuker", "Initiator" (3+ heroes with these tags) |
| `split-push` | Roles include "Pusher"; or high carry count (Pos 1) with "Pusher" tag |
| `pick-off` | Roles include "Assassin" or "Ganker" on 2+ heroes |
| `deathball` | Roles include "Pusher" + "Initiator" combination for fast objective takes |
| `late-game scale` | High AGI/INT carry percentage; roles include "Carry" without early disabler mass |

Confidence: `high` if top archetype score >= 60% of total, `medium` if 40–60%, `low` if < 40%.

```python
# engine/win_condition.py (new file)
from dataclasses import dataclass
from data.cache import DataCache, HeroCached

ARCHETYPE_WEIGHTS: dict[str, dict[str, float]] = {
    "teamfight":     {"Disabler": 2.0, "Nuker": 1.5, "Initiator": 2.0, "Support": 0.5},
    "split-push":    {"Pusher": 3.0, "Carry": 1.0, "Escape": 0.5},
    "pick-off":      {"Assassin": 3.0, "Ganker": 2.5, "Escape": 1.0},
    "deathball":     {"Pusher": 2.0, "Initiator": 1.5, "Nuker": 1.0},
    "late-game scale": {"Carry": 2.5, "Durable": 1.0, "Support": 0.5},
}

@dataclass
class WinConditionResult:
    archetype: str           # "teamfight" | "split-push" | "pick-off" | "deathball" | "late-game scale"
    confidence: str          # "high" | "medium" | "low"
    archetype_scores: dict[str, float]  # raw scores for transparency

def classify_draft(hero_ids: list[int], cache: DataCache) -> WinConditionResult | None:
    """Classify a team's macro archetype from hero IDs."""
    # ... implementation
```

### Pattern 3: Request Schema Extension (WCON-04)
**What:** The full enemy team (`opponents`, all 5 slots) must reach the classifier for WCON-04. Currently only `lane_opponents` (max 2) are sent. Solution: add `all_opponents: list[int]` to `RecommendRequest` OR use the existing `allies` pattern and add an analogous `all_opponents` field.

**Decision:** Add `all_opponents: list[int] = Field(default_factory=list, max_length=5)` to `RecommendRequest`. This field carries all 5 opponent hero IDs for win condition classification. The `lane_opponents` field is unchanged — it continues to drive matchup data and counter-item rules. Only the win condition classifier uses `all_opponents`.

Frontend `useRecommendation.ts` maps `game.opponents.filter(Boolean)` to `all_opponents`.

### Pattern 4: Frontend WinConditionBadge
**What:** A small labeled pill showing the allied archetype above the `overall_strategy` text in `ItemTimeline.tsx`.
**Styling:** Follows existing phase label pattern in PhaseCard.tsx — `text-xs font-semibold uppercase tracking-wide font-display`. Archetype uses `text-secondary` (gold) for allied team, `text-dire` for enemy team if present.

```tsx
// WinConditionBadge.tsx
interface WinConditionBadgeProps {
  archetype: string;
  confidence: "high" | "medium" | "low";
  side: "allied" | "enemy";
}
```

### Pattern 5: RecommendResponse Extension
**What:** `win_condition` field added to `RecommendResponse` (backend Pydantic) and `RecommendResponse` (frontend TypeScript interface). This carries the classified archetype to the frontend for badge display.

```python
# In schemas.py — add to RecommendResponse
win_condition: WinConditionResponse | None = None
```

```typescript
// In recommendation.ts — add to RecommendResponse
win_condition?: WinConditionResponse | null;
```

### Anti-Patterns to Avoid
- **Calling OpenDota API in classifier:** Hero roles are already in `HeroCached.roles`. Zero external calls needed.
- **Putting archetype in system prompt:** The "Win Condition Framing" directive is already in the system prompt. Only the per-request data goes in the user message.
- **Hardcoding hero IDs:** Phase 20 proved that ability-property queries beat hero ID lists. Archetype classification uses `HeroCached.roles` — no hero IDs hardcoded.
- **Classifying with only lane_opponents:** WCON-04 requires full enemy team. Lane opponents (2 max) cannot represent a 5-hero enemy archetype.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hero role data | Separate hero taxonomy DB | HeroCached.roles already populated from OpenDota | All 124+ heroes already have roles as tuple[str, ...] |
| Win condition display state | New Zustand store | `RecommendResponse.win_condition` field (server-owned) | Win condition is derived from the draft state — no independent client state needed |
| Archetype-to-item rules | New rules engine expansion | Claude system prompt directive already handles this | System prompt already says "If early-peaking, recommend survivability; if outscaled, recommend early aggression" |

**Key insight:** The system prompt's existing `## Win Condition Framing` directive is already written and tested (test_system_prompt.py::test_win_condition_framing_directive passes). The missing piece is feeding it the `## Team Strategy` context section it checks for. The planner does NOT need to modify the system prompt.

## Common Pitfalls

### Pitfall 1: Classifying with Incomplete Draft
**What goes wrong:** User may not have all 5 opponents filled in, especially early in draft.
**Why it happens:** Optional hero slots in UI. all_opponents can have 0–5 entries.
**How to avoid:** Classifier returns `None` when fewer than 3 heroes provided (insufficient signal). ContextBuilder omits `## Team Strategy` section when classifier returns None, matching the same conditional pattern used for timing and ability sections.
**Warning signs:** `## Team Strategy` section appearing in context with only 1 hero listed.

### Pitfall 2: all_opponents vs lane_opponents Confusion
**What goes wrong:** Counter-item rules fire against `lane_opponents`. Win condition classifier uses `all_opponents`. Sending wrong list to wrong consumer produces garbage.
**Why it happens:** Two separate fields with similar names, different purposes.
**How to avoid:** Name the field clearly (`all_opponents` not `opponents`). Document in `RecommendRequest` docstring which downstream consumers use which field.

### Pitfall 3: System Prompt Token Budget Breach
**What goes wrong:** Expanding the system prompt to add win condition guidance pushes it past 5000 estimated tokens.
**Why it happens:** Temptation to add more specific archetype guidance to the system prompt.
**How to avoid:** DO NOT modify the system prompt. The directive is already present. Only the user message context section is new. The `test_system_prompt.py::test_token_budget` test will catch any budget breach.

### Pitfall 4: WinConditionResponse Not in LLM_OUTPUT_SCHEMA
**What goes wrong:** Adding win_condition to RecommendResponse breaks nothing since it's post-LLM enrichment (like timing_data and build_paths). But if it's accidentally added to LLM_OUTPUT_SCHEMA, Claude will try to generate it.
**Why it happens:** Confusion between LLM-generated fields and post-LLM enriched fields.
**How to avoid:** win_condition is computed by the Python classifier, NOT generated by Claude. It goes on RecommendResponse only, mirroring timing_data and build_paths. Never add it to LLM_OUTPUT_SCHEMA or LLMRecommendation.

### Pitfall 5: Roles Tuple is None for Some Heroes
**What goes wrong:** HeroCached.roles can be None if the hero was seeded without role data.
**Why it happens:** OpenDota API occasionally returns null roles for new heroes.
**How to avoid:** Classifier guards all `hero.roles` accesses with `if hero.roles` before iterating.

### Pitfall 6: RecommendResponse Cache Key Stale
**What goes wrong:** Adding `win_condition` to RecommendResponse doesn't invalidate existing cached responses — old responses will return `win_condition: null` even after implementation.
**Why it happens:** ResponseCache hashes the request, not the response schema.
**How to avoid:** Not a deployment concern for production (TTL is 300s). For development, clear the cache after schema changes. No action needed in the plan — same as phases 21 and 22.

## Code Examples

Verified patterns from codebase:

### How the post-LLM enrichment pattern works (from recommender.py)
```python
# Step 6b: Enrich with timing data (zero DB queries, uses DataCache)
timing_data: list[ItemTimingResponse] = []
if self.cache:
    timing_data = self._enrich_timing_data(request.hero_id, phases)

# Step 6c: Enrich with build path data (zero DB queries, uses DataCache)
build_paths: list[BuildPathResponse] = []
if self.cache:
    build_paths = self._enrich_build_paths(request, phases)
```
Win condition is NOT post-LLM enrichment — it's PRE-LLM context injection. The classifier runs before `context_builder.build()` so its output appears in the user message.

### How conditional context sections work (from context_builder.py)
```python
timing_section = self._build_timing_section(request.hero_id)
if timing_section:
    sections.append(f"## Item Timing Benchmarks\n{timing_section}")
```
Win condition follows this pattern exactly:
```python
strategy_section = self._build_team_strategy_section(request)
if strategy_section:
    sections.append(f"## Team Strategy\n{strategy_section}")
```

### How existing system prompt directive is triggered (from system_prompt.py)
```python
## Win Condition Framing
If a "Team Strategy" section is present in the context:
- Frame overall_strategy around the team's win condition, not just enemy counters.
- Connect item timing to strategy: early-peaking teams need items before the power window; \
  scaling teams need efficient buildup without sacrificing the mid-game.
- If the enemy team outscales, recommend items that enable early aggression.
- If the enemy team peaks early, recommend survivability items to weather the storm.
```
This directive fires when the user message contains `## Team Strategy`. No system prompt edits needed.

### Frontend WinConditionBadge placement (from ItemTimeline.tsx lines 46–55)
```tsx
{data.overall_strategy && (
  <div className="mb-2">
    <span className="text-secondary text-xs font-semibold uppercase tracking-wide font-display">
      Strategy
    </span>
    <p className="text-on-surface-variant text-sm italic mt-1">
      {data.overall_strategy}
    </p>
  </div>
)}
```
WinConditionBadge renders as an archetype pill INSIDE this block, between the "Strategy" label and the strategy text.

### HeroCached.roles access pattern (from data/cache.py)
```python
@dataclass(frozen=True)
class HeroCached:
    roles: tuple[str, ...] | None
    # ...
```
Classifier must guard: `if hero.roles: for role in hero.roles: ...`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Lane-only context | Allied + enemy full team context | Phase 23 | Win condition needs 5+5 hero draft |
| User message had timing section only | User message has timing + abilities + team strategy | Phase 19–23 | Richer Claude context without system prompt inflation |

**Deprecated/outdated:**
- None — this is additive, no deprecations.

## Open Questions

1. **Minimum hero count threshold for classification**
   - What we know: 3+ heroes usually enough to show a pattern; 1–2 heroes is noise.
   - What's unclear: Should the threshold be 3 allied heroes total, or 3 across both teams?
   - Recommendation: Require 3+ allied heroes OR 3+ enemy heroes (evaluate each team independently). Show allied archetype when allied threshold met; show enemy archetype when enemy threshold met.

2. **Confidence label display**
   - What we know: Classifier produces "high"/"medium"/"low" confidence.
   - What's unclear: Does the user care about confidence at all, or is it noisy?
   - Recommendation: Show confidence as a subtle visual distinction (e.g., gold border for high, grey border for low) rather than displaying the text label. Matches DESIGN.md's "show, don't tell" philosophy.

3. **Archetype for mixed/unusual drafts**
   - What we know: Some drafts don't fit neatly into one archetype.
   - What's unclear: Should the context section say "mixed draft — no dominant strategy" or pick the top archetype with low confidence?
   - Recommendation: Always emit the top-scoring archetype (even if low confidence) with the confidence qualifier. Claude then has information about uncertainty. A "mixed" label adds a new enum value with no additional value.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies — pure Python classifier using in-memory DataCache, no new CLI tools, services, or databases required).

## Sources

### Primary (HIGH confidence)
- Codebase: `prismlab/backend/engine/prompts/system_prompt.py` — Win Condition Framing directive already present; triggered by `## Team Strategy` section header
- Codebase: `prismlab/backend/engine/context_builder.py` — Established pattern for conditional context sections (_build_timing_section pattern)
- Codebase: `prismlab/backend/engine/schemas.py` — RecommendRequest already has `allies: list[int]`; WinConditionResult follows ComponentStep/BuildPathResponse dataclass pattern
- Codebase: `prismlab/backend/engine/recommender.py` — Post-LLM enrichment pattern for timing_data and build_paths
- Codebase: `prismlab/backend/tests/test_system_prompt.py` — `test_win_condition_framing_directive` confirms directive section name must stay "Win Condition Framing"
- Codebase: `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` — overall_strategy rendering; insertion point for WinConditionBadge
- Codebase: `prismlab/backend/data/cache.py` — HeroCached.roles: tuple[str, ...] | None confirmed
- STATE.md: "WCON-04 requires full enemy team data — current schema only sends lane_opponents" confirmed as the scope gap to address

### Secondary (MEDIUM confidence)
- Dota 2 wiki / competitive meta: Archetype taxonomy (teamfight, split-push, pick-off, deathball, late-game scale) matches the 5 archetypes in REQUIREMENTS.md WCON-01 and is consistent with high-MMR coaching terminology
- OpenDota hero roles taxonomy: roles like "Disabler", "Nuker", "Initiator", "Pusher", "Assassin", "Ganker", "Carry", "Support", "Durable", "Escape" are the canonical OpenDota role strings already stored in HeroCached.roles

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all patterns sourced from existing codebase
- Architecture: HIGH — all patterns directly mirrored from Phase 20–22 implementations in codebase
- Pitfalls: HIGH — sourced from direct code inspection of schemas.py, recommender.py, test_system_prompt.py

**Research date:** 2026-03-27
**Valid until:** Stable — classifier logic is domain-stable (Dota 2 role taxonomy changes slowly). Re-verify if OpenDota changes hero role field names.
