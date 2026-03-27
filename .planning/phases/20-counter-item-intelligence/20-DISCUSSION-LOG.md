# Phase 20: Counter-Item Intelligence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 20-counter-item-intelligence
**Areas discussed:** Rule refactoring scope, New counter rules, Ability context for Claude, Threat escalation

---

## Rule Refactoring Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full refactor | Convert all 14 counter-item rules to ability-property queries. Rules that can't cleanly map keep hardcoded lists as fallback alongside ability checks. | ✓ |
| Targeted refactor | Only refactor 5-6 rules that map cleanly to AbilityCached properties. Leave the rest hardcoded. | |
| You decide | Claude determines which rules benefit from refactoring. | |

**User's choice:** Full refactor
**Notes:** User wants no rule relying ONLY on hero ID lists. Ability-first, hardcoded fallback for edge cases.

### Follow-up: Hybrid Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Ability-first, hardcoded fallback | Check ability properties first, fall back to curated hero list if no match. Gradually shrink fallback. | ✓ |
| Union of both | Trigger if EITHER ability properties OR hero list matches. Maximizes coverage but might over-recommend. | |
| Ability-only, drop edge cases | If can't express as ability property, rule doesn't fire. Cleaner but loses valid recs. | |

**User's choice:** Ability-first, hardcoded fallback

### Follow-up: Reasoning Specificity

| Option | Description | Selected |
|--------|-------------|----------|
| Name the ability | Rules engine resolves specific ability name from AbilityCached.dname. Matches CNTR-03 and system prompt directive. | ✓ |
| Generic ability type | Reference ability property only ('channeled abilities'). Simpler but less specific. | |

**User's choice:** Name the ability

---

## New Counter Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Core 5 | Eul's vs channeled, Lotus/Linken's vs single-target, BKB-pierce awareness, Dispel items vs debuffs, Hex/Root vs escapes. Hits 8+ ability-driven rules total. | ✓ |
| Aggressive 7 | Core 5 plus Aeon Disk vs burst combos and Blade Mail vs high-damage. Bigger scope. | |
| Minimal 3 | Just Eul's, Lotus/Linken's, BKB-pierce. Tight scope. | |

**User's choice:** Core 5

### Follow-up: BKB-pierce Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Warning annotation | BKB still recommended but reasoning notes which enemy abilities pierce it. Player decides. | ✓ |
| Suppress recommendation | Don't recommend BKB if primary threat pierces. Aggressive filtering. | |
| Downgrade priority | BKB drops from 'core' to 'situational'. Subtler signal. | |

**User's choice:** Warning annotation

---

## Ability Context for Claude

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-filtered | Only counter-relevant abilities (channeled, passive, BKB-pierce, dispellable). ~150 tokens. | ✓ |
| Full dump per enemy | All abilities for all enemies. ~500 tokens. Complete but noisy. | |
| Tiered: full for lane, filtered for others | Full for lane opponents, filtered for rest of team. | |

**User's choice:** Pre-filtered

### Follow-up: Section Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inline with opponents | Ability annotations under each opponent in existing Lane Opponents section. | ✓ |
| Separate ability section | New "Enemy Ability Threats" section. More structured but separated from hero context. | |

**User's choice:** Inline with opponents

---

## Threat Escalation

| Option | Description | Selected |
|--------|-------------|----------|
| Priority upgrade | Fed enemies: 'situational' -> 'core'. Behind enemies: 'core' -> 'situational'. Simple, predictable. | ✓ |
| Phase shift | Fed enemies cause counter-items to shift earlier in build. More aggressive. | |
| Claude-only escalation | Pass threat annotations to Claude, let it prioritize. Simpler but no deterministic escalation. | |

**User's choice:** Priority upgrade

### Follow-up: RuleResult Schema

| Option | Description | Selected |
|--------|-------------|----------|
| Add counter_target field | RuleResult gets `counter_target: str | None`. Structured data for tooltips, Claude context. | ✓ |
| Reasoning-only | Keep schema as-is. Ability name embedded in reasoning string only. | |

**User's choice:** Add counter_target field

---

## Claude's Discretion

- Ability-property mapping for non-obvious categories (escape heroes, spell spammers)
- Internal helper methods for ability querying
- Ultimate vs basic ability detection from ability data
- Fallback hero list sizing for hybrid rules
- Test fixture strategy

## Deferred Ideas

- Aeon Disk vs burst combos -- considered but deferred to keep scope at 5 new categories
- Blade Mail vs high-damage abilities -- deferred
- Frontend counter-item tooltips -- counter_target enables future display
- Full enemy team ability context -- relevant for Phase 23 Win Condition Framing
