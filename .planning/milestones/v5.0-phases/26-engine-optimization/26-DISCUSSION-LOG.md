# Phase 26: Engine Optimization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 26-engine-optimization
**Areas discussed:** LLM strategy, Rule-only fast path, Target latency, Cost controls

---

## LLM Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Local Ollama model | Fine-tune small model, zero cost, sub-3s | |
| Keep Claude API | Current approach, best quality, 10-25s | |
| Hybrid: Ollama + Claude fallback | Local for 90%, Claude for edge cases | ✓ |
| Rules-only, no LLM | Expand rules, instant, loses reasoning | |

**User's choice:** Hybrid — Ollama primary, Claude fallback for edge cases.

---

## Rule-only Fast Path

| Option | Description | Selected |
|--------|-------------|----------|
| Never skip LLM | Always call LLM after rules | |
| Re-evaluations only | First build gets LLM, re-evals rules-only | |
| Simple matchups | Skip LLM when rules produce 8+ items | |
| User toggle | Settings mode selector | |

**User's choice:** 3-mode selector: **Fast** (rules-only), **Auto** (smart routing — Ollama + Claude for edge cases), **Deep** (always Claude API).

---

## Target Latency

| Option | Description | Selected |
|--------|-------------|----------|
| Fast <1s, Auto <5s, Deep <15s | Balanced targets | ✓ |
| Fast <1s, Auto <3s, Deep <30s | Tighter Auto, relaxed Deep | |
| Fast <1s, Auto <5s, Deep <30s | Relaxed across the board | |

**User's choice:** Fast <1s, Auto <5s, Deep <15s. Auto is the hybrid mode that uses both local and Claude depending on situation.

---

## Cost Controls

| Option | Description | Selected |
|--------|-------------|----------|
| Auto mode as default | Smart routing minimizes API calls naturally | ✓ (base) |
| Monthly API budget cap | Dollar limit, fallback when hit | ✓ (added) |
| Per-game cap | Max N Claude calls per game | |

**User's choice:** Auto as default (minimal cost), PLUS configurable monthly API budget cap in Settings.

---

## Claude's Discretion

- Ollama API integration details
- Training data generation strategy
- Fine-tuning approach
- Confidence scoring for Auto routing
- Token counting / cost estimation
- Per-mode cache TTLs

## Deferred Ideas

None
