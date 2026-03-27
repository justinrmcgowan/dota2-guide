"""Unit tests for the context builder that assembles Claude API user messages.

Hero/item lookups come from DataCache (loaded from test DB in conftest).
Only matchup and popularity data are still mocked (they hit external APIs).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from data.cache import data_cache
from engine.context_builder import ContextBuilder
from engine.schemas import RecommendRequest, RuleResult


def _make_request(**kwargs) -> RecommendRequest:
    """Create a minimal valid RecommendRequest for testing."""
    defaults = dict(
        hero_id=1,
        role=1,
        playstyle="Farm-first",
        side="radiant",
        lane="safe",
        lane_opponents=[],
        allies=[],
    )
    defaults.update(kwargs)
    return RecommendRequest(**defaults)


@pytest.fixture
def builder():
    """ContextBuilder with a mock OpenDota client and DataCache singleton."""
    mock_opendota = MagicMock()
    return ContextBuilder(opendota_client=mock_opendota, cache=data_cache)


# ---------------------------------------------------------------------------
# _build_rules_lines (pure, no DB)
# ---------------------------------------------------------------------------


class TestBuildRulesLines:
    def test_formats_rule_items(self, builder: ContextBuilder):
        """Rule items are formatted with name, phase, and reasoning."""
        rules = [
            RuleResult(
                item_id=36,
                item_name="Magic Stick",
                reasoning="Bristleback spams quills",
                phase="laning",
                priority="core",
            ),
            RuleResult(
                item_id=116,
                item_name="Black King Bar",
                reasoning="Zeus deals heavy magic damage",
                phase="core",
                priority="core",
            ),
        ]
        result = builder._build_rules_lines(rules)
        assert "Magic Stick" in result
        assert "laning" in result
        assert "Bristleback spams quills" in result
        assert "Black King Bar" in result
        assert "core" in result
        assert "Zeus deals heavy magic damage" in result

    def test_empty_rules_returns_empty_string(self, builder: ContextBuilder):
        """Empty rules list produces empty string."""
        result = builder._build_rules_lines([])
        assert result == ""

    def test_single_rule_formatting(self, builder: ContextBuilder):
        """Single rule formats as '- name (phase): reasoning'."""
        rules = [
            RuleResult(
                item_id=48,
                item_name="Power Treads",
                reasoning="Good stat switching",
                phase="laning",
                priority="core",
            ),
        ]
        result = builder._build_rules_lines(rules)
        assert result == "- Power Treads (laning): Good stat switching"


# ---------------------------------------------------------------------------
# _build_midgame_section (pure, no DB)
# ---------------------------------------------------------------------------


class TestBuildMidgameSection:
    def test_no_midgame_fields_returns_empty(self, builder: ContextBuilder):
        """Request with no midgame fields produces empty string."""
        req = _make_request()
        result = builder._build_midgame_section(req)
        assert result == ""

    def test_lane_result_included(self, builder: ContextBuilder):
        """Lane result 'won' is capitalized and included."""
        req = _make_request(lane_result="won")
        result = builder._build_midgame_section(req)
        assert "Mid-Game Update" in result
        assert "Lane Result: Won" in result

    def test_lane_result_lost(self, builder: ContextBuilder):
        """Lane result 'lost' is capitalized correctly."""
        req = _make_request(lane_result="lost")
        result = builder._build_midgame_section(req)
        assert "Lane Result: Lost" in result

    def test_damage_profile_included(self, builder: ContextBuilder):
        """Damage profile percentages are formatted correctly."""
        req = _make_request(
            damage_profile={"physical": 60, "magical": 30, "pure": 10}
        )
        result = builder._build_midgame_section(req)
        assert "Mid-Game Update" in result
        assert "Damage Taken:" in result
        assert "Physical 60%" in result
        assert "Magical 30%" in result
        assert "Pure 10%" in result

    def test_enemy_items_spotted_title_case(self, builder: ContextBuilder):
        """Enemy items use title case with underscores replaced by spaces."""
        req = _make_request(enemy_items_spotted=["black_king_bar", "blink"])
        result = builder._build_midgame_section(req)
        assert "Mid-Game Update" in result
        assert "Enemy Items Spotted:" in result
        assert "Black King Bar" in result
        assert "Blink" in result

    def test_all_midgame_fields_combined(self, builder: ContextBuilder):
        """All midgame fields present in output when all set."""
        req = _make_request(
            lane_result="even",
            damage_profile={"physical": 50, "magical": 50, "pure": 0},
            enemy_items_spotted=["force_staff"],
        )
        result = builder._build_midgame_section(req)
        assert "Lane Result: Even" in result
        assert "Physical 50%" in result
        assert "Force Staff" in result


# ---------------------------------------------------------------------------
# Full build method (needs DB, mock external services)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _build_ally_lines (async, needs DB + mocked popularity)
# ---------------------------------------------------------------------------


class TestBuildAllyLines:
    @pytest.mark.asyncio
    async def test_empty_allies_returns_empty_string(
        self, builder: ContextBuilder, test_db_session
    ):
        """Empty allies list returns empty string."""
        result = await builder._build_ally_lines([], test_db_session)
        assert result == ""

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_allies_returns_hero_names(
        self, mock_popularity, builder: ContextBuilder, test_db_session
    ):
        """Two allies (Axe=2, Crystal Maiden=3) appear by name in output."""
        result = await builder._build_ally_lines([2, 3], test_db_session)
        assert "Axe" in result
        assert "Crystal Maiden" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value={
            "early_game_items": {"48": 500, "50": 400, "99": 300, "29": 200, "36": 150},
            "mid_game_items": {"1": 600, "102": 500},
        },
    )
    async def test_allies_include_popular_items(
        self, mock_popularity, builder: ContextBuilder, test_db_session
    ):
        """Ally lines include top popular items when popularity data available."""
        result = await builder._build_ally_lines([2], test_db_session)
        assert "Axe" in result
        assert "typical builds include" in result
        # Blink Dagger has highest count (600) across all phases
        assert "Blink Dagger" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_ally_no_popularity_shows_fallback(
        self, mock_popularity, builder: ContextBuilder, test_db_session
    ):
        """When popularity fetch returns None, ally line shows fallback text."""
        result = await builder._build_ally_lines([2], test_db_session)
        assert "Axe" in result
        assert "no typical build data available" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_with_allies_includes_section(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() with allies includes '## Allied Heroes' section."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(allies=[2, 3])
        result = await cb.build(req, [], test_db_session)
        assert "## Allied Heroes" in result
        assert "Axe" in result
        assert "Crystal Maiden" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_without_allies_no_section(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() with empty allies does NOT include 'Allied Heroes'."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(allies=[])
        result = await cb.build(req, [], test_db_session)
        assert "Allied Heroes" not in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_allied_heroes_section_ordering(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Allied Heroes appears after '## Your Hero' and before '## Lane Opponents'."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(allies=[2], lane_opponents=[3])
        result = await cb.build(req, [], test_db_session)

        hero_idx = result.index("## Your Hero")
        ally_idx = result.index("## Allied Heroes")
        opponent_idx = result.index("## Lane Opponents")

        assert hero_idx < ally_idx < opponent_idx


# ---------------------------------------------------------------------------
# Integration: full ally-aware pipeline (async, needs DB + mocked services)
# ---------------------------------------------------------------------------


class TestAllyIntegration:
    """Integration tests for ally context flowing through the full build pipeline."""

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_with_allies_and_popularity(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build with allies and popularity data shows ally names and items."""

        async def popularity_side_effect(hero_id, db, client):
            if hero_id == 2:  # Axe
                return {
                    "early_game_items": {"50": 500, "48": 400},
                    "mid_game_items": {"1": 300},
                }
            return None  # Player hero or other allies

        mock_popularity.side_effect = popularity_side_effect

        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(allies=[2])  # Axe as ally
        result = await cb.build(req, [], test_db_session)

        assert "Allied Heroes" in result
        assert "Axe" in result
        # Axe has popularity data, so should show typical builds
        assert "typical builds include" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_with_allies_no_popularity(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build with allies but no popularity shows fallback text."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(allies=[3])  # Crystal Maiden as ally
        result = await cb.build(req, [], test_db_session)

        assert "Allied Heroes" in result
        assert "Crystal Maiden" in result
        assert "no typical build data available" in result


# ---------------------------------------------------------------------------
# System prompt smoke tests (confirm ally coordination rules exist)
# ---------------------------------------------------------------------------


class TestSystemPromptAllyRules:
    """Smoke tests confirming system prompt contains ally coordination rules."""

    def test_system_prompt_has_team_coordination(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "## Team Coordination" in SYSTEM_PROMPT

    def test_system_prompt_has_aura_dedup_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "Aura and utility deduplication" in SYSTEM_PROMPT

    def test_system_prompt_has_combo_awareness_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "Combo and setup awareness" in SYSTEM_PROMPT

    def test_system_prompt_has_gap_filling_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "Team role gap filling" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Full build method (needs DB, mock external services)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Neutral Items Catalog tests
# ---------------------------------------------------------------------------


class TestNeutralCatalog:
    def test_neutral_catalog_groups_by_tier(self, builder: ContextBuilder):
        """Neutral catalog groups items by tier (reads from DataCache)."""
        result = builder._build_neutral_catalog()
        # Test DB has neutral items in tier 1, 3, and 5
        assert "T1:" in result
        assert "T3:" in result
        assert "Mysterious Hat" in result
        assert "Chipped Vest" in result
        assert "Psychic Headband" in result

    def test_neutral_catalog_empty_when_cache_empty(self):
        """Empty DataCache returns empty neutral catalog."""
        from data.cache import DataCache
        empty_cache = DataCache()
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=empty_cache)
        result = cb._build_neutral_catalog()
        assert result == ""

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_includes_neutral_catalog_section(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() with neutral items includes '## Neutral Items Catalog' section."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request()
        result = await cb.build(req, [], test_db_session)
        assert "## Neutral Items Catalog" in result
        assert "Mysterious Hat" in result


# ---------------------------------------------------------------------------
# System prompt neutral items smoke tests
# ---------------------------------------------------------------------------


class TestSystemPromptNeutralRules:
    """Smoke tests confirming system prompt contains neutral item rules."""

    def test_system_prompt_has_neutral_items_section(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "## Neutral Items" in SYSTEM_PROMPT

    def test_system_prompt_has_rank_by_hero_synergy(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "Rank by hero synergy" in SYSTEM_PROMPT

    def test_system_prompt_has_build_path_interaction(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "Build-path interaction" in SYSTEM_PROMPT

    def test_system_prompt_has_neutral_items_field(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "neutral_items" in SYSTEM_PROMPT


class TestBuildFull:
    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_contains_hero_and_game_state(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Build output contains hero name, role, playstyle, side, and lane."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request()
        result = await cb.build(req, [], test_db_session)

        assert "Anti-Mage" in result
        assert "Pos 1" in result
        assert "Farm-first" in result
        assert "radiant" in result
        assert "safe" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_includes_opponent_section(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Build output includes Lane Opponents section when opponents provided."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request(lane_opponents=[2])  # Axe
        result = await cb.build(req, [], test_db_session)

        assert "Lane Opponents" in result
        assert "Axe" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_includes_available_items(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Build output includes Available Items section with item catalog from cache."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        req = _make_request()
        result = await cb.build(req, [], test_db_session)

        assert "Available Items" in result
        # Power Treads is in test DB and not a recipe/neutral, so should appear
        assert "Power Treads" in result
        assert "1400g" in result

    @pytest.mark.asyncio
    @patch(
        "engine.context_builder.get_hero_item_popularity",
        new_callable=AsyncMock,
        return_value=None,
    )
    @patch(
        "engine.context_builder.get_or_fetch_matchup",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_build_includes_rules_section(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Build output includes Already Recommended section when rules provided."""
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
        rules = [
            RuleResult(
                item_id=36,
                item_name="Magic Stick",
                reasoning="Bristleback spams quills",
                phase="laning",
                priority="core",
            ),
        ]
        req = _make_request()
        result = await cb.build(req, rules, test_db_session)

        assert "Already Recommended" in result
        assert "Magic Stick" in result


# ---------------------------------------------------------------------------
# Ability annotations in opponent lines (D-06, D-07)
# ---------------------------------------------------------------------------


class TestAbilityAnnotations:
    """Tests for ability annotations in opponent lines (D-06, D-07)."""

    def test_counter_relevant_abilities_wd(self, builder):
        """Witch Doctor ability annotations include channeled and BKB-pierce."""
        result = builder._get_counter_relevant_abilities(30)
        assert "Death Ward" in result
        assert "channeled" in result
        assert "BKB-pierce" in result

    def test_counter_relevant_abilities_wd_maledict(self, builder):
        """Witch Doctor Maledict shows as undispellable."""
        result = builder._get_counter_relevant_abilities(30)
        assert "Maledict" in result
        assert "undispellable" in result

    def test_counter_relevant_abilities_am(self, builder):
        """Anti-Mage ability annotations include Mana Break (passive)."""
        result = builder._get_counter_relevant_abilities(1)
        assert "Mana Break" in result
        assert "passive" in result

    def test_counter_relevant_abilities_am_excludes_blink(self, builder):
        """Blink has no counter-relevant properties and is excluded."""
        result = builder._get_counter_relevant_abilities(1)
        # Blink should not appear (no channeled, no passive, no BKB-pierce, no undispellable)
        assert "Blink" not in result

    def test_counter_relevant_abilities_unknown_hero(self, builder):
        """Hero with no ability data returns empty string."""
        result = builder._get_counter_relevant_abilities(9999)
        assert result == ""

    def test_counter_relevant_abilities_cm(self, builder):
        """Crystal Maiden shows Freezing Field as channeled."""
        result = builder._get_counter_relevant_abilities(3)
        assert "Freezing Field" in result
        assert "channeled" in result

    @pytest.mark.asyncio
    async def test_opponent_lines_include_threats(self, builder, test_db_session):
        """Opponent lines include Threats annotation for WD."""
        with patch(
            "engine.context_builder.get_or_fetch_matchup",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await builder._build_opponent_lines(1, [30], test_db_session)
        assert "Threats:" in result
        assert "Death Ward" in result

    @pytest.mark.asyncio
    async def test_opponent_lines_no_threats_for_hero_without_abilities(self, builder, test_db_session):
        """Opponent lines omit Threats line for hero without counter-relevant abilities."""
        # Use a hero ID that exists but has no abilities with counter-relevant props
        # Hero 9999 has no ability data at all
        with patch(
            "engine.context_builder.get_or_fetch_matchup",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await builder._build_opponent_lines(1, [9999], test_db_session)
        assert "Threats:" not in result
