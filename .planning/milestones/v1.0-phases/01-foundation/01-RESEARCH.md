# Phase 1: Foundation - Research

**Researched:** 2026-03-21
**Domain:** Full-stack scaffolding (React + Vite + Tailwind frontend, FastAPI + SQLAlchemy backend, Docker Compose, OpenDota API data seeding)
**Confidence:** HIGH

## Summary

Phase 1 is a greenfield scaffolding phase covering four requirement IDs: DRFT-01 (hero picker with search), DISP-06 (dark theme with spectral cyan accent), INFR-01 (Docker Compose two-container deployment), and INFR-03 (environment configuration via .env). The core technical challenge is standing up a full-stack application from scratch with Docker orchestration, database seeding from an external API, and a polished dark-themed UI with fuzzy search -- all wired end-to-end.

The frontend stack uses React 19.2, Vite 8.0, Tailwind CSS 4.2 (CSS-first configuration via `@tailwindcss/vite`), Zustand 5.0 for state, and Fuse.js 7.1 for fuzzy hero search. The backend stack uses Python 3.12+ with FastAPI 0.135, SQLAlchemy 2.0 (async), and SQLite with aiosqlite. All versions verified against npm/pip registries on 2026-03-21.

**Primary recommendation:** Build frontend and backend as independent Docker services from day one. Use Nginx in the frontend container to both serve the SPA and reverse-proxy `/api/` requests to the backend container, eliminating CORS issues entirely.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Hero Picker UX:** Fuzzy search with real-time filtering -- type "am" matches "Anti-Mage", "jug" matches "Juggernaut". Filter as you type, no submit button. Small portrait (~40px) + hero name + colored attribute dot (str/agi/int/uni) in search results. Heroes already picked in other slots greyed out and moved to bottom. Your hero slot is larger/prominent at top of sidebar.
- **Data Seeding:** Auto-seed on first backend startup if DB is empty -- zero manual steps. Use OpenDota `/constants/heroes` + `/constants/items` for bulk data (no rate limits). Batch matchup data fetches with 1-second delays (60 req/min free tier). Default to "high" bracket (Legend+) for matchup data.
- **Visual Foundation:** Font: Inter for body text, JetBrains Mono for stats/numbers/gold costs. Favicon: SVG prism/diamond icon using spectral cyan (#00d4ff) gradient. Background: #0f1419 (near-black with cool undertone). Layout: Fixed sidebar (320px) + scrollable main panel.

### Claude's Discretion
- Exact fuzzy search algorithm (fuse.js or custom)
- Docker multi-stage build configuration details
- SQLAlchemy session management pattern
- Vite/Tailwind configuration specifics (use Tailwind v4 CSS-first config per research)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DRFT-01 | User can search and select their hero from a searchable dropdown with hero portraits | Fuse.js 7.1 for fuzzy search, OpenDota `/constants/heroes` API for hero data, Steam CDN URL pattern verified for hero portraits |
| DISP-06 | Dark theme with spectral cyan (#00d4ff) primary, Radiant teal (#6aff97), Dire red (#ff5555) | Tailwind v4 CSS-first @theme directive with OKLCH color values computed, Inter + JetBrains Mono font setup via fontsource |
| INFR-01 | Docker Compose deploys two containers: frontend (Nginx, port 8421) and backend (FastAPI, port 8420) | Multi-stage Dockerfiles researched for both containers, Nginx reverse proxy pattern for API routing |
| INFR-03 | Environment variable configuration via .env file (ANTHROPIC_API_KEY required, API keys optional) | FastAPI config pattern with pydantic-settings, Docker Compose env_file integration |

</phase_requirements>

## Standard Stack

### Core -- Frontend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.4 | UI framework | Latest stable, full concurrent features |
| react-dom | 19.2.4 | DOM rendering | Paired with React 19 |
| vite | 8.0.1 | Build tool / dev server | Fastest DX, native ESM, Tailwind v4 plugin support |
| @vitejs/plugin-react-swc | 4.3.0 | React Fast Refresh via SWC | 10x faster than Babel transforms |
| tailwindcss | 4.2.2 | Utility-first CSS | CSS-first config in v4, no JS config file needed |
| @tailwindcss/vite | 4.2.2 | Tailwind Vite plugin | Replaces PostCSS setup, faster builds |
| zustand | 5.0.12 | State management | Minimal API, TypeScript-first, no providers |
| fuse.js | 7.1.0 | Fuzzy search | Lightweight (5KB), zero dependencies, proven for hero name matching |
| typescript | 5.9.3 | Type safety | Strict mode, latest features |

### Core -- Backend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 | Web framework | Async-native, auto-generated API docs, Pydantic integration |
| uvicorn | 0.42.0 | ASGI server | Production-grade, works in Docker |
| sqlalchemy | 2.0.48 | ORM | Async support, type-safe queries, mature ecosystem |
| aiosqlite | 0.22.1 | Async SQLite driver | Required for SQLAlchemy async + SQLite |
| pydantic | 2.12.5 | Data validation | FastAPI's native validation, request/response schemas |
| httpx | 0.28.1 | HTTP client | Async support for OpenDota API calls |
| anthropic | 0.86.0 | Claude API SDK | Official SDK (not used in Phase 1 but installed for later phases) |

### Supporting -- Frontend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fontsource/inter | 5.2.8 | Inter font files | Self-hosted fonts, no external requests |
| @fontsource/jetbrains-mono | 5.2.8 | JetBrains Mono font files | Stats/numbers/gold costs display |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fuse.js | Custom filter with `String.includes()` | Fuse.js handles typos, abbreviations, and weighted multi-field search -- custom code would miss "jug" -> "Juggernaut" fuzzy matches. Use fuse.js. |
| @fontsource packages | Google Fonts CDN links | Fontsource is self-hosted (no external dependency), better for Docker/offline. Use fontsource. |
| aiosqlite | synchronous sqlite3 | Async is required for FastAPI async endpoints. Sync would block the event loop. Use aiosqlite. |

**Installation -- Frontend:**
```bash
npm create vite@latest prismlab-frontend -- --template react-swc-ts
cd prismlab-frontend
npm install tailwindcss @tailwindcss/vite zustand fuse.js @fontsource/inter @fontsource/jetbrains-mono
```

**Installation -- Backend:**
```bash
pip install fastapi[standard] uvicorn sqlalchemy aiosqlite pydantic httpx anthropic python-dotenv
```

**Version verification:** All versions verified via `npm view <pkg> version` and `pip index versions <pkg>` on 2026-03-21.

## Architecture Patterns

### Recommended Project Structure
```
prismlab/
├── docker-compose.yml
├── .env.example
├── .env                          # Gitignored
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app entry + lifespan for auto-seed
│   ├── config.py                 # pydantic-settings based config
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── heroes.py         # GET /api/heroes, GET /api/heroes/{id}
│   │       └── items.py          # GET /api/items, GET /api/items/{id}
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy ORM models (Hero, Item)
│   │   ├── database.py           # Async engine + session factory
│   │   ├── seed.py               # Auto-seed from OpenDota on first startup
│   │   └── opendota_client.py    # httpx wrapper for OpenDota API
│   └── tests/
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                # SPA routing + API proxy
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html                # Favicon link
│   ├── public/
│   │   └── favicon.svg           # Prism/diamond SVG icon
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts         # fetch wrapper for /api/* endpoints
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── MainPanel.tsx
│   │   │   └── draft/
│   │   │       ├── HeroPicker.tsx
│   │   │       └── HeroPortrait.tsx
│   │   ├── hooks/
│   │   │   └── useHeroes.ts
│   │   ├── stores/
│   │   │   └── gameStore.ts      # Zustand store (minimal for Phase 1)
│   │   ├── types/
│   │   │   ├── hero.ts
│   │   │   └── item.ts
│   │   ├── utils/
│   │   │   ├── heroSearch.ts     # Fuse.js config + search function
│   │   │   ├── imageUrls.ts      # Steam CDN URL builders
│   │   │   └── constants.ts
│   │   └── styles/
│   │       └── globals.css       # Tailwind @import + @theme block
│   └── tests/
│       └── components/
│           └── HeroPicker.test.tsx
│
└── data/                         # Docker volume mount for SQLite DB
    └── .gitkeep
```

### Pattern 1: Tailwind v4 CSS-First Theme Configuration

**What:** Define all custom colors and fonts in CSS using `@theme` directive instead of a JS config file.
**When to use:** Every Tailwind v4 project. No `tailwind.config.js` needed.

```css
/* src/styles/globals.css */
@import "tailwindcss";

@theme {
  /* Custom colors - OKLCH for Tailwind v4 */
  --color-cyan-accent: oklch(80.4% 0.146 219.5);      /* #00d4ff spectral cyan */
  --color-radiant: oklch(89.5% 0.192 150.6);           /* #6aff97 Radiant teal */
  --color-dire: oklch(68.2% 0.206 24.4);               /* #ff5555 Dire red */
  --color-bg-primary: oklch(18.8% 0.013 248.5);        /* #0f1419 main background */
  --color-bg-secondary: oklch(23.3% 0.022 272.8);      /* #1a1d28 sidebar/cards */
  --color-bg-elevated: oklch(27% 0.02 260);             /* Slightly lighter for hover states */

  /* Attribute colors */
  --color-attr-str: oklch(68% 0.19 25);                 /* Red for Strength */
  --color-attr-agi: oklch(75% 0.18 145);                /* Green for Agility */
  --color-attr-int: oklch(70% 0.15 250);                /* Blue for Intelligence */
  --color-attr-all: oklch(80% 0.1 90);                  /* Gold for Universal */

  /* Fonts */
  --font-body: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-stats: "JetBrains Mono", ui-monospace, monospace;
}
```

Then use in markup: `class="bg-bg-primary text-cyan-accent font-stats"`

### Pattern 2: Async SQLAlchemy Session Management

**What:** AsyncSession factory with FastAPI dependency injection.
**When to use:** Every database access in the backend.

```python
# data/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    "sqlite+aiosqlite:///./data/prismlab.db",
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

```python
# In route handlers
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/api/heroes")
async def list_heroes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hero).order_by(Hero.localized_name))
    return result.scalars().all()
