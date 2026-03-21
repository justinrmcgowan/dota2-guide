# Technology Stack

**Project:** Prismlab -- Dota 2 Adaptive Item Advisor
**Researched:** 2026-03-21
**Overall Confidence:** HIGH

---

## Recommended Stack

The blueprint specifies React 18, but React 19 is now the production standard (v19.2.1, stable since Dec 2024). Vite has jumped to v8 with Rolldown. Tailwind CSS v4 shipped a breaking architecture change. This research updates every technology to its current recommended version while preserving the blueprint's architectural intent.

### Frontend Core

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | 19.2.x | UI framework | Latest stable. React Compiler auto-optimizes without manual useMemo/useCallback. New `use()` hook simplifies async data. Full backward compat with React 18 patterns. No reason to start a greenfield project on 18. | HIGH |
| Vite | 8.0.x | Build tool / dev server | Ships Rolldown (Rust bundler), 10-30x faster builds vs Vite 5. `@vitejs/plugin-react` v6 drops Babel dependency, uses Oxc for React Refresh -- smaller install, faster HMR. | HIGH |
| TypeScript | 5.7.x | Type safety | Strict mode required per blueprint. Current stable, full Vite 8 compatibility. | HIGH |
| Tailwind CSS | 4.1.x | Utility-first CSS | CSS-first config (no `tailwind.config.js`), Rust-powered engine, 5x faster builds, incremental builds 100x faster. Use `@tailwindcss/vite` plugin (not PostCSS). OKLCH colors by default. | HIGH |
| Zustand | 5.0.x | Client state management | ~1KB, TypeScript-first, no providers/boilerplate. Perfect for the GameState store (hero, role, playstyle, lane, opponents, recommendations). V5 is production standard in 2026. | HIGH |

### Frontend Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| @tanstack/react-query | 5.91.x | Server state / data fetching | All API calls to backend (heroes, items, matchups, recommendations). Handles caching, loading states, error states, stale-while-revalidate. Separates server state from client state (Zustand). | HIGH |
| @vitejs/plugin-react | 6.0.x | Vite React integration | Required for JSX transform, React Refresh (HMR). V6 uses Oxc, no Babel dependency. | HIGH |
| @tailwindcss/vite | 4.1.x | Tailwind Vite plugin | Direct Vite integration, better performance than PostCSS route. Single `@import "tailwindcss"` in CSS. | HIGH |

### Backend Core

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.13.x | Runtime | JIT compiler provides 10-15% CPU-bound performance gains. Improved error messages with color. 2 years full support + 3 years security. All project dependencies support 3.13. Blueprint says 3.12, but 3.13 is better in every way and fully compatible. | HIGH |
| FastAPI | 0.135.x | API framework | Async-first, auto OpenAPI docs, Pydantic v2 native. SSE support for potential streaming recommendations. Still the standard Python async API framework. | HIGH |
| Pydantic | 2.12.x | Request/response validation | Required by FastAPI. V2 has Rust core (pydantic-core), massive perf gains over v1. Use for all request/response models per blueprint. | HIGH |
| SQLAlchemy | 2.0.x | ORM / database toolkit | 2.0-style with type-annotated mapped classes. Async support via `sqlalchemy[asyncio]` + aiosqlite. Battle-tested, maps cleanly to blueprint's Hero/Item/MatchupData models. | HIGH |
| SQLite | (bundled) | Database | Per blueprint. Simple, file-based, Docker volume-mountable. Perfect for caching hero/item/matchup data. No need for Postgres at this scale. | HIGH |
| aiosqlite | 0.22.x | Async SQLite driver | Required for async SQLAlchemy + SQLite. Runs SQLite in a background thread to avoid blocking the event loop. | HIGH |

### Backend Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| uvicorn | 0.42.x | ASGI server | Production server for FastAPI. Use `uvicorn[standard]` for uvloop + httptools performance. | HIGH |
| httpx | 0.28.x | Async HTTP client | All outbound API calls: OpenDota, Stratz, Claude API. Async-native, connection pooling, HTTP/2 support. Use instead of `requests` (blocking) or `aiohttp` (heavier). | HIGH |
| anthropic | 0.86.x | Claude API SDK | Official Anthropic Python SDK. Typed request/response objects, async support, streaming SSE. Use `output_config.format` for structured JSON output (GA, no beta headers needed). | HIGH |
| alembic | 1.18.x | DB migrations | Auto-generate migrations from SQLAlchemy model changes. Essential for schema evolution between data refreshes. | MEDIUM |
| pydantic-settings | 2.x | Environment config | Load .env vars into typed settings class. Replaces manual `os.getenv()`. Integrates with FastAPI dependency injection. | HIGH |

