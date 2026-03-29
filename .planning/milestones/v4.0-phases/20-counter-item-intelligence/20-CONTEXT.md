# Phase 20: Counter-Item Intelligence - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 20 refactors all counter-item rules from hardcoded hero-ID lists to ability-property queries using AbilityCached data from DataCache (built in Phase 19), adds 5 new counter-rule categories, enriches Claude's user message with pre-filtered ability context per opponent, and adds threat-level escalation so counter-item priority responds to enemy performance data. Backend only -- no frontend changes this phase.

</domain>

<decisions>
## Implementation Decisions

### Rule Refactoring Scope
- **D-01:** Full refactor -- all 14 counter-item rules converted to ability-property queries. Rules that can't cleanly map to ability properties (e.g., Magic Stick's "spell spammer" concept) use ability-first checking with hardcoded hero-ID fallback. No rule relies ONLY on hero ID lists after this phase.
- **D-02:** Self-hero rules (Quelling Blade, Boots, Mana Sustain, Mekansm) are NOT counter-item rules and stay hardcoded. Only rules matching against enemy heroes get refactored.
- **D-03:** Refactored rule reasoning names the specific ability from AbilityCached.dname. Example: "Against Witch Doctor's Death Ward (channeled), Eul's Scepter interrupts the channel" -- not generic "channeled abilities".

### New Counter Rules (5 new categories)
- **D-04:** Phase 20 adds 5 new counter-rule categories:
  1. **Eul's vs channeled ults** -- triggers on `ability.is_channeled` for ultimates
  2. **Lotus Orb / Linken's vs single-target ults** -- triggers on single-target behavior for high-impact ultimates
  3. **BKB-pierce awareness** -- warning annotation on BKB recommendations when enemy has BKB-piercing abilities. Does NOT suppress the BKB recommendation; adds note: "Note: Enemy X's Y ability pierces BKB -- BKB won't protect you from this specific threat."
  4. **Dispel items vs strong debuffs** -- Eul's/Lotus/Manta vs abilities with dispellable="No" or "Strong Dispels Only"
  5. **Hex/Root vs escape heroes** -- triggers on escape-type abilities (blink, invis, movement-based)
- **D-05:** Combined with refactored existing rules, the total ability-driven rule count should be 8+ rules.

### Ability Context for Claude
- **D-06:** Pre-filtered ability data sent in user message -- only abilities with counter-relevant properties: channeled, passive, BKB-pierce, dispellable=No/Strong. Each tagged with its property. ~150 tokens total. Example format: "Witch Doctor: Death Ward (channeled, BKB-pierce)".
- **D-07:** Ability annotations are inlined under each opponent in the existing Lane Opponents section of the user message (via context_builder._build_opponent_lines), not a separate section. Keeps ability context co-located with hero context.

### Threat Escalation
- **D-08:** Enemy performance data (KDA from screenshots/GSI, existing "fed/high threat" and "behind" annotations) flows into the rules engine as a threat_level per opponent. When an enemy is "fed/high threat", counter-item rules targeting that hero upgrade priority from "situational" to "core". Behind enemies downgrade from "core" to "situational".
- **D-09:** RuleResult schema gets a new `counter_target: str | None` field -- e.g., "Witch Doctor: Death Ward (channeled)". Structured data for downstream use (frontend tooltips, Claude context). Rules engine populates this for all ability-driven counter rules.