```

### Pattern 3: FastAPI Lifespan for Auto-Seed

**What:** Use FastAPI's lifespan context manager to check DB and auto-seed on first startup.
**When to use:** Ensures zero-manual-step deployment.

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + seed if empty
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_if_empty()
    yield
    # Shutdown: cleanup

app = FastAPI(lifespan=lifespan)
```

### Pattern 4: Nginx Reverse Proxy in Frontend Container

**What:** Frontend Nginx serves the SPA and proxies `/api/` to the backend container.
**When to use:** Docker Compose deployments to avoid CORS entirely.

```nginx
# frontend/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing - all non-file requests go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend container
    location /api/ {
        proxy_pass http://prismlab-backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

This means the frontend calls `/api/heroes` with a simple relative URL -- no CORS, no environment-specific API URL configuration.

### Pattern 5: Zustand Store (Minimal Phase 1)

**What:** TypeScript-first Zustand store for hero selection state.
**When to use:** Phase 1 only needs hero selection; expanded in Phase 2.

```typescript
// stores/gameStore.ts
import { create } from 'zustand';
import type { Hero } from '../types/hero';

interface GameStore {
  selectedHero: Hero | null;
  selectHero: (hero: Hero) => void;
  clearHero: () => void;
}

export const useGameStore = create<GameStore>()((set) => ({
  selectedHero: null,
  selectHero: (hero) => set({ selectedHero: hero }),
  clearHero: () => set({ selectedHero: null }),
}));
```

### Anti-Patterns to Avoid

- **CORS middleware instead of Nginx proxy:** Adding `CORSMiddleware` to FastAPI works for dev but creates environment-specific config headaches. Use Nginx proxy for both dev and prod consistency. Only add CORS middleware as a fallback for direct backend access during development.
- **Synchronous SQLAlchemy with FastAPI:** Will block the event loop. Always use `async_sessionmaker` + `aiosqlite`.
- **`tailwind.config.js` with Tailwind v4:** The JS config file is deprecated. Use `@theme` in CSS.
- **Hardcoded CDN URLs in components:** Extract CDN URL builders into `utils/imageUrls.ts` so the pattern is consistent and changeable.
- **Seeding data on every startup:** Check if heroes table has rows first. Only seed when empty.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy text search | Custom substring matching with scoring | Fuse.js | Handles typos, abbreviations ("jug" -> "Juggernaut"), weighted multi-field search, threshold tuning. Tiny bundle (5KB). |
| CSS utility framework | Custom CSS variables + utility classes | Tailwind CSS v4 | 1000+ utilities, responsive design, dark mode, consistent design tokens |
| HTTP client (backend) | urllib3/requests wrapper | httpx | Native async/await, connection pooling, timeout handling, retry logic |
| Request validation | Manual dict parsing | Pydantic models | Auto-validation, serialization, API docs generation, error messages |
| SVG favicon | Complex hand-drawn SVG | Simple geometric prism shape | A diamond/prism shape is 5-10 lines of SVG. Don't over-engineer. |

**Key insight:** Phase 1 is scaffolding -- resist the urge to build anything clever. Use standard libraries, standard patterns, and get the skeleton working end-to-end first.

## Common Pitfalls

### Pitfall 1: OpenDota API Data Shape Mismatch
**What goes wrong:** The OpenDota `/constants/heroes` returns a **keyed object** (keys are hero IDs as strings), not an array. Same for `/constants/items` (keys are item internal names). Code that expects `response.json()` to be a list will break.
**Why it happens:** Most REST APIs return arrays for list endpoints. OpenDota is an exception.
**How to avoid:** Parse the response as a dict and iterate over `.values()` or `.items()`. Hero IDs are the dict keys.
**Warning signs:** `TypeError: list indices must be integers` or empty hero lists.

Verified hero data shape:
```python
# Response is: { "1": { "id": 1, "name": "npc_dota_hero_antimage", ... }, "2": { ... } }
heroes_data = response.json()
for hero_id, hero_info in heroes_data.items():
    # hero_id is a string like "1", hero_info is the full hero dict
