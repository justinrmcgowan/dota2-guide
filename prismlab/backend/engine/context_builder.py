"""Context builder for Claude API user messages.

Assembles game state, matchup data, item catalog, and rules engine output
into a compact user message. Targets under 1500 tokens for the user message.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models import Hero, Item
from data.matchup_service import (
    get_or_fetch_matchup,
    get_hero_item_popularity,
    get_relevant_items,
)
from data.opendota_client import OpenDotaClient
from engine.schemas import RecommendRequest, RuleResult

logger = logging.getLogger(__name__)

# Map item popularity API keys to display labels
_POPULARITY_PHASE_MAP = {
    "start_game_items": "Starting",
    "early_game_items": "Early",
    "mid_game_items": "Mid",
    "late_game_items": "Late",
}


class ContextBuilder:
    """Builds the user message for Claude from game state + matchup data.

    The system prompt (static, cached) is separate — this only builds
    the per-request user message.
    """

    def __init__(self, opendota_client: OpenDotaClient):
        self.opendota = opendota_client

    async def build(
        self,
        request: RecommendRequest,
        rules_items: list[RuleResult],
        db: AsyncSession,
    ) -> str:
        """Build the user message for Claude from game state + matchup data.

        Target: under 1500 tokens for the user message.
        The system prompt (static, cached) is separate.
        """
        # 1. Fetch player's hero
        hero = await self._get_hero(request.hero_id, db)
        hero_name = hero.localized_name if hero else f"Hero #{request.hero_id}"
        primary_attr = (hero.primary_attr or "unknown") if hero else "unknown"
        attack_type = (hero.attack_type or "unknown") if hero else "unknown"

        # 2. Fetch opponent hero names and matchup data
        opponent_lines = await self._build_opponent_lines(
            request.hero_id, request.lane_opponents, db
        )

        # 3. Build already recommended section from rules
        rules_lines = self._build_rules_lines(rules_items)

        # 4. Get filtered item catalog
        items = await get_relevant_items(request.hero_id, request.role, db)
        item_lines = self._build_item_catalog(items)

        # 5. Get item popularity (optional)
        popularity_section = await self._build_popularity_section(
            request.hero_id, db, items
        )

        # 6. Assemble the message
        role_label = f"Pos {request.role}"
        sections = [
            f"## Your Hero\n{hero_name} ({role_label}, {request.playstyle} playstyle, "
            f"{request.side} {request.lane} lane)\n"
            f"Primary: {primary_attr}, Attack: {attack_type}",
        ]

        if opponent_lines:
            sections.append(f"## Lane Opponents\n{opponent_lines}")

        if rules_lines:
            sections.append(
                f"## Already Recommended (from rules engine, do NOT duplicate)\n"
                f"{rules_lines}"
            )

        sections.append(
            f"## Available Items (use ONLY these item_ids)\n{item_lines}"
        )

        if popularity_section:
            sections.append(
                f"## Popular Items on This Hero\n{popularity_section}"
            )

        sections.append(
            "Recommend items for each game phase. Be specific about WHY "
            "each item is good in THIS matchup."
        )

        return "\n\n".join(sections)

    async def _get_hero(self, hero_id: int, db: AsyncSession) -> Hero | None:
        """Look up a hero by ID from the database."""
        result = await db.execute(select(Hero).where(Hero.id == hero_id))
        return result.scalar_one_or_none()

    async def _build_opponent_lines(
        self,
        hero_id: int,
        lane_opponents: list[int],
        db: AsyncSession,
    ) -> str:
        """Build opponent section with matchup win rates."""
        lines: list[str] = []
        for opp_id in lane_opponents:
            opp_hero = await self._get_hero(opp_id, db)
            opp_name = opp_hero.localized_name if opp_hero else "Unknown Hero"

            matchup = await get_or_fetch_matchup(
                hero_id, opp_id, db, self.opendota
            )
            if matchup and matchup.win_rate is not None:
                pct = round(matchup.win_rate * 100, 1)
                games = matchup.games_played or 0
                lines.append(
                    f"- {opp_name}: {pct}% win rate over {games} games"
                )
            else:
                lines.append(f"- {opp_name}: no matchup data available")

        return "\n".join(lines)

    def _build_rules_lines(self, rules_items: list[RuleResult]) -> str:
        """Format already-recommended items from the rules engine."""
        if not rules_items:
            return ""
        lines = [
            f"- {r.item_name} ({r.phase}): {r.reasoning}" for r in rules_items
        ]
        return "\n".join(lines)

    def _build_item_catalog(self, items: list[dict]) -> str:
        """Build compact item catalog: 'id: name (cost)'."""
        lines = [f"{item['id']}: {item['name']} ({item['cost']}g)" for item in items]
        return "\n".join(lines)

    async def _build_popularity_section(
        self,
        hero_id: int,
        db: AsyncSession,
        available_items: list[dict],
    ) -> str:
        """Build popular items section grouped by game phase."""
        popularity = await get_hero_item_popularity(hero_id, db, self.opendota)
        if not popularity:
            return ""

        # Build an item name lookup from available items
        item_name_map = {item["id"]: item["name"] for item in available_items}

        # Also look up items from DB for IDs not in filtered catalog
        all_item_result = await db.execute(select(Item))
        all_items = all_item_result.scalars().all()
        for item in all_items:
            if item.id not in item_name_map:
                item_name_map[item.id] = item.name

        sections: list[str] = []
        for api_key, label in _POPULARITY_PHASE_MAP.items():
            phase_data: dict[str, Any] = popularity.get(api_key, {})
            if not phase_data:
                continue

            # Sort by count descending, take top 5
            sorted_items = sorted(
                phase_data.items(), key=lambda x: int(x[1]), reverse=True
            )[:5]

            item_names = []
            for item_id_str, count in sorted_items:
                item_id = int(item_id_str)
                name = item_name_map.get(item_id, f"Item #{item_id}")
                item_names.append(name)

            if item_names:
                sections.append(f"{label}: {', '.join(item_names)}")

        return "\n".join(sections)
