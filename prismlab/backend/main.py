import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data.database import engine, Base
from data.seed import seed_if_empty
from data.refresh import refresh_all_data
from api.routes.heroes import router as heroes_router
from api.routes.items import router as items_router
from api.routes.recommend import router as recommend_router
from api.routes.admin import router as admin_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables, seed data, and start daily refresh scheduler."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_if_empty()

    # Start daily data refresh scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_all_data,
        "interval",
        hours=24,
        id="daily_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Daily data refresh scheduler started (24h interval).")

    yield

    scheduler.shutdown()
    logger.info("Daily data refresh scheduler shut down.")


app = FastAPI(title="Prismlab API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8421"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(heroes_router, prefix="/api")
app.include_router(items_router, prefix="/api")
app.include_router(recommend_router, prefix="/api")
app.include_router(admin_router)