```

Verified item data shape:
```python
# Response is: { "blink": { "id": 1, "dname": "Blink Dagger", "cost": 2250, ... }, ... }
items_data = response.json()
for internal_name, item_info in items_data.items():
    # internal_name is like "blink", item_info has "id", "dname", "cost", etc.
```

### Pitfall 2: Hero Image URL Construction
**What goes wrong:** Building CDN URLs with wrong hero name format. The `img` field from OpenDota contains the relative path with a query string (e.g., `/apps/dota2/images/dota_react/heroes/antimage.png?`). The `name` field has the `npc_dota_hero_` prefix.
**Why it happens:** Multiple name formats exist: `npc_dota_hero_antimage` (internal), `antimage` (CDN slug), `Anti-Mage` (display).
**How to avoid:** Extract the CDN slug from the `img` field, or strip the `npc_dota_hero_` prefix from the `name` field. Store the CDN slug in the database.
**Warning signs:** Broken images in the UI.

```typescript
// utils/imageUrls.ts
const HERO_CDN = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes';

export const heroImageUrl = (heroSlug: string) => `${HERO_CDN}/${heroSlug}.png`;
export const heroIconUrl = (heroSlug: string) => `${HERO_CDN}/icons/${heroSlug}.png`;

const ITEM_CDN = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items';