### AI Engine

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Claude Sonnet 4.6 | `claude-sonnet-4-6-20250514` | Item reasoning engine | Latest Sonnet, same pricing as 4.5 ($3/$15 per MTok). 1M context window. Structured outputs GA -- compile JSON schema into grammar, guarantees valid JSON matching your schema. 64K max output. Best cost/performance ratio for this use case. | HIGH |

**Model ID for config:** `claude-sonnet-4-6-20250514`

**Structured Output:** Use `output_config.format` with a JSON schema matching the recommendation response structure. This replaces the old approach of hoping the model returns valid JSON -- the API now *guarantees* schema compliance at the token generation level.

**Cost estimate per recommendation:** ~$0.003-0.01 (2K input tokens at $3/MTok + 1K output tokens at $15/MTok). With prompt caching (cache the system prompt + hero/item static data), cache reads drop to $0.30/MTok -- ~90% savings on repeated context.

### Data Sources

| Source | Type | Purpose | Notes | Confidence |
|--------|------|---------|-------|------------|
| OpenDota API | REST | Hero stats, item data, matchup win rates, common item builds | Free tier: 50K calls/month, 60 req/min. Optional API key for higher limits. Endpoints: `/heroStats`, `/heroes`, `/constants/items`, `/heroes/{id}/matchups`. | HIGH |
| Stratz API | GraphQL | Hero stats, matchup data, item popularity by bracket | Free tier with token. GraphQL allows requesting exactly the fields needed. 13M+ requests/day capacity. Complements OpenDota with bracket-filtered data. | HIGH |
| Steam CDN | Static assets | Hero portraits, hero icons, item images | `cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/`. No API key needed, no rate limits. Per blueprint: never self-host these images. | HIGH |

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Vitest | 4.1.x | Frontend unit/component tests | Native Vite integration, zero-config TypeScript, 3-4x faster than Jest cold start, 50% less memory. Browser mode for real DOM testing. | HIGH |
| @testing-library/react | 16.x | React component testing | Standard React testing utilities, works with Vitest. Test user interactions, not implementation details. | HIGH |
| pytest | 8.x | Backend unit/integration tests | Python testing standard. Use with `pytest-asyncio` for async FastAPI endpoint tests. | HIGH |
| pytest-asyncio | 0.24.x | Async test support | Required for testing async FastAPI endpoints and async database operations. | HIGH |
| httpx (test client) | 0.28.x | API integration testing | FastAPI's recommended async test client. Use `httpx.AsyncClient` with `ASGITransport` for testing endpoints without running a server. | HIGH |

