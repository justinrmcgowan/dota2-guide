"""Context builder for Claude API user messages.

Assembles game state, matchup data, item catalog, and rules engine output
into a compact user message. Targets under 1500 tokens for the user message.

All hero/item lookups come from DataCache -- zero DB queries for hero/item
data on the hot path. Only matchup and popularity data still hit the DB.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.cache import DataCache, HeroCached
from data.matchup_service import (
    get_or_fetch_matchup,
    get_hero_item_popularity,
)
from data.opendota_client import OpenDotaClient
from engine.schemas import EnemyContext, RecommendRequest, RuleResult
from engine.timing_zones import classify_timing_zones

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

    def __init__(self, opendota_client: OpenDotaClient, cache: DataCache):
        self.opendota = opendota_client
        self.cache = cache

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
        # 1. Fetch player's hero (from cache -- zero DB queries)
        hero = self._get_hero(request.hero_id)
        hero_name = hero.localized_name if hero else f"Hero #{request.hero_id}"
        primary_attr = (hero.primary_attr or "unknown") if hero else "unknown"
        attack_type = (hero.attack_type or "unknown") if hero else "unknown"

        # 2. Build allied heroes section (if any)
        ally_lines = await self._build_ally_lines(request.allies, db)

        # 3. Fetch opponent hero names and matchup data
        opponent_lines = await self._build_opponent_lines(
            request.hero_id, request.lane_opponents, db
        )

        # 4. Build already recommended section from rules
        rules_lines = self._build_rules_lines(rules_items)

        # 5. Get filtered item catalog (from cache -- zero DB queries)
        items = self.cache.get_relevant_items(request.role)
        item_lines = self._build_item_catalog(items)

        # 6. Get item popularity (optional)
        popularity_section = await self._build_popularity_section(
            request.hero_id, db, items
        )

        # 7. Build mid-game context (if present)
        midgame_section = self._build_midgame_section(request)

        # 8. Assemble the message
        role_label = f"Pos {request.role}"
        sections = [
            f"## Your Hero\n{hero_name} ({role_label}, {request.playstyle} playstyle, "
            f"{request.side} {request.lane} lane)\n"
            f"Primary: {primary_attr}, Attack: {attack_type}",
        ]

        if ally_lines:
            sections.append(f"## Allied Heroes\n{ally_lines}")

        if opponent_lines:
            sections.append(f"## Lane Opponents\n{opponent_lines}")
        else:
            sections.append(
                "## Lane Opponents\nNone selected. Do NOT invent or assume opponents. "
                "Recommend items based on hero strengths, role duties, and playstyle."
            )

        # 3b. Build enemy team KDA context (if screenshot data present)
        enemy_status = self._build_enemy_context_section(request)
        if enemy_status:
            sections.append(enemy_status)

        if midgame_section:
            sections.append(midgame_section)

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

        # 6b. Build timing benchmarks section (per D-05)
        timing_section = self._build_timing_section(request.hero_id)
        if timing_section:
            sections.append(f"## Item Timing Benchmarks\n{timing_section}")

        # 7b. Get neutral items catalog (from cache -- zero DB queries)
        neutral_catalog = self._build_neutral_catalog()
        if neutral_catalog:
            sections.append(f"## Neutral Items Catalog\n{neutral_catalog}")

        # Final instruction: adjust for mid-game re-evaluation
        if request.purchased_items:
            sections.append(
                "Recommend items for REMAINING unpurchased slots only. "
                "Focus reasoning on how the game state changes affect "
                "remaining item choices."
            )
        else:
            if request.lane_opponents:
                sections.append(
                    "Recommend items for each game phase. Be specific about WHY "
                    "each item is good in THIS matchup."
                )
            else:
                sections.append(
                    "Recommend items for each game phase. Focus on WHY "
                    "each item synergizes with this hero's kit and role."
                )

        return "\n\n".join(sections)

    def _build_midgame_section(self, request: RecommendRequest) -> str:
        """Build mid-game context section for Claude prompt.

        Returns empty string if no mid-game fields are present, allowing
        backward compatibility with initial draft-phase requests.
        """
        has_midgame = (
            request.lane_result is not None
            or request.damage_profile is not None
            or len(request.enemy_items_spotted) > 0
        )
        if not has_midgame:
            return ""

        lines = ["## Mid-Game Update"]

        if request.lane_result is not None:
            lines.append(f"Lane Result: {request.lane_result.capitalize()}")

        if request.damage_profile is not None:
            parts = []
            for dmg_type, pct in request.damage_profile.items():
                parts.append(f"{dmg_type.capitalize()} {pct}%")
            lines.append(f"Damage Taken: {', '.join(parts)}")

        if request.enemy_items_spotted:
            # Map internal names to display names: replace underscores, title-case
            display_names = [
                name.replace("_", " ").title()
                for name in request.enemy_items_spotted
            ]
            lines.append(f"Enemy Items Spotted: {', '.join(display_names)}")

        return "\n".join(lines)

    def _build_enemy_context_section(self, request: RecommendRequest) -> str:
        """Build enemy team KDA/level section from screenshot data.

        Returns empty string if no enemy_context entries exist, preserving
        backward compatibility with requests that lack screenshot data.
        """
        if not request.enemy_context:
            return ""

        lines: list[str] = []
        for ec in request.enemy_context:
            # Skip entries with no KDA data at all
            if ec.kills is None and ec.deaths is None and ec.assists is None:
                continue

            hero = self._get_hero(ec.hero_id)
            name = hero.localized_name if hero else f"Hero #{ec.hero_id}"

            # Build KDA string
            k = ec.kills if ec.kills is not None else 0
            d = ec.deaths if ec.deaths is not None else 0
            a = ec.assists if ec.assists is not None else 0

            level_part = f" (Lv {ec.level})" if ec.level is not None else ""

            # Threat annotation
            annotation = ""
            if k >= 5 and d > 0 and k >= 2 * d:
                annotation = " -- fed, high threat"
            elif k >= 5 and d == 0:
                annotation = " -- fed, high threat"
            elif d >= 3 and k > 0 and d >= 2 * k:
                annotation = " -- behind"
            elif d >= 3 and k == 0:
                annotation = " -- behind"

            lines.append(f"- {name}{level_part}: {k}/{d}/{a}{annotation}")

        if not lines:
            return ""

        return "## Enemy Team Status\n" + "\n".join(lines)

    def _get_hero(self, hero_id: int) -> HeroCached | None:
        """Look up a hero by ID from the in-memory cache."""
        return self.cache.get_hero(hero_id)

    def _get_counter_relevant_abilities(self, hero_id: int) -> str:
        """Pre-filter abilities to only counter-relevant properties.

        Returns a compact string like:
        "Death Ward (channeled, BKB-pierce); Maledict (undispellable)"

        Only includes abilities with at least one counter-relevant property:
        channeled, passive, BKB-pierce, or undispellable debuff.
        Per D-06: ~150 tokens total across all opponents.
        """
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return ""
        tags: list[str] = []
        for a in abilities:
            props: list[str] = []
            if a.is_channeled:
                props.append("channeled")
            if a.is_passive:
                props.append("passive")
            if a.bkbpierce:
                props.append("BKB-pierce")
            if a.dispellable and a.dispellable.lower() in ("no", "strong dispels only"):
                props.append("undispellable")
            if props:
                tags.append(f"{a.dname} ({', '.join(props)})")
        return "; ".join(tags)

    async def _build_opponent_lines(
        self,
        hero_id: int,
        lane_opponents: list[int],
        db: AsyncSession,
    ) -> str:
        """Build opponent section with matchup win rates and ability threats."""
        lines: list[str] = []
        for opp_id in lane_opponents:
            opp_hero = self._get_hero(opp_id)
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

            # Inline ability annotations (D-06, D-07)
            ability_tags = self._get_counter_relevant_abilities(opp_id)
            if ability_tags:
                lines.append(f"  Threats: {ability_tags}")

        return "\n".join(lines)

    async def _build_ally_lines(
        self,
        allies: list[int],
        db: AsyncSession,
    ) -> str:
        """Build allied heroes section with typical item builds."""
        if not allies:
            return ""

        lines: list[str] = []
        fallback = "no typical build data available"
        for ally_id in allies:
            ally_hero = self._get_hero(ally_id)
            ally_name = ally_hero.localized_name if ally_hero else f"Hero #{ally_id}"

            # Fetch popular items for this ally
            popularity = await get_hero_item_popularity(ally_id, db, self.opendota)
            popular_items = (
                self._extract_top_items(popularity)
                if popularity
                else ""
            )
            if popular_items:
                lines.append(
                    f"- {ally_name}: typical builds include {popular_items}"
                )
            else:
                lines.append(f"- {ally_name}: {fallback}")

        return "\n".join(lines)

    def _extract_top_items(
        self,
        popularity: dict,
        limit: int = 5,
    ) -> str:
        """Merge all phase popularity dicts and return top item names.

        Combines early, mid, and late game item counts into one ranking,
        takes the top N unique items, resolves names from cache.
        Returns a comma-separated string of item names.
        """
        merged: dict[int, int] = {}
        for phase_key in _POPULARITY_PHASE_MAP:
            phase_data = popularity.get(phase_key, {})
            if not phase_data:
                continue
            for item_id_str, count in phase_data.items():
                item_id = int(item_id_str)
                merged[item_id] = merged.get(item_id, 0) + int(count)

        if not merged:
            return ""

        # Sort by count descending, take top N
        sorted_items = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        top_ids = [item_id for item_id, _ in sorted_items[:limit]]

        # Resolve item names from cache (zero DB queries)
        item_name_map = self.cache.get_item_name_map()

        names = [item_name_map.get(iid, f"Item #{iid}") for iid in top_ids]
        return ", ".join(names)

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

        # Also look up items from cache for IDs not in filtered catalog
        full_name_map = self.cache.get_item_name_map()
        for item_id, name in full_name_map.items():
            if item_id not in item_name_map:
                item_name_map[item_id] = name

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

    def _build_neutral_catalog(self) -> str:
        """Build compact neutral items catalog grouped by tier.

        Reads all neutral items from cache and formats them as compact
        markdown for Claude to rank by hero synergy. Returns empty string
        if no neutral items exist in the cache.
        """
        tier_groups = self.cache.get_neutral_items_by_tier()
        if not tier_groups:
            return ""

        tier_lines: list[str] = []
        for tier in sorted(tier_groups.keys()):
            items = tier_groups[tier]
            names = [item["name"] for item in items]
            tier_lines.append(f"T{tier}: {', '.join(names)}")

        return "\n".join(tier_lines)

    def _build_timing_section(self, hero_id: int) -> str:
        """Build timing benchmark section for Claude context.

        Format per item: "BKB: good <20min (58% WR), on-track 20-25min (52%), late >25min (41%)"
        Approximately 200 tokens for 5-8 items. Only includes items with
        sufficient timing data (per D-06).

        Returns empty string if no timing data available for this hero.
        """
        timings = self.cache.get_hero_timings(hero_id)
        if not timings:
            return ""

        lines: list[str] = []
        for item_name, buckets in timings.items():
            classified = classify_timing_zones(buckets)
            if classified is None:
                continue

            display_name = item_name.replace("_", " ").title()
            good_wr = round(classified["good_win_rate"] * 100)
            late_wr = round(classified["late_win_rate"] * 100)

            line = (
                f"{display_name}: good {classified['good_range']} ({good_wr}% WR), "
                f"on-track {classified['ontrack_range']}, "
                f"late {classified['late_range']} ({late_wr}% WR)"
            )
            if classified["is_urgent"]:
                line += " [TIMING-CRITICAL]"
            lines.append(line)

        if not lines:
            return ""
        return "\n".join(lines)