export const itemImageUrl = (itemSlug: string) => `${ITEM_CDN}/${itemSlug}.png`;
```

Verified: `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png` returns a valid PNG (61.4KB).

### Pitfall 3: SQLite WAL Mode on Docker Volumes
**What goes wrong:** SQLite WAL mode can fail or corrupt data on network-mounted filesystems (NFS, CIFS). Unraid typically uses NFS or Btrfs/XFS-backed shares.
**Why it happens:** WAL requires shared memory (mmap) between processes. Network filesystems don't support this.
**How to avoid:** Mount the SQLite data volume to a **local filesystem** in Docker (a bind mount to a local directory on the Unraid cache drive, not an NFS share). WAL mode works fine on Linux local filesystems, even across containers sharing the same Docker volume.
**Warning signs:** `database is locked` errors, silent data corruption.

```yaml
# docker-compose.yml -- use a local bind mount
volumes:
  - ./data:/app/data    # Must be on local filesystem, not NFS
```

### Pitfall 4: Tailwind v4 No JS Config File
**What goes wrong:** Creating a `tailwind.config.js` file and expecting it to work with Tailwind v4.
**Why it happens:** Muscle memory from Tailwind v3. All tutorials before Jan 2025 show JS config.
**How to avoid:** Use `@theme` directive in CSS. No `tailwind.config.js` file. No `@tailwind base/components/utilities` directives. Just `@import "tailwindcss"`.
**Warning signs:** Custom colors/fonts not working, "unknown at rule" warnings.

### Pitfall 5: Missing `check_same_thread` for SQLite
**What goes wrong:** SQLite raises `ProgrammingError: SQLite objects created in a thread can only be used in that same thread` in async contexts.
**Why it happens:** SQLite's default thread safety check conflicts with async connection pools.
**How to avoid:** Pass `connect_args={"check_same_thread": False}` to `create_async_engine`.
**Warning signs:** Intermittent `ProgrammingError` on database access.

### Pitfall 6: Vite Build Output in Docker
**What goes wrong:** The `npm run build` output directory is `dist/` but the Dockerfile copies from the wrong location, or the Nginx root points to the wrong path.
**Why it happens:** Different build tools use different output directories.
**How to avoid:** Verify `vite build` outputs to `dist/`. In the Dockerfile, `COPY --from=build /app/dist /usr/share/nginx/html`.
**Warning signs:** Nginx serves 404 for all routes.

## Code Examples

### OpenDota Data Seeding

```python
# data/opendota_client.py
import httpx

