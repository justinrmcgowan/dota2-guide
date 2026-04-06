---
id: SEED-001
status: dormant
planted: 2026-04-06
planted_during: v7.0 Engine Hardening (Phase 38)
trigger_when: Tauri desktop app milestone (v8.0) or when adding RAG/knowledge-base enrichment
scope: Large
---

# SEED-001: In-Game Overlay & RAG Knowledge Base — Reference dota-ai-coach

## Why This Matters

The open-source project [BrightGir/dota-ai-coach](https://github.com/BrightGir/dota-ai-coach) (MIT licensed)
solves two problems Prismlab hasn't tackled yet:

1. **In-game overlay rendering** — They use RayLib + WinAPI transparency to render advice
   directly on top of the Dota 2 window. When Prismlab ships as a Tauri desktop app (v8.0),
   an overlay mode would let players see recommendations without alt-tabbing. Their hotkey
   system (F9 toggle, F10 focus) and "minimal disruption" design philosophy are worth studying.

2. **RAG knowledge base for Dota concepts** — They use BERT embeddings + ChromaDB to
   vectorize hero/item/ability knowledge, then retrieve relevant chunks before prompting
   the LLM. Prismlab currently packs context into structured Claude prompts directly.
   A RAG layer could handle edge cases and deep mechanic questions that don't fit in a
   single prompt window (e.g., "why is Radiance bad on Spectre this patch?").

Note: Their GSI integration patterns are NOT needed — Prismlab already shipped GSI in v2.0.

## When to Surface

**Trigger:** When starting the Tauri desktop app milestone (v8.0), or if a milestone
involves enriching the AI reasoning with a knowledge base / RAG pipeline.

This seed should be presented during `/gsd:new-milestone` when the milestone
scope matches any of these conditions:
- Tauri, desktop app, or native packaging work
- In-game overlay or always-on-top window features
- RAG, knowledge base, vector search, or embedding-based retrieval
- AI prompt enrichment beyond structured JSON context

## Scope Estimate

**Large** — A full milestone. The overlay requires Tauri window management research
(always-on-top, click-through transparency, hotkey registration). The RAG pipeline
requires embedding model selection, vector DB setup, knowledge chunking strategy,
and integration with the existing hybrid recommendation engine.

## Breadcrumbs

Related code and decisions found in the current codebase:

- `CLAUDE.md:80` — "NO GSI/live game data integration in V1 (that's V2)" (V2 shipped, but overlay is still open)
- `.planning/PROJECT.md:29-33` — V2 GSI features already shipped
- `.planning/ROADMAP.md:181` — "Package Prismlab as a native Windows desktop application using Tauri v2"
- `.planning/STATE.md` — "[v7.0]: Tauri Desktop App deferred to v8.0 — engine quality before distribution"
- `docs/superpowers/specs/2026-03-30-engine-hardening-design.md:320` — "No Tauri desktop packaging (deferred to after hardening)"
- `PRISMLAB_BLUEPRINT.md:702` — "GSI integration" listed as future (now done)
- `PRISMLAB_BLUEPRINT.md:708` — "Dota Plus-style real-time overlay (stretch goal — requires different architecture)"

## Notes

**dota-ai-coach architecture highlights worth studying:**
- `internal/ui/` — RayLib overlay with three panels: advice display, question input, context notes
- `internal/retriever/` — BERT-based vector search with 0.7 similarity threshold
- `internal/prompt/` — RAG pipeline: generate search queries → retrieve knowledge → construct final prompt
- `assets/` — Embedded knowledge base covering heroes, items, abilities (chunked for retrieval)
- `cmd/rag/` — Utilities for knowledge base management (loader, vectorizer, prompt debugger)
- Config uses 60s auto-advice interval with pause-after-user-question — good UX pattern

**Key difference from Prismlab:** dota-ai-coach uses Gemini/OpenRouter with RAG for general
tactical advice. Prismlab uses Claude with structured JSON output for specific item recommendations.
These are complementary approaches — Prismlab could adopt RAG for the "why" explanations
while keeping structured output for the "what to buy" decisions.
