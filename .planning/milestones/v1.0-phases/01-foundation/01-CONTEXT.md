# Phase 1: Foundation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the project scaffolding, Docker deployment, database with seeded hero/item data, the hero picker component, and the dark-themed visual foundation. After this phase, the app launches via Docker Compose, displays a polished dark UI, and lets the user search for and select a hero.

</domain>

<decisions>
## Implementation Decisions

### Hero Picker UX
- Fuzzy search with real-time filtering — type "am" matches "Anti-Mage", "jug" matches "Juggernaut". Filter as you type, no submit button
- Small portrait (~40px) + hero name + colored attribute dot (str/agi/int/uni) in search results
- Heroes already picked in other slots are greyed out and moved to bottom of list to prevent duplicates
- Your hero slot is larger/prominent at top of sidebar; team/opponent slots are compact rows (built in Phase 2)

### Data Seeding & API Integration
- Auto-seed on first backend startup if DB is empty — zero manual steps required
- Use OpenDota `/constants/heroes` + `/constants/items` for bulk data (no rate limits)
- Batch matchup data fetches with 1-second delays between requests (60 req/min free tier)
- Default to "high" bracket (Legend+) for matchup data — more relevant than all-bracket averages

### Visual Foundation
- Font: Inter for body text, JetBrains Mono for stats/numbers/gold costs
- Favicon: SVG prism/diamond icon using spectral cyan (#00d4ff) gradient
- Background: #0f1419 (near-black with cool undertone, makes cyan accent pop)
- Layout: Fixed sidebar (320px) + scrollable main panel. Sidebar stays visible while browsing recommendations

### Claude's Discretion
- Exact fuzzy search algorithm (fuse.js or custom)
- Docker multi-stage build configuration details
- SQLAlchemy session management pattern
- Vite/Tailwind configuration specifics (use Tailwind v4 CSS-first config per research)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code — greenfield project
- PRISMLAB_BLUEPRINT.md contains complete file structure, data models, and API route definitions

### Established Patterns
- Blueprint specifies: React + Vite + TypeScript + Tailwind CSS + Zustand frontend
- Blueprint specifies: Python + FastAPI + SQLAlchemy + SQLite backend
- Research updated versions: React 19, Vite 8, Tailwind v4, Python 3.13
- Research recommends TanStack Query for data fetching (not in blueprint)

### Integration Points
- Steam CDN for hero portraits: `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{name}.png`
- OpenDota constants API: `https://api.opendota.com/api/constants/heroes`, `/constants/items`
- Docker Compose: frontend on port 8421, backend on port 8420

</code_context>

<specifics>
## Specific Ideas

- Blueprint has complete data models (Hero, Item, MatchupData) ready to implement
- Blueprint has complete project file structure mapped out
- Research flagged: use `@tailwindcss/vite` instead of PostCSS for Tailwind v4
- Research flagged: SQLite WAL mode needs testing on Unraid Docker volumes (use cache drive, not array)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