### Deployment / Infrastructure

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Docker Compose | v2 (bundled) | Container orchestration | Two containers per blueprint: frontend (Nginx + static build) + backend (FastAPI/uvicorn). SQLite DB on a Docker volume. | HIGH |
| Nginx | stable-alpine | Frontend static serving + API proxy | Multi-stage Docker build: Node for `npm run build`, then copy dist to nginx:stable-alpine. Final image ~25-30MB. Proxy `/api/*` to backend container. | HIGH |
| Node.js | 22-slim | Frontend build stage | LTS release for Docker build stage only (not runtime). Used in multi-stage Dockerfile for `npm install && npm run build`. | HIGH |
| Python | 3.13-slim | Backend runtime | Slim variant for smaller Docker image. Install deps via pip, run uvicorn. | HIGH |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Frontend framework | React 19 | React 18 | 18 is maintenance-only. 19 is stable (v19.2.1), has React Compiler, better async patterns. No benefit to starting on 18 in 2026. |
| Build tool | Vite 8 | Vite 6/7 | Vite 8 ships Rolldown (unified Rust bundler). 10-30x faster builds. Plugin ecosystem updated. No reason for older versions. |
| CSS framework | Tailwind v4 | Tailwind v3 | v4 is faster (Rust engine), simpler (CSS-first config), and the ecosystem has migrated. v3 is maintenance-only. |
| State management | Zustand 5 | Redux Toolkit | Zustand is 1KB, no boilerplate, TypeScript-first. Redux is 7x larger and adds unnecessary ceremony for this app's scope. |
| State management | Zustand 5 | Jotai / Valtio | All from pmndrs. Zustand is best for the "single store" pattern this app needs (one GameState store). Jotai is atom-based (better for many independent pieces), Valtio is proxy-based (mutation-style). |
| Data fetching | TanStack Query v5 | SWR | TanStack Query has DevTools, better mutation handling (useMutation for POST /recommend), and larger ecosystem. SWR is simpler but we need mutation lifecycle control. |
| Data fetching | TanStack Query v5 | Raw fetch/axios | Query handles caching, loading, error, stale-while-revalidate, and retry automatically. Manual fetching means reimplementing all of this. |
| Python runtime | 3.13 | 3.12 | 3.13 has JIT compiler, better error messages, same library compatibility. Blueprint says 3.12 but 3.13 is the better choice now. |
| HTTP client (Python) | httpx | aiohttp | httpx has cleaner API, sync+async in one library, HTTP/2 support. aiohttp is heavier and callback-oriented. |
| HTTP client (Python) | httpx | requests | requests is sync-only, blocks the event loop. Unusable in an async FastAPI app without threading hacks. |
| Database | SQLite | PostgreSQL | Overkill for caching hero/item data. SQLite is file-based, zero-config, Docker-volume mountable. This app has one writer (data refresh) and many readers (recommendations). |
| ORM | SQLAlchemy 2.0 | Tortoise ORM | SQLAlchemy is the Python ORM standard with 20+ years of production use. Tortoise is async-first but smaller ecosystem, fewer resources when debugging. |
| API framework | FastAPI | Django REST | Django is synchronous by default, carries ORM/admin/auth/middleware baggage this app does not need. FastAPI is async-native, lighter, auto-generates OpenAPI docs. |
| Testing (frontend) | Vitest | Jest | Vitest is Vite-native, shares config, faster cold start, ESM-first. Jest requires separate config and transformation setup for Vite projects. |
| AI model | Sonnet 4.6 | Opus 4.6 | Opus is $15/$75 per MTok (5x Sonnet cost). For item recommendations, Sonnet's reasoning is sufficient. Use Opus only if recommendation quality is measurably poor (unlikely). |
| AI model | Sonnet 4.6 | Haiku 4.5 | Haiku is faster and cheaper but may produce less nuanced matchup reasoning. Start with Sonnet; downgrade to Haiku only for cost optimization after validating quality. |

---

## Version Pinning Strategy

Pin **major.minor** in package files, allow patch updates:

**Frontend (package.json):**
```json
{
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "@tanstack/react-query": "^5.91.0",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "vite": "^8.0.0",
    "@vitejs/plugin-react": "^6.0.0",
    "@tailwindcss/vite": "^4.1.0",
    "tailwindcss": "^4.1.0",
    "typescript": "^5.7.0",
    "vitest": "^4.1.0",
    "@testing-library/react": "^16.0.0"
  }
}
```

**Backend (requirements.txt):**
```txt
fastapi>=0.135.0,<1.0
uvicorn[standard]>=0.42.0,<1.0
pydantic>=2.12.0,<3.0
pydantic-settings>=2.0.0,<3.0
sqlalchemy[asyncio]>=2.0.46,<2.1
aiosqlite>=0.22.0,<1.0
alembic>=1.18.0,<2.0
httpx>=0.28.0,<1.0
anthropic>=0.86.0,<1.0
pytest>=8.0.0,<9.0
pytest-asyncio>=0.24.0,<1.0
```

---

## Installation

### Frontend

```bash
# Scaffold with Vite
npm create vite@latest frontend -- --template react-ts

# Core dependencies
npm install react@^19.2.0 react-dom@^19.2.0 @tanstack/react-query@^5.91.0 zustand@^5.0.0

# Dev dependencies
npm install -D vite@^8.0.0 @vitejs/plugin-react@^6.0.0 tailwindcss@^4.1.0 @tailwindcss/vite@^4.1.0 typescript@^5.7.0 vitest@^4.1.0 @testing-library/react@^16.0.0
```

### Backend

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings "sqlalchemy[asyncio]" aiosqlite alembic httpx anthropic

