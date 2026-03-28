# Phase 26: Engine Optimization - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce recommendation latency and API cost through a 3-mode engine architecture (Fast/Auto/Deep), local LLM integration via Ollama, and smart routing that uses the right tool for each request.

</domain>

<decisions>
## Implementation Decisions

### LLM Strategy — 3-Mode Architecture
- **D-01:** Implement three recommendation modes selectable by the user:
  - **Fast** — Rules engine only. Instant (<1s). Zero API cost. No natural language reasoning.
  - **Auto** — Smart routing: Ollama local LLM primary, Claude API fallback for edge cases. Target <5s. Minimal cost.
  - **Deep** — Always Claude API with full reasoning. Target <15s. Full cost.
- **D-02:** Default mode: **Auto**. User can change in Settings panel.
- **D-03:** Auto mode routing logic: rules fire first, then Ollama generates reasoning. If rules produce 8+ confident items AND matchup is straightforward, Ollama handles it. If matchup is complex (unusual hero combos, <3 items from rules), escalate to Claude API.
- **D-04:** Ollama model: fine-tune Llama 3.1 8B or Qwen 2.5 7B on Claude-generated training data. Deploy as quantized Q4_K_M on Unraid Ollama instance (already running, port 11434).

### Training Data Pipeline
- **D-05:** Generate training data by running Claude API across hero/role/matchup combinations systematically. Use the existing system prompt and context builder to produce input/output pairs.
- **D-06:** Target 5,000-10,000 training pairs covering all heroes, roles, and common matchups. Claude's discretion on exact generation strategy.

### Fast Path (Rules-Only Mode)
- **D-07:** In Fast mode, skip ALL LLM calls. Return rules engine output directly with no natural language reasoning (just item names, phases, and rule-based one-liners).
- **D-08:** Fast mode still returns full phase structure (starting, laning, core, late_game, situational) — rules populate all phases.

### Cost Controls
- **D-09:** Auto mode is the default — Claude API only fires for edge cases in Auto, or always in Deep mode.
- **D-10:** Add an API budget cap setting in the Settings panel (monthly dollar limit). Once reached, fall back to Ollama/rules for the rest of the month. Track cumulative usage.
- **D-11:** Display current month's API usage in Settings panel (approximate cost based on token counts).

### Target Latency
- **D-12:** Fast: <1 second
- **D-13:** Auto: <5 seconds (Ollama on Unraid hardware)
- **D-14:** Deep: <15 seconds (Claude API)

### Claude's Discretion
- Ollama API integration details (HTTP endpoint, model loading)
- Training data generation script design
- Fine-tuning approach (QLoRA, hyperparams)
- Confidence scoring for Auto mode routing
- Token counting / cost estimation implementation
- Response cache strategy per mode (different TTLs?)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Engine
- `prismlab/backend/engine/llm.py` — Current Claude API wrapper (Haiku 4.5, 5120 tokens, 30s timeout)
- `prismlab/backend/engine/recommender.py` — HybridRecommender orchestrator (rules → LLM → merge → validate)
- `prismlab/backend/engine/rules.py` — 23 deterministic rules, ability-first queries
- `prismlab/backend/engine/prompts/system_prompt.py` — System prompt (~2500 tokens)
- `prismlab/backend/engine/context_builder.py` — User message assembly
- `prismlab/backend/engine/schemas.py` — Request/response models

### Infrastructure
- `prismlab/backend/config.py` — Settings model (add mode selector, API budget)
- `prismlab/frontend/src/components/settings/SettingsPanel.tsx` — Settings UI (add mode + budget)
- Ollama instance: `http://100.78.161.13:11434` (already running on Unraid)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `HybridRecommender` already has rules → LLM → merge → fallback architecture — extend with mode routing
- `ResponseCache` with TTL — can vary TTL per mode
- `FallbackReason` enum — extend with "ollama_error" variant
- `LLMEngine.generate()` — create `OllamaEngine` with same interface

### Established Patterns
- Async httpx for API calls — Ollama uses HTTP REST (`/api/generate`)
- `Settings` pydantic model — add `recommendation_mode` and `api_budget_monthly` fields
- Fallback architecture: if primary fails, degrade gracefully

### Integration Points
- `HybridRecommender.recommend()` — add mode check at top, route to fast/auto/deep paths
- `LLMEngine` → create parallel `OllamaEngine` with same `generate()` signature
- Settings panel → new mode selector (3 radio buttons) + API budget input
- Frontend `useRecommendation.ts` → pass mode from settings to backend request

</code_context>

<specifics>
## Specific Ideas

- Auto mode should feel indistinguishable from Deep mode to the user — same UI, same phases, just faster
- Training data pipeline is a one-time script, not a recurring process (re-run on patch changes)
- Budget cap is a soft limit — warn at 80%, hard stop at 100%

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 26-engine-optimization*
*Context gathered: 2026-03-28*
