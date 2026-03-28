from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, Boolean, Text, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from data.database import Base


class Hero(Base):
    """Dota 2 hero data seeded from OpenDota API."""

    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    localized_name: Mapped[str] = mapped_column(String, nullable=False)
    internal_name: Mapped[str] = mapped_column(String, nullable=False)
    primary_attr: Mapped[str | None] = mapped_column(String)
    attack_type: Mapped[str | None] = mapped_column(String)
    roles: Mapped[list | None] = mapped_column(JSON)

    # Base stats
    base_health: Mapped[float | None] = mapped_column(Float)
    base_mana: Mapped[float | None] = mapped_column(Float)
    base_armor: Mapped[float | None] = mapped_column(Float)
    base_str: Mapped[float | None] = mapped_column(Float)
    base_agi: Mapped[float | None] = mapped_column(Float)
    base_int: Mapped[float | None] = mapped_column(Float)
    str_gain: Mapped[float | None] = mapped_column(Float)
    agi_gain: Mapped[float | None] = mapped_column(Float)
    int_gain: Mapped[float | None] = mapped_column(Float)
    base_attack_min: Mapped[int | None] = mapped_column(Integer)
    base_attack_max: Mapped[int | None] = mapped_column(Integer)
    attack_range: Mapped[int | None] = mapped_column(Integer)
    move_speed: Mapped[int | None] = mapped_column(Integer)

    # Metadata
    img_url: Mapped[str | None] = mapped_column(String)
    icon_url: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())


class Item(Base):
    """Dota 2 item data seeded from OpenDota API."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    internal_name: Mapped[str] = mapped_column(String, nullable=False)
    cost: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Item properties
    components: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_recipe: Mapped[bool] = mapped_column(Boolean, default=False)
    is_neutral: Mapped[bool] = mapped_column(Boolean, default=False)
    tier: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Stat bonuses
    bonuses: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Descriptions
    active_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    passive_desc: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    img_url: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())


class MatchupData(Base):
    """Hero vs hero matchup statistics. Schema-only in Phase 1."""

    __tablename__ = "matchup_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"))
    opponent_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"))
    win_rate: Mapped[float | None] = mapped_column(Float)
    games_played: Mapped[int | None] = mapped_column(Integer)
    common_items: Mapped[list | None] = mapped_column(JSON)
    common_starting_items: Mapped[list | None] = mapped_column(JSON)
    bracket: Mapped[str] = mapped_column(String, default="high")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())


class HeroAbilityData(Base):
    """Cached hero ability constants from OpenDota. One row per hero, abilities_json contains all ability metadata."""

    __tablename__ = "hero_ability_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"), unique=True)
    abilities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())


class ItemTimingData(Base):
    """Cached item timing benchmark data per hero from OpenDota scenarios. One row per hero, timings_json contains all item timing buckets."""

    __tablename__ = "item_timing_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"), unique=True)
    timings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())


class ApiUsage(Base):
    """Track Claude API usage per month for budget enforcement (Phase 26)."""

    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String, index=True)  # "2026-03"
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    request_count: Mapped[int] = mapped_column(Integer, default=0)


class DataRefreshLog(Base):
    """Tracks data refresh pipeline executions for freshness reporting."""

    __tablename__ = "data_refresh_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    refresh_type: Mapped[str] = mapped_column(String, nullable=False)  # "full", "heroes", "items"
    status: Mapped[str] = mapped_column(String, nullable=False)  # "success" or "failed"
    heroes_updated: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