OPENDOTA_BASE = "https://api.opendota.com/api"

class OpenDotaClient:
    def __init__(self, api_key: str | None = None):
        self.params = {"api_key": api_key} if api_key else {}

    async def fetch_heroes(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENDOTA_BASE}/constants/heroes",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()  # Returns dict keyed by hero ID strings

    async def fetch_items(self) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENDOTA_BASE}/constants/items",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()  # Returns dict keyed by item internal names
```

```python
# data/seed.py
from sqlalchemy import select, func

async def seed_if_empty():
    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(Hero))
        if count and count > 0:
            return  # Already seeded

        client = OpenDotaClient(api_key=settings.opendota_api_key)
        heroes_data = await client.fetch_heroes()

        for hero_id_str, info in heroes_data.items():
            # Extract CDN slug from internal name
            slug = info["name"].replace("npc_dota_hero_", "")
            hero = Hero(
                id=info["id"],
                name=info["name"],
                localized_name=info["localized_name"],
                internal_name=info["name"],
                primary_attr=info["primary_attr"],
                attack_type=info["attack_type"],
                roles=info.get("roles", []),
                base_health=info.get("base_health", 120),
                base_mana=info.get("base_mana", 75),
                base_armor=info.get("base_armor", 0),
                base_attack_min=info.get("base_attack_min", 0),
                base_attack_max=info.get("base_attack_max", 0),
                base_str=info.get("base_str", 0),
                base_agi=info.get("base_agi", 0),
                base_int=info.get("base_int", 0),
                str_gain=info.get("str_gain", 0),
                agi_gain=info.get("agi_gain", 0),
                int_gain=info.get("int_gain", 0),
                attack_range=info.get("attack_range", 150),
                move_speed=info.get("move_speed", 300),
                img_url=f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{slug}.png",
                icon_url=f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/icons/{slug}.png",
            )
            session.add(hero)

        # Similar loop for items...
        await session.commit()
```

### Fuse.js Hero Search Configuration

```typescript
// utils/heroSearch.ts
import Fuse from 'fuse.js';
import type { Hero } from '../types/hero';

const fuseOptions: Fuse.IFuseOptions<Hero> = {
  keys: [
    { name: 'localized_name', weight: 2 },   // "Anti-Mage" - highest priority
    { name: 'roles', weight: 0.5 },           // "Carry", "Escape"
  ],
  threshold: 0.4,        // 0 = exact, 1 = match anything. 0.4 catches typos.
  distance: 100,          // How far from expected position characters can be
  minMatchCharLength: 2,  // Don't match single characters
};

export function createHeroSearcher(heroes: Hero[]): Fuse<Hero> {
  return new Fuse(heroes, fuseOptions);
}

export function searchHeroes(fuse: Fuse<Hero>, query: string): Hero[] {
  if (!query.trim()) return [];
  return fuse.search(query).map(result => result.item);
}
```

### Multi-Stage Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
services:
  prismlab-backend:
    build: ./backend
    container_name: prismlab-backend
    restart: unless-stopped
    ports:
      - "8420:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/prismlab.db
    volumes:
      - ./data:/app/data
    networks:
      - prismlab-net

  prismlab-frontend:
    build: ./frontend
    container_name: prismlab-frontend
    restart: unless-stopped
    ports:
      - "8421:80"
    depends_on:
      - prismlab-backend
    networks:
      - prismlab-net

networks:
  prismlab-net:
    driver: bridge
```

