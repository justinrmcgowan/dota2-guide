# Phase 28: Patch 7.41 Data Refresh - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 28-patch-data-refresh
**Areas discussed:** Data source strategy, Rules engine updates, System prompt updates, Validation approach

---

## Data Source Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Re-run OpenDota seed | Existing script fetches new data automatically | ✓ |
| Manual patch script | One-time migration for specific changes | |
| Re-seed + manual fixes | Bulk auto + targeted manual patches | |

**User's choice:** Re-run the existing seed. Cleanest approach.

---

## Rules Engine Updates

| Option | Description | Selected |
|--------|-------------|----------|
| Full audit of all 23 rules | Check every rule against 7.41 changes | ✓ |
| Targeted fixes only | Only fix broken references | |
| Skip rules — Claude adapts | Let Claude handle via catalog | |

**User's choice:** Full audit — comprehensive check of all rules.

---

## System Prompt Updates

| Option | Description | Selected |
|--------|-------------|----------|
| Keep patch-agnostic | Only fix factual errors | |
| Add 7.41 meta hints | Brief behavioral notes in prompt | ✓ |
| Separate patch notes section | Dynamic section in user message | |

**User's choice:** Add meta hints — brief notes about key behavioral changes (Refresher rework, Bloodstone aura, Shiva's cost).

---

## Validation Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Automated tests | Check new items exist, costs correct, rules clean | ✓ |
| Manual spot-check | Query DB manually after seed | |
| Both automated + manual | Tests + one end-to-end recommendation | |

**User's choice:** Automated tests in pytest suite. Repeatable for future patches.

---

## Claude's Discretion

- Re-seed procedure and error handling
- Which new items get new rules
- Meta hint wording
- Test fixture design

## Deferred Ideas

None
