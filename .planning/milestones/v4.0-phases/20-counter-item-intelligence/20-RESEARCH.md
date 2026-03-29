# Phase 20: Counter-Item Intelligence - Research

**Researched:** 2026-03-27
**Domain:** Backend rules engine refactoring, ability-driven counter-item logic, Claude prompt enrichment
**Confidence:** HIGH

## Summary

Phase 20 converts all 14 enemy-matching counter-item rules from hardcoded hero ID lists to ability-property queries using the AbilityCached data loaded in Phase 19, adds 5 new counter-rule categories, enriches the Claude user message with pre-filtered ability context per opponent, and implements threat-level escalation for counter-item priority. This is a pure backend phase -- no frontend changes.

The existing codebase is well-structured for this refactoring. The `RulesEngine` already receives `DataCache` via constructor injection, `AbilityCached` already exposes `is_channeled`, `is_passive`, `bkbpierce`, `dispellable`, and `behavior` properties, and the `_build_opponent_lines` method in `context_builder.py` is the natural insertion point for ability annotations. The `_build_enemy_context_section` already computes threat annotations ("fed, high threat" / "behind") which can be extracted into a reusable threat_level classification.

**Primary recommendation:** Refactor rules in-place using ability-first-with-fallback pattern (query `DataCache.get_hero_abilities()` first, fall back to small hero ID sets only for edge cases where ability properties don't fully capture the concept). Add `counter_target` field to `RuleResult`. Build 3-4 helper methods on `RulesEngine` for common ability queries (channeled ults, passives, escape abilities, BKB-pierce, dispellable). Inline ability annotations into `_build_opponent_lines` per D-07.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full refactor -- all 14 counter-item rules converted to ability-property queries. Rules that can't cleanly map to ability properties (e.g., Magic Stick's "spell spammer" concept) use ability-first checking with hardcoded hero-ID fallback. No rule relies ONLY on hero ID lists after this phase.
- **D-02:** Self-hero rules (Quelling Blade, Boots, Mana Sustain, Mekansm) are NOT counter-item rules and stay hardcoded. Only rules matching against enemy heroes get refactored.
- **D-03:** Refactored rule reasoning names the specific ability from AbilityCached.dname. Example: "Against Witch Doctor's Death Ward (channeled), Eul's Scepter interrupts the channel" -- not generic "channeled abilities".
- **D-04:** Phase 20 adds 5 new counter-rule categories: (1) Eul's vs channeled ults, (2) Lotus Orb / Linken's vs single-target ults, (3) BKB-pierce awareness annotation, (4) Dispel items vs strong debuffs, (5) Hex/Root vs escape heroes.
- **D-05:** Combined with refactored existing rules, the total ability-driven rule count should be 8+ rules.
- **D-06:** Pre-filtered ability data sent in user message -- only abilities with counter-relevant properties. ~150 tokens total. Format: "Witch Doctor: Death Ward (channeled, BKB-pierce)".
- **D-07:** Ability annotations are inlined under each opponent in the existing Lane Opponents section via `context_builder._build_opponent_lines`, not a separate section.
- **D-08:** Enemy performance data flows into rules engine as threat_level per opponent. "fed/high threat" upgrades counter-item priority from "situational" to "core"; "behind" downgrades from "core" to "situational".
- **D-09:** RuleResult schema gets a new `counter_target: str | None` field. Rules engine populates this for all ability-driven counter rules.

### Claude's Discretion
- Ability-property mapping strategy for rules that don't have a clean 1:1 mapping (e.g., which specific ability properties define "escape hero")
- Internal helper methods for ability querying on DataCache (e.g., heroes_with_channeled_ults, heroes_with_passives)
- How to detect "ultimate" vs "basic" abilities from the ability data
- Fallback hero lists for rules where ability data doesn't fully cover the concept
- Test strategy: which hero/ability combinations to use as test fixtures

### Deferred Ideas (OUT OF SCOPE)
- Aeon Disk vs burst combos
- Blade Mail vs high-damage abilities
- Frontend counter-item tooltips (counter_target field enables this but display is future)
- Full enemy team ability context (not just lane opponents) -- relevant for Phase 23
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CNTR-01 | Counter-item rules query ability properties (channeled, passive, BKB-pierce) instead of hardcoded hero ID lists | AbilityCached already has is_channeled, is_passive, bkbpierce properties; DataCache.get_hero_abilities(hero_id) returns list; refactor each rule to query abilities first |
| CNTR-02 | System includes 5-8 new counter-item rules covering channeled ults, single-target ults, escape abilities, high regen, and burst damage patterns | 5 new rule categories defined in D-04; existing rules being refactored to ability-driven also count toward total |
| CNTR-03 | Counter-item reasoning names the specific enemy ability being countered | AbilityCached.dname provides display names (e.g., "Death Ward"); reasoning templates use f-string interpolation with ability name |
| CNTR-04 | Counter-item priority escalates based on enemy performance data (KDA from screenshots/GSI) | _build_enemy_context_section already classifies threat levels; extract classification, pass to rules engine, adjust priority strings |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack:** Python 3.12 + FastAPI + SQLAlchemy + SQLite backend; all changes in `prismlab/backend/`
- **Hybrid engine:** Rules fire first (instant, no API call) for obvious stuff. Claude API fires for reasoning/explanations and edge cases
- **Structured JSON output:** Parse and validate before returning to frontend
- **Dark theme with specific accent colors** (not relevant this phase -- backend only)
- **System prompt is the heart of the app:** Reasoning must sound like 8K+ MMR coach -- direct, specific, referencing actual hero abilities
- **Phase ordering:** Follow blueprint phases strictly. Phase 20 depends on Phase 19 (complete)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ (3.14.3 on machine) | Runtime | Project spec |
| FastAPI | existing | Web framework | Project spec |
| Pydantic | existing | Schema validation | Used for RuleResult, RecommendRequest |
| pytest | 9.0.2 | Test framework | Already in requirements.txt |
| pytest-asyncio | 1.3.0 | Async test support | Already in requirements.txt |

### Supporting
No new dependencies required. All work uses existing DataCache, AbilityCached, and Pydantic patterns.

## Architecture Patterns

### Files Modified (by scope)

```
prismlab/backend/
  engine/
    schemas.py              # Add counter_target field to RuleResult
    rules.py                # Refactor 14 rules + add 5 new rules + helper methods
    context_builder.py      # Inline ability annotations in _build_opponent_lines
    recommender.py          # Pass threat_level data to evaluate() (minor)
  tests/
    conftest.py             # Add test heroes, items, and ability data
    test_rules.py           # Major expansion: tests for all refactored + new rules
    test_context_builder.py # Tests for ability annotation in opponent lines
```

### Pattern 1: Ability-First with Fallback

**What:** Each counter-item rule queries `DataCache.get_hero_abilities(hero_id)` first, checks ability properties, then falls back to a small hero ID set for edge cases.

**When to use:** All 14 enemy-matching rules.

**Example:**
```python
def _silver_edge_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Silver Edge vs heroes with critical passives (Break)."""
    se_id = self._item_id("silver_edge")
    if se_id is None or req.role > 3:
        return []

    # Ability-first: check for passive abilities
    for op_id in req.lane_opponents:
        abilities = self.cache.get_hero_abilities(op_id)
        if abilities:
            passives = [a for a in abilities if a.is_passive]
            if passives:
                hero_name = self._hero_name(op_id)
                ability = passives[0]  # Use first passive for reasoning
                return [RuleResult(
                    item_id=se_id,
                    item_name="Silver Edge",
                    reasoning=(
                        f"Against {hero_name}'s {ability.dname} (passive), "
                        f"Silver Edge's Break disables their passives for 4 seconds."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {ability.dname} (passive)",
                )]

    # Fallback: heroes whose passives aren't well-captured by ability data
    fallback = self._hero_ids("Spectre")  # Minimal fallback set
    for op_id in req.lane_opponents:
        if op_id in fallback:
            hero_name = self._hero_name(op_id)
            return [RuleResult(
                item_id=se_id,
                item_name="Silver Edge",
                reasoning=(
                    f"Against {hero_name}'s passive abilities, "
                    f"Silver Edge's Break disables their passives for 4 seconds."
                ),
                phase="core",
                priority="situational",
                counter_target=f"{hero_name}: passive abilities",
            )]
    return []
```

### Pattern 2: Helper Methods for Ability Queries

**What:** Private helper methods on RulesEngine that encapsulate common ability queries.

**When to use:** When multiple rules need the same ability property check.

**Example:**
```python
def _has_channeled_ult(self, hero_id: int) -> AbilityCached | None:
    """Return the channeled ultimate ability, or None."""
    abilities = self.cache.get_hero_abilities(hero_id)
    if not abilities:
        return None
    for ability in abilities:
        if ability.is_channeled:
            return ability
    return None

def _has_passive(self, hero_id: int) -> AbilityCached | None:
    """Return the first passive ability, or None."""
    abilities = self.cache.get_hero_abilities(hero_id)
    if not abilities:
        return None
    for ability in abilities:
        if ability.is_passive:
            return ability
    return None

def _has_bkb_piercing(self, hero_id: int) -> list[AbilityCached]:
    """Return all BKB-piercing abilities for a hero."""
    abilities = self.cache.get_hero_abilities(hero_id)
    if not abilities:
        return []
    return [a for a in abilities if a.bkbpierce]

def _has_escape_ability(self, hero_id: int) -> AbilityCached | None:
    """Return an escape-type ability (blink, invis, movement), or None."""
    abilities = self.cache.get_hero_abilities(hero_id)
    if not abilities:
        return None
    escape_keywords = {"blink", "invis", "leap", "pounce", "ball_lightning",
                       "waveform", "time_walk", "phase_shift", "illusory_orb"}
    for ability in abilities:
        if any(kw in ability.key for kw in escape_keywords):
            return ability
    return None
```

### Pattern 3: Threat Level Extraction and Priority Adjustment

**What:** Extract the threat classification logic from `_build_enemy_context_section` into a reusable function that the rules engine can consume.

**When to use:** When rules need to adjust priority based on enemy performance.

**Example:**
```python
# In schemas.py or a shared utility
def compute_threat_level(ec: EnemyContext) -> str:
    """Classify enemy threat: 'high', 'normal', 'behind'."""
    k = ec.kills or 0
    d = ec.deaths or 0
    if (k >= 5 and d > 0 and k >= 2 * d) or (k >= 5 and d == 0):
        return "high"
    elif (d >= 3 and k > 0 and d >= 2 * k) or (d >= 3 and k == 0):
        return "behind"
    return "normal"

# In rules.py evaluate():
def evaluate(self, request: RecommendRequest) -> list[RuleResult]:
    # Build threat map from enemy_context
    threat_map: dict[int, str] = {}
    for ec in request.enemy_context:
        threat_map[ec.hero_id] = compute_threat_level(ec)

    results: list[RuleResult] = []
    for rule_fn in self._rules:
        results.extend(rule_fn(request))

    # Post-process: adjust priority based on threat
    for result in results:
        if result.counter_target is None:
            continue
        # Find which opponent this targets
        for op_id in request.lane_opponents:
            hero_name = self._hero_name(op_id)
            if hero_name in (result.counter_target or ""):
                threat = threat_map.get(op_id, "normal")
                if threat == "high" and result.priority == "situational":
                    result = result.model_copy(update={"priority": "core"})
                elif threat == "behind" and result.priority == "core":
                    result = result.model_copy(update={"priority": "situational"})
                break

    return results
```

Note: Because `RuleResult` is a Pydantic model (not frozen), priority can be adjusted. The pattern uses `model_copy(update=...)` for immutability safety.

### Pattern 4: Ability Annotations in Context Builder

**What:** Inline ability annotations under each opponent in `_build_opponent_lines`.

**When to use:** Building the Claude user message.

**Example:**
```python
async def _build_opponent_lines(self, hero_id, lane_opponents, db):
    lines: list[str] = []
    for opp_id in lane_opponents:
        opp_hero = self._get_hero(opp_id)
        opp_name = opp_hero.localized_name if opp_hero else "Unknown Hero"

        matchup = await get_or_fetch_matchup(hero_id, opp_id, db, self.opendota)
        if matchup and matchup.win_rate is not None:
            pct = round(matchup.win_rate * 100, 1)
            games = matchup.games_played or 0
            lines.append(f"- {opp_name}: {pct}% win rate over {games} games")
        else:
            lines.append(f"- {opp_name}: no matchup data available")

        # Inline ability annotations (D-06, D-07)
        ability_tags = self._get_counter_relevant_abilities(opp_id)
        if ability_tags:
            lines.append(f"  Threats: {ability_tags}")

    return "\n".join(lines)

def _get_counter_relevant_abilities(self, hero_id: int) -> str:
    """Pre-filter abilities to only counter-relevant properties."""
    abilities = self.cache.get_hero_abilities(hero_id)
    if not abilities:
        return ""
    tags = []
    for a in abilities:
        props = []
        if a.is_channeled:
            props.append("channeled")
        if a.is_passive:
            props.append("passive")
        if a.bkbpierce:
            props.append("BKB-pierce")
        if a.dispellable and a.dispellable.lower() in ("no", "strong dispels only"):
            props.append(f"dispellable={a.dispellable}")
        if props:
            tags.append(f"{a.dname} ({', '.join(props)})")
    return "; ".join(tags)
```

### Anti-Patterns to Avoid
- **Removing all fallback hero lists:** Some concepts (spell-spammer for Magic Stick, high-regen for Spirit Vessel) don't map cleanly to ability properties. Keep small fallback sets for edge cases.
- **Mutating RuleResult in-place during threat escalation:** Use `model_copy(update=...)` instead of direct attribute assignment.
- **Passing threat data as a global variable:** Thread it through the evaluate method signature or request enrichment, not a module global.
- **Over-filtering ability annotations:** D-06 says only counter-relevant properties. Don't dump all ability data into the user message.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ability property queries | Custom SQL queries per rule | `DataCache.get_hero_abilities(hero_id)` | Already cached, zero DB queries, synchronous |
| Threat classification | New threat scoring system | Reuse `_build_enemy_context_section` logic | Same thresholds (kills>=5, K/D>=2) already battle-tested |
| Schema validation | Manual dict checking | Pydantic `RuleResult` with `counter_target` field | Automatic validation, serialization |
| Ultimate detection | Hardcoded ability name lists | Check if ability key contains hero's ult name pattern | OpenDota ability keys follow `heroname_abilityname` naming |

## Common Pitfalls

### Pitfall 1: Ultimate Detection from Ability Data
**What goes wrong:** OpenDota ability data does NOT have an "is_ultimate" field. You cannot directly distinguish ults from basic abilities.
**Why it happens:** The API provides a flat list of abilities per hero. Ultimates are typically the last non-talent ability in the hero_abilities mapping, but this convention isn't guaranteed.
**How to avoid:** Use a heuristic: abilities are typically listed in skill order (Q, W, E, R). The channeled ability on Witch Doctor IS the ultimate. For the "channeled ults" rule (D-04 category 1), channeled abilities are rare enough that ALL channeled abilities are worth interrupting -- don't filter to ults only. For single-target ult detection, use a small curated list of high-impact single-target ultimate ability keys.
**Warning signs:** Tests failing because an ability is incorrectly classified as an ultimate.

### Pitfall 2: Escape Ability Detection
**What goes wrong:** "Escape" is a gameplay concept, not an ability property in the API data. No single field marks an ability as an escape.
**Why it happens:** Whether an ability is an "escape" depends on how it's used, not its raw properties.
**How to avoid:** Use ability key matching against known escape ability patterns (blink, leap, pounce, waveform, time_walk, ball_lightning, illusory_orb, shukuchi, windrun). Supplement with hero role tags -- heroes with "Escape" in their roles array from HeroCached are likely escape heroes. Keep a small fallback list for heroes whose escape ability doesn't have an obvious keyword.
**Warning signs:** Missing Anti-Mage blink, Slark pounce, QoP blink -- all critical escape abilities.

### Pitfall 3: Pydantic Model Immutability
**What goes wrong:** Trying to modify `RuleResult.priority` directly after creation during threat escalation.
**Why it happens:** Pydantic v2 models allow attribute setting by default but the pattern in this codebase treats them as immutable (break after first match, no mutation).
**How to avoid:** Use `result.model_copy(update={"priority": "core"})` to create a new instance with the adjusted priority. Or apply threat escalation as a post-processing step that builds new results.
**Warning signs:** Unexpected mutation affecting other rules' results.

### Pitfall 4: Missing Test Fixture Data
**What goes wrong:** New rules reference heroes/items/abilities not in the test conftest, causing `None` lookups and silent failures.
**Why it happens:** conftest.py only has 21 heroes, ~30 items, and ability data for AM and CM. New rules need Witch Doctor, Enigma, Lion, Puck, QoP abilities and Eul's, Lotus Orb, Linken's Sphere items.
**How to avoid:** Expand conftest with all heroes and items needed by the 5 new rules BEFORE writing rule tests. Use the same pattern (Hero/Item/HeroAbilityData rows).
**Warning signs:** Tests passing vacuously (no results returned because hero not found in cache).

### Pitfall 5: Breaking Existing Tests
**What goes wrong:** Refactoring existing rules to use ability properties changes behavior when ability data is missing for a test hero.
**Why it happens:** The ability-first pattern returns no match if `get_hero_abilities(hero_id)` returns None. If existing test heroes don't have ability data seeded, refactored rules silently stop matching.
**How to avoid:** Ensure ALL heroes used in existing test_rules.py tests have corresponding HeroAbilityData entries in conftest. Add ability data for Bristleback (id=69), Zeus (id=22), PA (id=12), Riki (id=32), Slark (id=93), etc. The fallback hero lists catch this too, but tests should validate the ability-first path.
**Warning signs:** Existing test_rules.py tests start failing after refactoring.

### Pitfall 6: BKB-Pierce Annotation Disrupting BKB Rule
**What goes wrong:** The BKB-pierce awareness rule (D-04 category 3) could be misunderstood as suppressing the BKB recommendation.
**Why it happens:** D-04 explicitly says it's a WARNING annotation, not a suppression. BKB still helps against OTHER abilities.
**How to avoid:** Implement as an addendum to reasoning text: "Note: Enemy X's Y ability pierces BKB -- BKB won't protect you from this specific threat." The BKB rule fires normally; the BKB-pierce check appends the note.
**Warning signs:** BKB not being recommended at all against heroes with BKB-piercing abilities.

## Code Examples

### RuleResult Schema Extension

```python
# In schemas.py
class RuleResult(BaseModel):
    """Output of a single deterministic rule evaluation."""

    item_id: int
    item_name: str
    reasoning: str
    phase: str  # "starting" | "laning" | "core" | "late_game"
    priority: str  # "core" | "situational" | "luxury"
    counter_target: str | None = None  # e.g. "Witch Doctor: Death Ward (channeled)"
```

### New Rule: Eul's vs Channeled Abilities

```python
def _euls_channel_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Eul's Scepter to interrupt channeled abilities."""
    euls_id = self._item_id("cyclone")  # Eul's internal name
    if euls_id is None:
        return []
    for op_id in req.lane_opponents:
        channeled = self._has_channeled_ability(op_id)
        if channeled:
            hero_name = self._hero_name(op_id)
            return [RuleResult(
                item_id=euls_id,
                item_name="Eul's Scepter of Divinity",
                reasoning=(
                    f"Against {hero_name}'s {channeled.dname} (channeled), "
                    f"Eul's Scepter interrupts the channel on cast. "
                    f"Also provides mana regen and movement speed."
                ),
                phase="core",
                priority="situational",
                counter_target=f"{hero_name}: {channeled.dname} (channeled)",
            )]
    return []
```

### Test Fixture: Witch Doctor Ability Data

```python
# In conftest.py, add to ability_data list
HeroAbilityData(
    hero_id=30,  # Witch Doctor
    abilities_json={
        "witch_doctor_paralyzing_cask": {
            "dname": "Paralyzing Cask",
            "behavior": "Unit Target",
            "dmg_type": "Magical",
            "bkbpierce": "No",
            "dispellable": "Strong Dispels Only",
        },
        "witch_doctor_voodoo_restoration": {
            "dname": "Voodoo Restoration",
            "behavior": ["No Target", "Toggle"],
            "dmg_type": None,
            "bkbpierce": None,
            "dispellable": None,
        },
        "witch_doctor_maledict": {
            "dname": "Maledict",
            "behavior": ["AOE", "Point Target"],
            "dmg_type": "Magical",
            "bkbpierce": "No",
            "dispellable": "No",
        },
        "witch_doctor_death_ward": {
            "dname": "Death Ward",
            "behavior": ["Channeled", "Point Target"],
            "dmg_type": "Physical",
            "bkbpierce": "Yes",
            "dispellable": None,
        },
    },
),
```

### Threat Level Classification (Extracted)

```python
def compute_threat_level(ec: EnemyContext) -> str:
    """Classify enemy threat level from KDA data.

    Matches the logic in context_builder._build_enemy_context_section:
    - fed/high threat: kills >= 5 and K/D >= 2 (or deaths == 0)
    - behind: deaths >= 3 and D/K >= 2 (or kills == 0)
    - normal: everything else
    """
    k = ec.kills or 0
    d = ec.deaths or 0
    if (k >= 5 and d > 0 and k >= 2 * d) or (k >= 5 and d == 0):
        return "high"
    elif (d >= 3 and k > 0 and d >= 2 * k) or (d >= 3 and k == 0):
        return "behind"
    return "normal"
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | None (convention-based, tests/ directory) |
| Quick run command | `cd prismlab/backend && python -m pytest tests/test_rules.py -x -q` |
| Full suite command | `cd prismlab/backend && python -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CNTR-01 | Rules query ability properties instead of hero IDs | unit | `python -m pytest tests/test_rules.py::TestAbilityDrivenRules -x` | No -- Wave 0 |
| CNTR-01 | Fallback hero IDs fire when ability data missing | unit | `python -m pytest tests/test_rules.py::TestAbilityFallback -x` | No -- Wave 0 |
| CNTR-02 | 5 new counter-rule categories fire correctly | unit | `python -m pytest tests/test_rules.py::TestNewCounterRules -x` | No -- Wave 0 |
| CNTR-02 | Rule count >= 23 (18 existing + 5 new) | unit | `python -m pytest tests/test_rules.py::TestRuleCount -x` | Yes (update needed) |
| CNTR-03 | Reasoning names specific ability dname | unit | `python -m pytest tests/test_rules.py::TestReasoningNamesAbility -x` | No -- Wave 0 |
| CNTR-03 | counter_target field populated on ability-driven rules | unit | `python -m pytest tests/test_rules.py::TestCounterTargetField -x` | No -- Wave 0 |
| CNTR-04 | Fed enemy upgrades counter-item from situational to core | unit | `python -m pytest tests/test_rules.py::TestThreatEscalation -x` | No -- Wave 0 |
| CNTR-04 | Behind enemy downgrades counter-item from core to situational | unit | `python -m pytest tests/test_rules.py::TestThreatEscalation -x` | No -- Wave 0 |
| D-06/D-07 | Ability annotations appear in opponent lines | unit | `python -m pytest tests/test_context_builder.py::TestAbilityAnnotations -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/backend && python -m pytest tests/test_rules.py -x -q`
- **Per wave merge:** `cd prismlab/backend && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Expand `conftest.py` with: Witch Doctor (id=30), Enigma (id=33 -- hero exists, needs abilities), Puck, QoP, Storm Spirit heroes + ability data
- [ ] Add items to conftest: Eul's Scepter, Lotus Orb, Linken's Sphere, Scythe of Vyse, Rod of Atos
- [ ] Add HeroAbilityData for ALL existing test heroes used by current rules (Bristleback, Zeus, PA, Riki, Slark, etc.) to prevent silent failures
- [ ] New test classes in `test_rules.py`: TestAbilityDrivenRules, TestNewCounterRules, TestReasoningNamesAbility, TestCounterTargetField, TestThreatEscalation
- [ ] New test class in `test_context_builder.py`: TestAbilityAnnotations

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded hero ID sets per rule | Ability-property queries + small fallback | Phase 20 | Rules adapt to new heroes automatically when ability data is fetched |
| Generic "against X" reasoning | Specific ability naming in reasoning | Phase 20 | User sees exactly which ability is being countered |
| Flat priority (no escalation) | Threat-adjusted priority | Phase 20 | Counter-items prioritized against enemies that are winning |

## Open Questions

1. **Eul's internal item name**
   - What we know: Item internal names in the DB follow OpenDota naming (e.g., "bkb", "monkey_king_bar")
   - What's unclear: Eul's Scepter might be "cyclone" or "wind_lace" or another name in the DB
   - Recommendation: Check DB items or OpenDota constants for Eul's, Lotus, Linken's internal names before writing rules. These must match what's seeded.

2. **Hero IDs for new test fixtures**
   - What we know: Witch Doctor is hero_id 30 in OpenDota. Puck is 13. QoP is 39. Storm Spirit is 17.
   - What's unclear: Need to verify these IDs match what OpenDota uses
   - Recommendation: Cross-reference with existing conftest hero IDs (known correct) and OpenDota constants

3. **Ability data completeness for all 124+ heroes**
   - What we know: Phase 19 fetches and caches ability data. But some heroes may have incomplete ability metadata.
   - What's unclear: What percentage of heroes have proper channeled/passive/bkbpierce tags in OpenDota data
   - Recommendation: The fallback hero ID lists protect against gaps. Test with known-good heroes (WD Death Ward is definitely channeled).

## Sources

### Primary (HIGH confidence)
- `prismlab/backend/data/cache.py` -- AbilityCached dataclass with is_channeled, is_passive, bkbpierce, dispellable, behavior properties
- `prismlab/backend/engine/rules.py` -- All 18 existing rules, patterns, hero ID sets
- `prismlab/backend/engine/schemas.py` -- RuleResult, RecommendRequest, EnemyContext schemas
- `prismlab/backend/engine/context_builder.py` -- _build_opponent_lines, _build_enemy_context_section patterns
- `prismlab/backend/tests/conftest.py` -- Test fixture patterns for heroes, items, ability data
- `prismlab/backend/tests/test_rules.py` -- Existing test patterns

### Secondary (MEDIUM confidence)
- OpenDota API constants/abilities schema -- verified via dotaconstants repo and existing AbilityCached mapping
- Phase 19 summaries -- confirm ability data and system prompt v4.0 directives are in place

### Tertiary (LOW confidence)
- Exact OpenDota internal names for Eul's, Lotus Orb, Linken's Sphere items -- need DB verification
- Hero ID assignments for Witch Doctor, Puck, QoP, Storm Spirit -- need OpenDota constants verification

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all existing patterns
- Architecture: HIGH - patterns derived directly from existing codebase examination
- Pitfalls: HIGH - identified from concrete code review (missing test fixtures, ability data gaps, ult detection limitations)

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable domain -- Dota 2 ability properties don't change architecture)