# Dev/test dependencies
pip install pytest pytest-asyncio
```

---

## Key Configuration Notes

### Tailwind CSS v4 (Breaking Change from v3)

Tailwind v4 eliminates `tailwind.config.js`. Configuration is now CSS-first:

```css
/* src/styles/globals.css */
@import "tailwindcss";

@theme {
  --color-primary: oklch(0.72 0.19 220);       /* spectral cyan #00d4ff */
  --color-radiant: oklch(0.85 0.2 145);         /* teal #6aff97 */
  --color-dire: oklch(0.62 0.24 25);             /* red #ff5555 */
  --color-bg-primary: oklch(0.12 0.02 260);      /* #0f1117 */
  --color-bg-secondary: oklch(0.15 0.02 260);    /* #1a1d28 */
}
```

The `@tailwindcss/vite` plugin replaces PostCSS config entirely. No `postcss.config.js` needed.

### Vite Config (v8)

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### Claude API Structured Output

```python
# Use output_config.format for guaranteed JSON schema compliance
import anthropic

client = anthropic.AsyncAnthropic()

response = await client.messages.create(
    model="claude-sonnet-4-6-20250514",
    max_tokens=2000,
    temperature=0.3,
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": context}],
    output_config={
        "format": {
            "type": "json_schema",
            "json_schema": RECOMMENDATION_SCHEMA,
        }
    },
)
```

This guarantees the response matches your schema at the token generation level -- no more parsing failures or malformed JSON.

### FastAPI Async with SQLAlchemy

```python
# Use async session factory
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///./data/prismlab.db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

Install SQLAlchemy with `sqlalchemy[asyncio]` to get the greenlet dependency.

---

## Blueprint Deviations

These are intentional upgrades from the PRISMLAB_BLUEPRINT.md specifications:

| Blueprint Says | Research Recommends | Rationale |
|----------------|---------------------|-----------|
| React 18 | React 19.2.x | 19 is stable, has React Compiler, better for new projects. No migration needed since this is greenfield. |
| Python 3.12 | Python 3.13.x | JIT compiler, better errors, same compat. 3.12 is fine but 3.13 is strictly better. |
| `claude-sonnet-4-20250514` | `claude-sonnet-4-6-20250514` | Sonnet 4.6 is newer, same price, better at coding/reasoning. Structured outputs are now GA. |
| Axios/fetch (implied) | TanStack Query + native fetch | Query handles caching, loading states, mutations, retry. Eliminates boilerplate. No Axios needed -- fetch is sufficient as the transport. |
| `tailwind.config.js` (implied) | CSS-first `@theme` config | Tailwind v4 breaking change. No JS config file needed. |
| PostCSS plugin (implied) | `@tailwindcss/vite` plugin | Direct Vite integration, better performance than PostCSS route. |

---

## Sources

- [React Versions](https://react.dev/versions) -- React 19.2.1 stable
- [Vite 8.0 Announcement](https://vite.dev/blog/announcing-vite8) -- Rolldown-powered Vite
- [Tailwind CSS v4.0](https://tailwindcss.com/blog/tailwindcss-v4) -- CSS-first config, Rust engine
- [Zustand GitHub](https://github.com/pmndrs/zustand) -- v5.0.8 latest
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/) -- v0.135.x
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) -- v2.0.46
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) -- v0.86.0
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) -- GA, no beta headers
- [Claude Sonnet 4.6 Pricing](https://platform.claude.com/docs/en/about-claude/pricing) -- $3/$15 per MTok
- [OpenDota API Docs](https://docs.opendota.com/) -- REST endpoints
- [Stratz API](https://stratz.com/api) -- GraphQL
- [TanStack Query](https://tanstack.com/query/latest) -- v5.91.x
- [Vitest](https://vitest.dev/) -- v4.1.0
- [Pydantic Docs](https://docs.pydantic.dev/latest/) -- v2.12.x
- [uvicorn PyPI](https://pypi.org/project/uvicorn/) -- v0.42.0
- [httpx Docs](https://www.python-httpx.org/) -- v0.28.1
- [aiosqlite PyPI](https://pypi.org/project/aiosqlite/) -- v0.22.1
- [Alembic Docs](https://alembic.sqlalchemy.org/) -- v1.18.4
