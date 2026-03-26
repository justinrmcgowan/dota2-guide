import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from data.database import engine, Base, async_session
from data.seed import seed_if_empty
from data.refresh import refresh_all_data
from api.routes.recommend import _rules
from api.routes.heroes import router as heroes_router
from api.routes.items import router as items_router
from api.routes.recommend import router as recommend_router
from api.routes.admin import router as admin_router
from api.routes.settings import router as settings_router
from api.routes.screenshot import router as screenshot_router
from gsi.receiver import router as gsi_router
from gsi.ws_manager import ws_manager
from gsi.state_manager import gsi_state_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables, seed data, and start daily refresh scheduler."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_if_empty()

    # Initialize rules engine lookups from DB
    async with async_session() as session:
        await _rules.init_lookups(session)
    logger.info("Rules engine lookups initialized from DB.")

    # Start data refresh scheduler — every 6h to catch patches same day
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_all_data,
        "interval",
        hours=6,
        id="data_refresh",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    logger.info("Data refresh scheduler started (6h interval).")

    # Start WebSocket broadcast loop (1Hz throttle)
    broadcast_task = asyncio.create_task(ws_manager.start_broadcast_loop(gsi_state_manager))
    logger.info("WebSocket broadcast loop started (1Hz throttle).")

    yield

    # Stop WebSocket broadcast loop
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    logger.info("WebSocket broadcast loop stopped.")

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
app.include_router(gsi_router)  # /gsi at root, no prefix
app.include_router(settings_router, prefix="/api")
app.include_router(screenshot_router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live game state updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; we only push, never expect client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
