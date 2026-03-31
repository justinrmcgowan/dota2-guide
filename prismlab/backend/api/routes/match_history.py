"""Match logging and history endpoints for game analytics.

POST /match-log: Ingest end-of-game data with items + recommendations.
GET /match-history: Paginated, filterable match list with nested items/recs.
GET /match-stats: Aggregate metrics (win rate, follow rate by outcome).
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import MatchLog, MatchItem, MatchRecommendation

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class MatchItemPayload(BaseModel):
    slot_type: str  # "inventory" | "backpack" | "neutral"
    item_name: str


class MatchRecommendationPayload(BaseModel):
    phase: str
    item_id: int
    item_name: str
    priority: str
    was_purchased: bool


class MatchLogPayload(BaseModel):
    match_id: str
    hero_id: int
    hero_name: str
    role: int
    playstyle: str | None = None
    side: str | None = None
    lane: str | None = None
    allies: list[int] = []
    opponents: list[int] = []
    lane_opponents: list[int] = []
    win: bool
    duration_seconds: int | None = None
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gpm: int = 0
    xpm: int = 0
    net_worth: int = 0
    last_hits: int = 0
    denies: int = 0
    engine_mode: str | None = None
    was_fallback: bool = False
    overall_strategy: str | None = None
    items: list[MatchItemPayload] = []
    recommendations: list[MatchRecommendationPayload] = []


class MatchHistoryItem(BaseModel):
    id: int
    match_id: str
    hero_id: int
    hero_name: str
    role: int
    playstyle: str | None
    side: str | None
    lane: str | None
    win: bool
    duration_seconds: int | None
    kills: int
    deaths: int
    assists: int
    gpm: int
    xpm: int
    net_worth: int
    engine_mode: str | None
    was_fallback: bool
    overall_strategy: str | None
    follow_rate: float | None
    played_at: str  # ISO format string
    items: list[MatchItemPayload]
    recommendations: list[MatchRecommendationPayload]


class MatchHistoryResponse(BaseModel):
    matches: list[MatchHistoryItem]
    total: int
    limit: int
    offset: int


class FlaggedItemResponse(BaseModel):
    """Item recommended frequently but rarely purchased -- prompt tuning candidate."""
    item_name: str
    times_recommended: int
    times_purchased: int
    purchase_rate: float  # 0.0-1.0


class MatchStatsResponse(BaseModel):
    total_games: int
    wins: int
    losses: int
    win_rate: float
    avg_follow_rate: float | None
    avg_follow_rate_wins: float | None
    avg_follow_rate_losses: float | None
    # Accuracy metrics
    follow_win_rate: float | None       # win rate for games where follow_rate >= 0.7
    deviate_win_rate: float | None      # win rate for games where follow_rate < 0.4
    follow_game_count: int              # number of games in follow bucket
    deviate_game_count: int             # number of games in deviate bucket
    flagged_items: list[FlaggedItemResponse]  # items recommended 5+ times with purchase_rate < 0.3


# ---------------------------------------------------------------------------
# POST /match-log
# ---------------------------------------------------------------------------

@router.post("/match-log")
async def create_match_log(
    payload: MatchLogPayload,
    db: AsyncSession = Depends(get_db),
):
    """Ingest end-of-game match data with items and recommendations.

    Computes follow_rate (recommended items purchased / total recommended)
    and persists across match_log, match_items, and match_recommendations.
    """
    # Compute follow rate
    total_recs = len(payload.recommendations)
    if total_recs > 0:
        purchased_count = sum(1 for r in payload.recommendations if r.was_purchased)
        follow_rate = round(purchased_count / total_recs, 4)
    else:
        follow_rate = None

    # Create match log row
    match_log = MatchLog(
        match_id=payload.match_id,
        hero_id=payload.hero_id,
        hero_name=payload.hero_name,
        role=payload.role,
        playstyle=payload.playstyle,
        side=payload.side,
        lane=payload.lane,
        allies=payload.allies,
        opponents=payload.opponents,
        lane_opponents=payload.lane_opponents,
        win=payload.win,
        duration_seconds=payload.duration_seconds,
        kills=payload.kills,
        deaths=payload.deaths,
        assists=payload.assists,
        gpm=payload.gpm,
        xpm=payload.xpm,
        net_worth=payload.net_worth,
        last_hits=payload.last_hits,
        denies=payload.denies,
        engine_mode=payload.engine_mode,
        was_fallback=payload.was_fallback,
        overall_strategy=payload.overall_strategy,
        follow_rate=follow_rate,
    )
    db.add(match_log)
    await db.flush()  # Get the auto-generated ID

    # Bulk-create item rows
    for item in payload.items:
        db.add(MatchItem(
            match_log_id=match_log.id,
            slot_type=item.slot_type,
            item_name=item.item_name,
        ))

    # Bulk-create recommendation rows
    for rec in payload.recommendations:
        db.add(MatchRecommendation(
            match_log_id=match_log.id,
            phase=rec.phase,
            item_id=rec.item_id,
            item_name=rec.item_name,
            priority=rec.priority,
            was_purchased=rec.was_purchased,
        ))

    await db.commit()

    return {"status": "ok", "id": match_log.id, "follow_rate": follow_rate}


# ---------------------------------------------------------------------------
# GET /match-history
# ---------------------------------------------------------------------------

@router.get("/match-history", response_model=MatchHistoryResponse)
async def get_match_history(
    hero_id: int | None = Query(None),
    result: str | None = Query(None),   # "win" or "loss"
    mode: str | None = Query(None),     # "fast" / "auto" / "deep"
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated match list with nested items and recommendations.

    Filters: hero_id, result (win/loss), mode (engine_mode).
    """
    # Base filter conditions
    conditions = []
    if hero_id is not None:
        conditions.append(MatchLog.hero_id == hero_id)
    if result == "win":
        conditions.append(MatchLog.win == True)  # noqa: E712
    elif result == "loss":
        conditions.append(MatchLog.win == False)  # noqa: E712
    if mode is not None:
        conditions.append(MatchLog.engine_mode == mode)

    # Count total matching rows
    count_stmt = select(func.count(MatchLog.id))
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch paginated match logs
    stmt = select(MatchLog).order_by(MatchLog.played_at.desc()).limit(limit).offset(offset)
    for cond in conditions:
        stmt = stmt.where(cond)
    rows = await db.execute(stmt)
    matches = list(rows.scalars().all())

    if not matches:
        return MatchHistoryResponse(matches=[], total=total, limit=limit, offset=offset)

    match_ids = [m.id for m in matches]

    # Batch-load items
    items_stmt = select(MatchItem).where(MatchItem.match_log_id.in_(match_ids))
    items_result = await db.execute(items_stmt)
    all_items = items_result.scalars().all()

    items_by_match: dict[int, list[MatchItemPayload]] = {}
    for item in all_items:
        items_by_match.setdefault(item.match_log_id, []).append(
            MatchItemPayload(slot_type=item.slot_type, item_name=item.item_name)
        )

    # Batch-load recommendations
    recs_stmt = select(MatchRecommendation).where(MatchRecommendation.match_log_id.in_(match_ids))
    recs_result = await db.execute(recs_stmt)
    all_recs = recs_result.scalars().all()

    recs_by_match: dict[int, list[MatchRecommendationPayload]] = {}
    for rec in all_recs:
        recs_by_match.setdefault(rec.match_log_id, []).append(
            MatchRecommendationPayload(
                phase=rec.phase,
                item_id=rec.item_id,
                item_name=rec.item_name,
                priority=rec.priority,
                was_purchased=rec.was_purchased,
            )
        )

    # Assemble response
    history_items = []
    for m in matches:
        history_items.append(MatchHistoryItem(
            id=m.id,
            match_id=m.match_id,
            hero_id=m.hero_id,
            hero_name=m.hero_name,
            role=m.role,
            playstyle=m.playstyle,
            side=m.side,
            lane=m.lane,
            win=m.win,
            duration_seconds=m.duration_seconds,
            kills=m.kills,
            deaths=m.deaths,
            assists=m.assists,
            gpm=m.gpm,
            xpm=m.xpm,
            net_worth=m.net_worth,
            engine_mode=m.engine_mode,
            was_fallback=m.was_fallback,
            overall_strategy=m.overall_strategy,
            follow_rate=m.follow_rate,
            played_at=m.played_at.isoformat() if m.played_at else "",
            items=items_by_match.get(m.id, []),
            recommendations=recs_by_match.get(m.id, []),
        ))

    return MatchHistoryResponse(matches=history_items, total=total, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# GET /match-stats
# ---------------------------------------------------------------------------

@router.get("/match-stats", response_model=MatchStatsResponse)
async def get_match_stats(db: AsyncSession = Depends(get_db)):
    """Return aggregate match statistics: games, win rate, follow rate by outcome."""
    # Total games and wins
    total_result = await db.execute(select(func.count(MatchLog.id)))
    total_games = total_result.scalar() or 0

    wins_result = await db.execute(
        select(func.count(MatchLog.id)).where(MatchLog.win == True)  # noqa: E712
    )
    wins = wins_result.scalar() or 0
    losses = total_games - wins

    win_rate = round(wins / total_games, 4) if total_games > 0 else 0.0

    # Average follow rates
    avg_fr_result = await db.execute(
        select(func.avg(MatchLog.follow_rate)).where(MatchLog.follow_rate.isnot(None))
    )
    avg_follow_rate = avg_fr_result.scalar()
    if avg_follow_rate is not None:
        avg_follow_rate = round(float(avg_follow_rate), 4)

    avg_fr_wins_result = await db.execute(
        select(func.avg(MatchLog.follow_rate)).where(
            MatchLog.win == True,  # noqa: E712
            MatchLog.follow_rate.isnot(None),
        )
    )
    avg_follow_rate_wins = avg_fr_wins_result.scalar()
    if avg_follow_rate_wins is not None:
        avg_follow_rate_wins = round(float(avg_follow_rate_wins), 4)

    avg_fr_losses_result = await db.execute(
        select(func.avg(MatchLog.follow_rate)).where(
            MatchLog.win == False,  # noqa: E712
            MatchLog.follow_rate.isnot(None),
        )
    )
    avg_follow_rate_losses = avg_fr_losses_result.scalar()
    if avg_follow_rate_losses is not None:
        avg_follow_rate_losses = round(float(avg_follow_rate_losses), 4)

    # ---- Follow win rate: games where follow_rate >= 0.7 ----
    follow_count_q = await db.execute(
        select(func.count(MatchLog.id)).where(
            MatchLog.follow_rate >= 0.7,
            MatchLog.follow_rate.isnot(None),
        )
    )
    follow_game_count = follow_count_q.scalar() or 0

    follow_wins_q = await db.execute(
        select(func.count(MatchLog.id)).where(
            MatchLog.follow_rate >= 0.7,
            MatchLog.follow_rate.isnot(None),
            MatchLog.win == True,  # noqa: E712
        )
    )
    follow_wins = follow_wins_q.scalar() or 0
    follow_win_rate = round(follow_wins / follow_game_count, 4) if follow_game_count > 0 else None

    # ---- Deviate win rate: games where follow_rate < 0.4 ----
    deviate_count_q = await db.execute(
        select(func.count(MatchLog.id)).where(
            MatchLog.follow_rate < 0.4,
            MatchLog.follow_rate.isnot(None),
        )
    )
    deviate_game_count = deviate_count_q.scalar() or 0

    deviate_wins_q = await db.execute(
        select(func.count(MatchLog.id)).where(
            MatchLog.follow_rate < 0.4,
            MatchLog.follow_rate.isnot(None),
            MatchLog.win == True,  # noqa: E712
        )
    )
    deviate_wins = deviate_wins_q.scalar() or 0
    deviate_win_rate = round(deviate_wins / deviate_game_count, 4) if deviate_game_count > 0 else None

    # ---- Flagged items: recommended 5+ times with purchase rate below 30% ----
    flagged_q = await db.execute(
        select(
            MatchRecommendation.item_name,
            func.count(MatchRecommendation.id).label("times_recommended"),
            func.sum(
                case((MatchRecommendation.was_purchased == True, 1), else_=0)  # noqa: E712
            ).label("times_purchased"),
        )
        .where(MatchRecommendation.priority.in_(["core", "situational"]))  # exclude luxury -- optional items
        .group_by(MatchRecommendation.item_name)
        .having(func.count(MatchRecommendation.id) >= 5)
    )
    flagged_rows = flagged_q.all()

    flagged_items: list[FlaggedItemResponse] = []
    for row in flagged_rows:
        purchase_rate = round(row.times_purchased / row.times_recommended, 4) if row.times_recommended > 0 else 0.0
        if purchase_rate < 0.3:
            flagged_items.append(FlaggedItemResponse(
                item_name=row.item_name,
                times_recommended=row.times_recommended,
                times_purchased=row.times_purchased,
                purchase_rate=purchase_rate,
            ))

    # Sort flagged items by purchase_rate ascending (worst offenders first)
    flagged_items.sort(key=lambda x: x.purchase_rate)

    return MatchStatsResponse(
        total_games=total_games,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        avg_follow_rate=avg_follow_rate,
        avg_follow_rate_wins=avg_follow_rate_wins,
        avg_follow_rate_losses=avg_follow_rate_losses,
        follow_win_rate=follow_win_rate,
        deviate_win_rate=deviate_win_rate,
        follow_game_count=follow_game_count,
        deviate_game_count=deviate_game_count,
        flagged_items=flagged_items,
    )