### Claude's Discretion
- Ability-property mapping strategy for rules that don't have a clean 1:1 mapping (e.g., which specific ability properties define "escape hero")
- Internal helper methods for ability querying on DataCache (e.g., heroes_with_channeled_ults, heroes_with_passives)
- How to detect "ultimate" vs "basic" abilities from the ability data
- Fallback hero lists for rules where ability data doesn't fully cover the concept
- Test strategy: which hero/ability combinations to use as test fixtures

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` -- CNTR-01, CNTR-02, CNTR-03, CNTR-04
- `.planning/ROADMAP.md` -- Phase 20 success criteria (4 criteria that must be TRUE)

### Phase 19 Foundation (dependency)
- `.planning/phases/19-data-foundation-prompt-architecture/19-CONTEXT.md` -- DataCache extensions, AbilityCached design, prompt architecture split
- `.planning/phases/19-data-foundation-prompt-architecture/19-03-SUMMARY.md` -- System prompt v4.0 directives already added

### Backend Files (existing patterns to modify)
- `prismlab/backend/engine/rules.py` -- All 18 existing rules, _hero_ids() pattern, evaluate() entry point, RulesEngine constructor takes DataCache
- `prismlab/backend/engine/schemas.py` -- RuleResult schema (needs counter_target field), RecommendRequest
- `prismlab/backend/data/cache.py` -- AbilityCached dataclass (is_channeled, is_passive, bkbpierce, dispellable, dmg_type), get_hero_abilities(hero_id)
- `prismlab/backend/engine/context_builder.py` -- _build_opponent_lines() where ability annotations will be inlined, _build_enemy_context_section() for threat data
- `prismlab/backend/engine/prompts/system_prompt.py` -- Counter-item naming directives (line 61-66), BKB-pierce distinction directive
- `prismlab/backend/engine/recommender.py` -- Where RulesEngine.evaluate() is called and results are assembled
- `prismlab/backend/tests/test_rules.py` -- Existing rule tests (pattern for new tests)

### Prior Phase Context
- `.planning/phases/16-backend-data-cache/16-CONTEXT.md` -- DataCache architecture, three-cache coherence
- `.planning/phases/14-recommendation-quality-system-hardening/14-CONTEXT.md` -- Rules expansion from Phase 14

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataCache.get_hero_abilities(hero_id)` returns `list[AbilityCached] | None` -- the primary data source for ability-driven rules
- `AbilityCached` has `is_channeled` and `is_passive` properties, plus `bkbpierce: bool`, `dispellable: str | None`, `dmg_type: str | None`, `behavior: tuple[str, ...]`
- `RulesEngine._hero_ids(*names)` pattern -- being replaced but useful as fallback builder
- `RulesEngine._hero_name(hero_id)` -- reuse for reasoning strings
- `_build_enemy_context_section()` already detects "fed, high threat" (kills>=5 and K/D>=2) and "behind" (deaths>=3 and D/K>=2) -- threat data source for escalation

### Established Patterns
- Rules return `list[RuleResult]` and iterate `req.lane_opponents` checking against hero sets
- Priority values: "core", "situational", "luxury"
- Phase values: "starting", "laning", "core", "late_game"
- Each rule has `break` after first match (one recommendation per rule per request)
- Context builder sections assembled with `\n\n`.join()

### Integration Points
- `rules.py` RulesEngine.__init__ already receives DataCache -- no new constructor wiring needed
- `schemas.py` RuleResult -- add `counter_target: str | None = None`
- `context_builder.py` _build_opponent_lines -- inline ability annotations
- `recommender.py` -- pass threat_level data to RulesEngine.evaluate() (new parameter or via request enrichment)
- `test_rules.py` -- new test cases for ability-driven rules with mock AbilityCached data

</code_context>

<specifics>
## Specific Ideas

- Ability-first with hardcoded fallback means each rule method follows: query abilities first, if no match check fallback hero list. The fallback lists should be smaller than current lists (only edge cases not caught by ability properties).
- BKB-pierce awareness is a warning annotation, not a block -- the rule fires normally but appends a note to reasoning. This respects that BKB helps vs OTHER enemies even if one ability pierces.
- The `counter_target` field on RuleResult enables future frontend work (Phase 21+ tooltips showing "counters: Death Ward") without schema changes later.
- Threat escalation via priority upgrade is the simplest mechanism -- "situational" becomes "core" for fed enemies, "core" becomes "situational" for behind enemies. No phase shifting, no new priority values.

</specifics>

<deferred>
## Deferred Ideas

- **Aeon Disk vs burst combos** -- considered for new rules but deferred to keep scope at 5 new categories
- **Blade Mail vs high-damage abilities** -- same, deferred
- **Frontend counter-item tooltips** -- counter_target field enables this but display is a future phase concern
- **Full enemy team ability context** (not just lane opponents) -- relevant for Phase 23 (Win Condition Framing) which needs full team data

</deferred>

---

*Phase: 20-counter-item-intelligence*
*Context gathered: 2026-03-27*
