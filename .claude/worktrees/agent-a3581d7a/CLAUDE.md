# CLAUDE.md — Prismlab Project Instructions

## Project Overview
Prismlab is a Dota 2 adaptive item advisor. It helps players make better itemization decisions by analyzing their hero, role, playstyle, lane matchup, and evolving game state. It uses a hybrid recommendation engine: rule-based logic for fast/obvious decisions, Claude API for nuanced reasoning with natural language explanations.

## Read First
Before starting ANY implementation work, read `PRISMLAB_BLUEPRINT.md` in this directory. It contains the complete project spec including:
- Tech stack decisions
- Full project structure with every file mapped out
- Data models (Hero, Item, MatchupData, GameState)
- API endpoint specifications with request/response schemas
- Claude system prompt skeleton for the reasoning engine
- Playstyle taxonomy by role (Pos 1-5)
- UI layout wireframe and design direction
- Docker Compose configuration
- Implementation phases (follow these in order)

## Tech Stack
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + Zustand (state)
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **AI Engine:** Claude API (Sonnet) for item reasoning
- **Data Sources:** OpenDota API, Stratz API
- **Deployment:** Docker Compose (two containers: frontend Nginx + backend FastAPI)

## Implementation Order
Follow the phases in the blueprint strictly:
1. **Phase 1:** Project scaffolding, Docker, DB models, OpenDota client, hero picker
2. **Phase 2:** All draft-phase UI components (role, playstyle, side, lane, opponents)
3. **Phase 3:** Recommendation engine (rules layer + Claude API + hybrid orchestrator)
4. **Phase 4:** Item timeline UI and end-to-end flow
5. **Phase 5:** Mid-game adaptation (lane result, damage profile, enemy items, re-evaluate)
6. **Phase 6:** Polish, data pipeline, error handling

## Critical Requirements
- **ALWAYS include a favicon** — Missing favicons is unacceptable. Use a prism/refraction themed icon.
- **Hero/item images** come from Steam CDN, NOT self-hosted. See blueprint for URL patterns.
- **The Claude system prompt is the heart of this app.** The reasoning must sound like an 8K+ MMR coach — direct, specific, referencing actual hero abilities and matchup dynamics. Never generic advice.
- **Hybrid engine architecture:** Rules fire first (instant, no API call) for obvious stuff. Claude API fires for reasoning/explanations and edge cases. Always have a fallback if the LLM call fails or times out.
- **Structured JSON output** from Claude API — parse and validate before returning to frontend.
- **Dark theme** with spectral cyan (#00d4ff) primary accent, Radiant teal (#6aff97), Dire red (#ff5555).
- **Desktop-first layout:** Left sidebar for inputs, right main panel for item timeline recommendations.

## Code Style
- Frontend: TypeScript strict mode, functional components, hooks
- Backend: Type hints throughout, async endpoints, Pydantic models for request/response validation
- Use meaningful variable names that reference Dota concepts clearly

## Project Structure
All code lives under `prismlab/` subdirectory:
- `prismlab/backend/` — FastAPI app
- `prismlab/frontend/` — React + Vite app
- `prismlab/docker-compose.yml` — Container orchestration
- `prismlab/.env.example` — Environment variable template

## Data Flow
1. User selects hero, role, playstyle, side, lane, opponents in the UI
2. Frontend sends POST to `/api/recommend` with full game state
3. Backend's hybrid engine:
   a. Rules layer checks for obvious recommendations (Magic Stick vs spell-spammers, etc.)
   b. Context builder assembles hero stats, matchup data, and game state into a prompt
   c. Claude API generates reasoned recommendations in structured JSON
   d. Response is validated and returned to frontend
4. Frontend renders item timeline with phase cards and reasoning tooltips
5. User can update game state mid-game and hit "Re-Evaluate" to refresh recommendations

## Environment Setup
Copy `.env.example` to `.env` and fill in:
- `ANTHROPIC_API_KEY` (required)
- `OPENDOTA_API_KEY` (optional, for higher rate limits)
- `STRATZ_API_TOKEN` (optional, for Stratz data)

## Deployment Target
Docker Compose on Unraid server. Backend on port 8420, frontend on port 8421.
Will be reverse-proxied via Cloudflare Tunnel or Nginx Proxy Manager.

## V1 Scope Boundaries
- V1 focuses on "win your lane" — your hero + lane opponent(s) only
- NO allied team heroes in V1 (that's V2)
- NO neutral items in V1 (that's V2)
- NO GSI/live game data integration in V1 (that's V2)
- Desktop browser only — don't break on mobile but don't optimize for it