### SVG Favicon

```svg
<!-- public/favicon.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <defs>
    <linearGradient id="prism" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00d4ff" />
      <stop offset="50%" stop-color="#6aff97" />
      <stop offset="100%" stop-color="#00d4ff" />
    </linearGradient>
  </defs>
  <path d="M16 2 L28 26 L4 26 Z" fill="none" stroke="url(#prism)" stroke-width="2" />
  <path d="M16 8 L22 22 L10 22 Z" fill="url(#prism)" opacity="0.3" />
</svg>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind JS config (`tailwind.config.js`) | CSS-first config (`@theme` in CSS) | Tailwind v4, Jan 2025 | No JS config file needed. All theme customization in CSS. |
| PostCSS plugin for Tailwind | `@tailwindcss/vite` plugin | Tailwind v4, Jan 2025 | Direct Vite integration. Up to 100x faster incremental builds. |
| `@tailwind base/components/utilities` | `@import "tailwindcss"` | Tailwind v4, Jan 2025 | Single import replaces three directives. |
| React 18 `createRoot` | React 19 (same API, new features) | React 19, Dec 2024 | No breaking changes for this use case. Concurrent features available. |
| Vite 5/6 | Vite 8.0 | Vite 8, 2026 | Performance improvements, better plugin API. |
| `tiangolo/uvicorn-gunicorn-fastapi` Docker image | Build from `python:3.12-slim` | FastAPI docs, 2024+ | Official Docker image deprecated. Build from scratch recommended. |
| SQLAlchemy 1.x `session.query()` | SQLAlchemy 2.0 `select()` statements | SQLAlchemy 2.0, 2023 | Type-safe queries, async native. Do NOT use legacy query API. |

**Deprecated/outdated:**
- `tailwind.config.js` -- replaced by CSS-first `@theme` in Tailwind v4
- `@tailwind base; @tailwind components; @tailwind utilities;` -- replaced by `@import "tailwindcss";`
- `tiangolo/uvicorn-gunicorn-fastapi` Docker image -- deprecated by FastAPI docs
- `declarative_base()` function -- replaced by `class Base(DeclarativeBase): pass` in SQLAlchemy 2.0

## Open Questions

1. **OpenDota item data completeness**
   - What we know: The `/constants/items` endpoint returns items keyed by internal name with fields like `id`, `dname`, `cost`, `components`, `img`. The `qual` field distinguishes item quality.
   - What's unclear: Which items should be excluded from seeding? There are recipe items, unfinished/deprecated items, and Roshan items in the data. Need filtering logic.
   - Recommendation: Seed all items but add an `is_relevant` flag. Filter in queries, not in seeding. Items with `cost: null` or `cost: 0` and non-recipe items can be flagged as irrelevant.

2. **Matchup data seeding scope for Phase 1**
   - What we know: The CONTEXT.md mentions seeding matchup data with 1-second delays. The blueprint's MatchupData model exists.
   - What's unclear: Phase 1 success criteria don't mention matchup data. It's needed for Phase 3 (recommendation engine).
   - Recommendation: Create the MatchupData table schema in Phase 1 but defer seeding to Phase 3. Keep the seeding scope to heroes + items only for Phase 1.

3. **Vite 8 template compatibility**
   - What we know: `npm create vite@latest` with Vite 8 uses the `react-swc-ts` template. React 19 is the default.
   - What's unclear: Whether the Vite 8 template auto-includes React 19 or React 18.
   - Recommendation: Verify after scaffolding. If React 18 is included, upgrade `react` and `react-dom` to 19.2.4.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework (Frontend) | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Framework (Backend) | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file (Frontend) | `vite.config.ts` (Vitest uses Vite config) -- Wave 0 |
| Config file (Backend) | `pytest.ini` or `pyproject.toml` -- Wave 0 |
| Quick run (Frontend) | `npx vitest run --reporter=verbose` |
| Quick run (Backend) | `pytest tests/ -x -q` |
| Full suite | `docker compose exec prismlab-backend pytest && docker compose exec prismlab-frontend npx vitest run` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DRFT-01 | Hero search returns fuzzy matches | unit | `npx vitest run src/utils/heroSearch.test.ts` | Wave 0 |
| DRFT-01 | HeroPicker renders search results with portraits | component | `npx vitest run src/components/draft/HeroPicker.test.tsx` | Wave 0 |
| DISP-06 | Dark theme CSS variables are defined | manual-only | Visual inspection (CSS custom properties in @theme) | N/A |
| INFR-01 | Docker Compose starts both containers | smoke | `docker compose up -d && curl -f http://localhost:8421 && curl -f http://localhost:8420/api/heroes` | Wave 0 (script) |
| INFR-01 | API proxy routes /api/ to backend | integration | `curl -f http://localhost:8421/api/heroes` | Wave 0 (script) |
| INFR-03 | Backend reads env vars from .env | unit | `pytest tests/test_config.py -x` | Wave 0 |
| N/A | Hero API returns seeded data | integration | `pytest tests/test_api.py::test_list_heroes -x` | Wave 0 |
| N/A | Item API returns seeded data | integration | `pytest tests/test_api.py::test_list_items -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `npx vitest run` (frontend) / `pytest tests/ -x -q` (backend)
- **Per wave merge:** Full suite + Docker smoke test
- **Phase gate:** All tests green + Docker Compose smoke test passes

### Wave 0 Gaps
- [ ] `frontend/vitest.config.ts` or test config in `vite.config.ts` -- Vitest setup with jsdom/happy-dom
- [ ] `frontend/src/utils/heroSearch.test.ts` -- covers DRFT-01 fuzzy search
- [ ] `frontend/src/components/draft/HeroPicker.test.tsx` -- covers DRFT-01 component
- [ ] `backend/tests/test_api.py` -- covers hero/item API endpoints
- [ ] `backend/tests/test_config.py` -- covers INFR-03 env var loading
- [ ] `backend/tests/conftest.py` -- shared fixtures (test DB, async session)
- [ ] `scripts/smoke-test.sh` -- Docker Compose smoke test script
- [ ] Frontend test deps: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`
- [ ] Backend test deps: `pip install pytest pytest-asyncio httpx` (httpx for FastAPI TestClient async)

