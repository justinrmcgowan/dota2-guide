---
phase: 01-foundation
plan: 01
subsystem: api, database, infra
tags: [fastapi, sqlalchemy, sqlite, docker, opendota, pydantic, async]

# Dependency graph
requires: []
provides:
  - FastAPI backend with async SQLAlchemy and SQLite database
  - Hero and Item ORM models with all base stats
  - MatchupData schema (empty, ready for Phase 3)
  - OpenDota API client for fetching hero/item constants
  - Auto-seed logic populating DB from OpenDota on first startup
  - REST endpoints GET /api/heroes, GET /api/heroes/{id}, GET /api/items, GET /api/items/{id}
  - Docker Compose with backend (8420) and frontend placeholder (8421)
  - Pydantic Settings config reading from .env file
  - Backend test infrastructure with in-memory SQLite and ASGI transport
affects: [01-02, 01-03, 02-draft-ui, 03-recommendation-engine]

# Tech tracking
tech-stack:
  added: [fastapi 0.135.1, sqlalchemy 2.0.48, aiosqlite 0.22.1, pydantic 2.12.5, pydantic-settings 2.8.1, httpx 0.28.1, uvicorn 0.42.0, anthropic 0.86.0, pytest 9.0.2, pytest-asyncio 1.3.0]
  patterns: [async SQLAlchemy with DeclarativeBase, FastAPI lifespan for startup tasks, Pydantic response models with from_attributes, dependency injection via get_db]

key-files:
  created:
    - prismlab/backend/main.py
    - prismlab/backend/config.py
    - prismlab/backend/data/database.py
    - prismlab/backend/data/models.py
    - prismlab/backend/data/seed.py
    - prismlab/backend/data/opendota_client.py
    - prismlab/backend/api/routes/heroes.py
    - prismlab/backend/api/routes/items.py
    - prismlab/backend/tests/conftest.py
    - prismlab/backend/tests/test_api.py
    - prismlab/backend/tests/test_config.py
    - prismlab/docker-compose.yml
    - prismlab/.env.example
    - prismlab/backend/Dockerfile
    - prismlab/backend/requirements.txt
  modified: []

key-decisions:
  - "Used SQLAlchemy 2.0 Mapped/mapped_column syntax instead of legacy Column syntax for type safety"
  - "OpenDota keyed-object response iterated with .items() to avoid array assumption pitfall"
  - "Items without 'id' field skipped during seeding to handle malformed OpenDota data"
  - "Recipe detection via internal_name.startswith('recipe_'), neutral detection via qual=='rare'"

patterns-established:
  - "Async database pattern: async_sessionmaker with get_db dependency injection"
  - "Pydantic response models with model_config from_attributes=True for ORM-to-response conversion"
  - "FastAPI lifespan for startup tasks (table creation, auto-seeding)"
  - "Test pattern: in-memory SQLite, ASGI transport, dependency override for get_db"

requirements-completed: [INFR-01, INFR-03]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 01 Plan 01: Backend Foundation Summary

**FastAPI backend with async SQLAlchemy Hero/Item models, OpenDota auto-seeding, REST endpoints, Docker Compose, and 9-test suite**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T18:50:11Z
- **Completed:** 2026-03-21T18:53:48Z
- **Tasks:** 2
- **Files modified:** 22

## Accomplishments
- Complete FastAPI backend scaffolding with async SQLAlchemy 2.0, SQLite database, and Pydantic config
- Hero, Item, and MatchupData ORM models with full base stats matching OpenDota API shape
- OpenDota async client + auto-seed logic that populates DB on first startup with correct keyed-object parsing
- REST endpoints for heroes (list/detail) and items (list/detail) with Pydantic response validation
- Docker Compose defining both containers (backend 8420, frontend placeholder 8421)
- 9 passing tests covering health check, hero CRUD, item CRUD, and config loading

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend scaffolding with FastAPI, SQLAlchemy models, database, config, and Docker Compose** - `8b5221c` (feat)
2. **Task 2: OpenDota client, auto-seed logic, and backend tests** - `5b588af` (feat)

## Files Created/Modified
- `prismlab/backend/main.py` - FastAPI app entry with lifespan auto-seed, CORS, health endpoint
- `prismlab/backend/config.py` - Pydantic Settings reading ANTHROPIC_API_KEY, OPENDOTA_API_KEY from .env
- `prismlab/backend/data/database.py` - Async SQLAlchemy engine, session factory, get_db dependency
- `prismlab/backend/data/models.py` - Hero, Item, MatchupData ORM models with all stats
- `prismlab/backend/data/seed.py` - Auto-seed from OpenDota API on first startup
- `prismlab/backend/data/opendota_client.py` - Async httpx client for OpenDota constants API
- `prismlab/backend/api/routes/heroes.py` - GET /api/heroes, GET /api/heroes/{id}
- `prismlab/backend/api/routes/items.py` - GET /api/items, GET /api/items/{id}
- `prismlab/backend/tests/conftest.py` - Test fixtures with in-memory SQLite and ASGI transport
- `prismlab/backend/tests/test_api.py` - 7 API tests (health, hero list/detail/404, item list/detail/404)
- `prismlab/backend/tests/test_config.py` - 2 config tests (defaults, custom values)
- `prismlab/docker-compose.yml` - Two-container orchestration (backend + frontend placeholder)
- `prismlab/.env.example` - Environment variable template
- `prismlab/backend/Dockerfile` - Python 3.12-slim container
- `prismlab/backend/requirements.txt` - Pinned dependency versions
- `prismlab/data/.gitkeep` - Persistent data volume mount point
- `.gitignore` - Python, SQLite, Node, IDE exclusions

## Decisions Made
- Used SQLAlchemy 2.0 Mapped/mapped_column syntax for type safety over legacy Column syntax
- OpenDota keyed-object response iterated with .items() to correctly handle dict-of-dicts format
- Items without 'id' field skipped during seeding to handle malformed OpenDota data gracefully
- Recipe detection via internal_name prefix, neutral detection via qual field
- pytest-asyncio 1.3.0 with async fixtures via @pytest_asyncio.fixture decorator

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added .gitignore for generated files**
- **Found during:** Task 2 (committing test files)
- **Issue:** __pycache__ directories and other generated files had no .gitignore, would be committed
- **Fix:** Created root .gitignore covering Python, SQLite, .env, Node, IDE files
- **Files modified:** .gitignore
- **Verification:** git status no longer shows __pycache__ as untracked
- **Committed in:** 5b588af (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for repository hygiene. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Backend auto-seeds from OpenDota public API on first startup.

## Next Phase Readiness
- Backend foundation complete, serving hero/item data via REST endpoints
- Ready for Plan 02 (frontend scaffolding) and Plan 03 (hero picker component)
- Docker Compose frontend service defined but will fail to build until Plan 02 creates the frontend

## Self-Check: PASSED

All 16 created files verified present on disk. Both task commits (8b5221c, 5b588af) verified in git log. 9/9 tests passing.

---
*Phase: 01-foundation*
*Completed: 2026-03-21*
