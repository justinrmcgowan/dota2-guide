"""Context builder for Claude API user messages.

Assembles game state, matchup data, item catalog, and rules engine output
into the user message for Claude's recommendation generation.

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
    get_or_fetch_hero_timings,
)
from data.opendota_client import OpenDotaClient
from engine.schemas import EnemyContext, RecommendRequest, RuleResult
from engine.timing_zones import classify_timing_zones
from engine.win_condition import classify_draft, WinConditionResult

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

        # Phase 36: Game clock for time-aware reasoning (PROM-02)
        clock_section = self._build_game_clock_section(request)
        if clock_section:
            sections.append(clock_section)

        # Phase 36: Unusual role detection (PROM-03)
        unusual_role = self._build_unusual_role_section(request)
        if unusual_role:
            sections.append(unusual_role)

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

        # Phase 36: Partial draft caveats (PROM-04)
        partial_draft = self._build_partial_draft_section(request)
        if partial_draft:
            sections.append(partial_draft)

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

        # 6a. Pro reference section: Divine/Immortal item baselines
        pro_section = self._build_pro_reference_section(request.hero_id)
        if pro_section:
            sections.append(
                f"## What Divine/Immortal Players Build (5400+ MMR)\n{pro_section}\n"
                f"If you deviate from these popular choices, explain WHY your recommendation "
                f"is better for this specific matchup."
            )

        # 6b. Build timing benchmarks section (per D-05)
        timing_section = await self._build_timing_section(request.hero_id, db)
        if timing_section:
            sections.append(f"## Item Timing Benchmarks\n{timing_section}")

        # 6c. Team strategy section (WCON-01, WCON-04)
        strategy_section = self._build_team_strategy_section(request)
        if strategy_section:
            sections.append(f"## Team Strategy\n{strategy_section}")

        # 7b. Get neutral items catalog (from cache -- zero DB queries)
        neutral_catalog = self._build_neutral_catalog()
        if neutral_catalog:
            sections.append(f"## Neutral Items Catalog\n{neutral_catalog}")

        # Final instruction: the last thing Claude reads before generating
        if request.purchased_items:
            sections.append(
                "## Instructions\n"
                "Recommend items for REMAINING unpurchased slots only. "
                "Focus reasoning on how the game state changes affect "
                "remaining item choices. Still cover ALL remaining phases "
                "(core, late_game, situational) — never leave the build incomplete."
            )
        else:
            matchup_focus = (
                "Be specific about WHY each item counters THIS matchup. "
                "Reference what top players build and explain any deviations."
                if request.lane_opponents
                else "Focus on WHY each item synergizes with this hero's kit and role."
            )
            sections.append(
                f"## Instructions\n"
                f"Build a COMPLETE item guide covering ALL 5 phases: "
                f"starting, laning, core, late_game, and situational. "
                f"Do NOT skip any phase. The player needs to know what to buy "
                f"from minute 0 through six-slotted. {matchup_focus}\n"
                f"Include timing and gold_budget for each phase."
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

    # ------------------------------------------------------------------
    # Phase 36: Game clock, unusual role, partial draft annotations
    # ------------------------------------------------------------------

    def _build_game_clock_section(self, request: RecommendRequest) -> str:
        """Inject game clock into Claude context for time-aware reasoning.

        Returns empty string if game_time_seconds is None (pre-game or unknown).
        """
        if request.game_time_seconds is None:
            return ""

        minutes = request.game_time_seconds // 60
        seconds = request.game_time_seconds % 60
        clock_str = f"{minutes}:{seconds:02d}"

        turbo_note = " (TURBO MODE -- all timing benchmarks halved)" if request.turbo else ""

        return (
            f"## Game Clock\n"
            f"Current game time: {clock_str}{turbo_note}. "
            f"Adjust item recommendations for this timing window. "
            f"Items that are strong early may be too late; items that scale "
            f"may be the right pivot."
        )

    def _build_unusual_role_section(self, request: RecommendRequest) -> str:
        """Detect and flag unusual hero-role combinations.

        Uses HERO_ROLE_VIABLE from hero_selector to check if the hero
        is commonly played in this role. Returns annotation for Claude
        if the role is uncommon.
        """
        from engine.hero_selector import HERO_ROLE_VIABLE

        viable_ids = HERO_ROLE_VIABLE.get(request.role, set())
        if not viable_ids or request.hero_id in viable_ids:
            return ""  # Normal role or no data

        hero = self._get_hero(request.hero_id)
        hero_name = hero.localized_name if hero else f"Hero #{request.hero_id}"

        return (
            f"## Unusual Role Alert\n"
            f"{hero_name} is in an uncommon role (Pos {request.role}). "
            f"This is NOT a standard pick for this position. Adjust item builds "
            f"accordingly -- prioritize items that compensate for the hero's "
            f"weaknesses in this role rather than standard builds. "
            f"Acknowledge the unconventional pick in your strategy."
        )

    def _build_partial_draft_section(self, request: RecommendRequest) -> str:
        """Add caveats when draft is incomplete (<10 heroes picked).

        Returns empty string if draft is complete (5 allies + 5 enemies = 10).
        """
        total_heroes = 1 + len(request.allies) + len(request.all_opponents)  # player + allies + enemies
        if total_heroes >= 10:
            return ""  # Full draft

        return (
            f"## Partial Draft ({total_heroes}/10 heroes picked)\n"
            f"Draft is incomplete -- {10 - total_heroes} heroes not yet picked. "
            f"Focus on hero-intrinsic items (stats, lane sustainability, core timing items) "
            f"rather than counter-specific items. Recommendations will be refined as more "
            f"heroes are revealed. Acknowledge this uncertainty in your strategy."
        )

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

    def _build_pro_reference_section(self, hero_id: int) -> str:
        """Build 'What Divine/Immortal players build' section from cached baselines.

        Returns empty string if no baselines available (graceful fallback).
        """
        baselines = self.cache.get_hero_item_baselines(hero_id)
        if not baselines:
            return ""

        lines: list[str] = []
        phase_labels = {
            "starting": "Starting",
            "laning": "Laning",
            "core": "Core",
            "late_game": "Late Game",
        }
        for phase_key, label in phase_labels.items():
            items = baselines.get(phase_key, [])
            if not items:
                continue
            item_strs = [f"{name} ({count} games)" for _, name, count, _ in items[:5]]
            lines.append(f"{label}: {', '.join(item_strs)}")

        if not lines:
            return ""
        return "\n".join(lines)

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

    async def _build_timing_section(self, hero_id: int, db: AsyncSession) -> str:
        """Build timing benchmark section for Claude context.

        Format per item: "BKB: good <20min (58% WR), on-track 20-25min (52%), late >25min (41%)"
        Approximately 200 tokens for 5-8 items. Only includes items with
        sufficient timing data (per D-06).

        Uses stale-while-revalidate on-demand fetch when cache is empty (DATA-03).
        Returns empty string if no timing data available for this hero.
        """
        timings = self.cache.get_hero_timings(hero_id)
        if not timings:
            # On-demand fetch for heroes not yet in cache (DATA-03 debt fix)
            timings = await get_or_fetch_hero_timings(hero_id, db, self.opendota)
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

    def _build_team_strategy_section(self, request: "RecommendRequest") -> str:
        """Build ## Team Strategy section for Claude context.

        Classifies allied team (from request.allies + request.hero_id) and
        enemy team (from request.all_opponents) into macro archetypes.
        Returns empty string if either team has fewer than 3 heroes.

        WCON-01: Allied archetype classification
        WCON-04: Enemy archetype classification using full all_opponents list
        """
        # Allied team: player hero + allies (up to 5 total)
        allied_ids = [request.hero_id] + list(request.allies)
        allied_result = classify_draft(allied_ids, self.cache)

        # Enemy team: full opponents list (not lane_opponents -- WCON-04)
        enemy_result = classify_draft(list(request.all_opponents), self.cache)

        if allied_result is None and enemy_result is None:
            return ""

        lines: list[str] = []
        if allied_result:
            confidence_note = f" ({allied_result.confidence} confidence)"
            lines.append(f"Allied strategy: {allied_result.archetype}{confidence_note}")

        if enemy_result:
            confidence_note = f" ({enemy_result.confidence} confidence)"
            lines.append(f"Enemy strategy: {enemy_result.archetype}{confidence_note}")

        return "\n".join(lines)