## Sources

### Primary (HIGH confidence)
- OpenDota `/constants/heroes` API -- live fetch verified, hero object structure with all fields documented (id, name, localized_name, primary_attr, attack_type, roles, base stats, img, icon)
- OpenDota `/constants/items` API -- live fetch verified, item object structure documented (id, dname, cost, components, abilities, attrib, img)
- Steam CDN hero image URL -- verified `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png` returns valid 61.4KB PNG
- npm registry -- all frontend package versions verified via `npm view` on 2026-03-21
- pip registry -- all backend package versions verified via `pip index versions` on 2026-03-21
- [Tailwind CSS v4 installation docs](https://tailwindcss.com/docs) -- CSS-first setup with `@tailwindcss/vite`
- [Tailwind CSS theme variables docs](https://tailwindcss.com/docs/theme) -- `@theme` directive, OKLCH syntax, font/color namespaces
- [FastAPI Docker deployment docs](https://fastapi.tiangolo.com/deployment/docker/) -- official Dockerfile pattern, deprecated tiangolo base image

### Secondary (MEDIUM confidence)
- [FastAPI async SQLAlchemy session pattern](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e) -- verified pattern aligns with SQLAlchemy 2.0 docs
- [Vite multi-stage Docker build guide](https://dev.to/it-wibrc/guide-to-containerizing-a-modern-javascript-spa-vuevitereact-with-a-multi-stage-nginx-build-1lma) -- standard Nginx + SPA pattern
- OpenDota rate limits -- 60 req/min, 50K/month free tier (from [blog.opendota.com](https://blog.opendota.com/2018/04/17/changes-to-the-api/), 2018 but still current)
- SQLite WAL mode on Docker -- works on Linux local filesystems, fails on NFS/CIFS (multiple sources including [SQLite forum](https://sqlite.org/forum/info/87824f1ed837cdbb))

### Tertiary (LOW confidence)
- OKLCH color conversions -- computed programmatically via sRGB->OKLAB->OKLCH pipeline. Values should be visually verified against hex originals in browser.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against live registries, APIs tested
- Architecture: HIGH -- patterns sourced from official docs (Tailwind, FastAPI, SQLAlchemy)
- Pitfalls: HIGH -- OpenDota data shape verified with live API call, SQLite WAL issues documented in official SQLite forum
- OKLCH colors: MEDIUM -- computed programmatically, should be visually verified

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable stack, 30-day validity)
