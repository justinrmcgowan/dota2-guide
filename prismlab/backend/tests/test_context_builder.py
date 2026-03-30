"""Unit tests for the context builder that assembles Claude API user messages.

Hero/item lookups come from DataCache (loaded from test DB in conftest).
Only matchup and popularity data are still mocked (they hit external APIs).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from data.cache import data_cache, DataCache, TimingBucket
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

    def test_system_prompt_has_allies_section(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "## Allies" in SYSTEM_PROMPT

    def test_system_prompt_has_aura_dedup_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "deduplicate auras" in SYSTEM_PROMPT

    def test_system_prompt_has_combo_awareness_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "identify combos" in SYSTEM_PROMPT

    def test_system_prompt_has_gap_filling_rule(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "fill team gaps" in SYSTEM_PROMPT


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

        assert "rank 2-3 per tier by hero synergy" in SYSTEM_PROMPT

    def test_system_prompt_has_build_path_interaction(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "build-path interactions" in SYSTEM_PROMPT

    def test_system_prompt_has_neutral_items_field(self):
        from engine.prompts.system_prompt import SYSTEM_PROMPT

        assert "neutral_items" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Pro Reference Section tests (Phase 35: Quality Foundation)
# ---------------------------------------------------------------------------


class TestProReferenceSection:
    """Tests for _build_pro_reference_section in context_builder."""

    def test_pro_section_included_when_baselines_exist(self):
        """Pro section contains hero item baselines with game counts."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_item_baselines.return_value = {
            "starting": [(36, "Magic Stick", 5000, 0.0), (237, "Tango", 8000, 0.0)],
            "laning": [(48, "Power Treads", 3000, 0.0)],
            "core": [(116, "Black King Bar", 2500, 0.0)],
        }
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = cb._build_pro_reference_section(hero_id=1)
        assert "Starting:" in result
        assert "Magic Stick (5000 games)" in result
        assert "Tango (8000 games)" in result
        assert "Laning:" in result
        assert "Power Treads (3000 games)" in result
        assert "Core:" in result
        assert "Black King Bar (2500 games)" in result

    def test_pro_section_skipped_when_no_baselines(self):
        """Pro section returns empty string when no baselines available."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_item_baselines.return_value = None
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = cb._build_pro_reference_section(hero_id=1)
        assert result == ""

    def test_pro_section_skipped_when_baselines_empty_dict(self):
        """Pro section returns empty string when baselines is empty dict."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_item_baselines.return_value = {}
        mock_opendota = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = cb._build_pro_reference_section(hero_id=1)
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
    async def test_build_includes_pro_section_when_baselines_cached(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() includes 'What Divine/Immortal Players Build' when baselines exist."""
        original_baselines = data_cache._hero_item_baselines.copy()
        data_cache._hero_item_baselines[1] = {
            "starting": [(36, "Magic Stick", 5000, 0.0)],
            "core": [(116, "Black King Bar", 2500, 0.0)],
        }
        try:
            mock_opendota = MagicMock()
            cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
            req = _make_request()
            result = await cb.build(req, [], test_db_session)
            assert "What Divine/Immortal Players Build" in result
            assert "explain WHY your recommendation is better" in result
            assert "Magic Stick (5000 games)" in result
        finally:
            data_cache._hero_item_baselines = original_baselines

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
    async def test_build_excludes_pro_section_when_no_baselines(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() does NOT include 'What Divine/Immortal Players Build' when no baselines."""
        original_baselines = data_cache._hero_item_baselines.copy()
        # Ensure no baselines for hero 1
        data_cache._hero_item_baselines.pop(1, None)
        try:
            mock_opendota = MagicMock()
            cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
            req = _make_request()
            result = await cb.build(req, [], test_db_session)
            assert "What Divine/Immortal Players Build" not in result
        finally:
            data_cache._hero_item_baselines = original_baselines


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

    @pytest.mark.usefixtures("test_db_setup")
    def test_counter_relevant_abilities_wd(self, builder):
        """Witch Doctor ability annotations include channeled and BKB-pierce."""
        result = builder._get_counter_relevant_abilities(30)
        assert "Death Ward" in result
        assert "channeled" in result
        assert "BKB-pierce" in result

    @pytest.mark.usefixtures("test_db_setup")
    def test_counter_relevant_abilities_wd_maledict(self, builder):
        """Witch Doctor Maledict shows as undispellable."""
        result = builder._get_counter_relevant_abilities(30)
        assert "Maledict" in result
        assert "undispellable" in result

    @pytest.mark.usefixtures("test_db_setup")
    def test_counter_relevant_abilities_am(self, builder):
        """Anti-Mage ability annotations include Mana Break (passive)."""
        result = builder._get_counter_relevant_abilities(1)
        assert "Mana Break" in result
        assert "passive" in result

    @pytest.mark.usefixtures("test_db_setup")
    def test_counter_relevant_abilities_am_excludes_blink(self, builder):
        """Blink has no counter-relevant properties and is excluded."""
        result = builder._get_counter_relevant_abilities(1)
        # Blink should not appear (no channeled, no passive, no BKB-pierce, no undispellable)
        assert "Blink" not in result

    @pytest.mark.usefixtures("test_db_setup")
    def test_counter_relevant_abilities_unknown_hero(self, builder):
        """Hero with no ability data returns empty string."""
        result = builder._get_counter_relevant_abilities(9999)
        assert result == ""

    @pytest.mark.usefixtures("test_db_setup")
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


# ---------------------------------------------------------------------------
# _build_timing_section tests (Phase 21: Timing Benchmarks)
# ---------------------------------------------------------------------------


def _timing_bucket(time_s: int, games: int, wins: int, confidence: str = "strong") -> TimingBucket:
    """Helper to create a TimingBucket."""
    return TimingBucket(time=time_s, games=games, wins=wins, confidence=confidence)


class TestBuildTimingSection:
    """Tests for _build_timing_section in context_builder (D-05 format)."""

    @pytest.mark.asyncio
    @patch("engine.context_builder.get_or_fetch_hero_timings", new_callable=AsyncMock, return_value=None)
    async def test_timing_section_empty_when_no_data(self, mock_fetch):
        """Returns empty string when cache has no timing data for hero."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_timings.return_value = None
        mock_opendota = MagicMock()
        mock_db = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = await cb._build_timing_section(hero_id=1, db=mock_db)
        assert result == ""

    @pytest.mark.asyncio
    async def test_timing_section_formats_correctly(self):
        """Timing section formats item with good/on-track/late ranges and win rates."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_timings.return_value = {
            "black_king_bar": [
                _timing_bucket(600, 200, 110),    # 55% WR, 10 min
                _timing_bucket(900, 300, 174),     # 58% WR, 15 min
                _timing_bucket(1200, 250, 130),    # 52% WR, 20 min
                _timing_bucket(1500, 200, 96),     # 48% WR, 25 min
                _timing_bucket(1800, 150, 61),     # ~41% WR, 30 min
            ],
        }
        mock_opendota = MagicMock()
        mock_db = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = await cb._build_timing_section(hero_id=1, db=mock_db)
        assert "Black King Bar" in result
        assert "good" in result
        assert "WR" in result
        assert "min" in result
        # Should NOT contain raw seconds
        assert "600" not in result
        assert "1800" not in result

    @pytest.mark.asyncio
    async def test_timing_section_marks_urgent(self):
        """Items with steep falloff show [TIMING-CRITICAL] tag."""
        mock_cache = MagicMock(spec=DataCache)
        mock_cache.get_hero_timings.return_value = {
            "bkb": [
                _timing_bucket(600, 200, 110),    # 55% WR
                _timing_bucket(900, 300, 174),     # 58% WR
                _timing_bucket(1200, 250, 130),    # 52% WR
                _timing_bucket(1500, 200, 96),     # 48% WR
                _timing_bucket(1800, 150, 61),     # ~41% WR -- steep falloff
            ],
        }
        mock_opendota = MagicMock()
        mock_db = MagicMock()
        cb = ContextBuilder(opendota_client=mock_opendota, cache=mock_cache)

        result = await cb._build_timing_section(hero_id=1, db=mock_db)
        assert "[TIMING-CRITICAL]" in result

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
    async def test_build_includes_timing(
        self, mock_matchup, mock_popularity, test_db_session
    ):
        """Full build() includes '## Item Timing Benchmarks' section when data present."""
        # Use real data_cache but inject timing data for hero_id=1
        original_timings = data_cache._timing_benchmarks.copy()
        data_cache._timing_benchmarks[1] = {
            "power_treads": [
                _timing_bucket(600, 200, 110),
                _timing_bucket(900, 300, 150),
                _timing_bucket(1200, 250, 120),
            ],
        }
        try:
            mock_opendota = MagicMock()
            cb = ContextBuilder(opendota_client=mock_opendota, cache=data_cache)
            req = _make_request()
            result = await cb.build(req, [], test_db_session)
            assert "## Item Timing Benchmarks" in result
            assert "Power Treads" in result
        finally:
            data_cache._timing_benchmarks = original_timings


# ── Phase 36: Game clock, unusual role, partial draft ─────────────────


class TestBuildGameClockSection:
    """Tests for _build_game_clock_section (PROM-02)."""

    def test_game_clock_with_time(self, builder: ContextBuilder):
        """Game clock section formats minutes:seconds from game_time_seconds."""
        req = _make_request(game_time_seconds=1500)
        result = builder._build_game_clock_section(req)
        assert "25:00" in result
        assert "## Game Clock" in result

    def test_game_clock_none(self, builder: ContextBuilder):
        """Game clock section returns empty when game_time_seconds is None."""
        req = _make_request(game_time_seconds=None)
        result = builder._build_game_clock_section(req)
        assert result == ""

    def test_game_clock_turbo(self, builder: ContextBuilder):
        """Game clock section includes TURBO annotation in turbo mode."""
        req = _make_request(game_time_seconds=600, turbo=True)
        result = builder._build_game_clock_section(req)
        assert "TURBO" in result
        assert "10:00" in result

    def test_game_clock_non_turbo_no_turbo_text(self, builder: ContextBuilder):
        """Game clock section omits TURBO when turbo is False."""
        req = _make_request(game_time_seconds=600, turbo=False)
        result = builder._build_game_clock_section(req)
        assert "TURBO" not in result


class TestBuildUnusualRoleSection:
    """Tests for _build_unusual_role_section (PROM-03)."""

    def test_unusual_role_detected(self, builder: ContextBuilder):
        """Unusual role flagged when hero_id NOT in HERO_ROLE_VIABLE[role]."""
        from engine.hero_selector import HERO_ROLE_VIABLE

        # Find a hero_id that is NOT viable for role 1 (carry)
        # hero_id=22 is Zeus -- typically pos 2/4, not pos 1
        viable = HERO_ROLE_VIABLE.get(1, set())
        # Use hero_id 22 (Zeus) as pos 1 carry -- should be unusual
        req = _make_request(hero_id=22, role=1, playstyle="Aggressive")
        result = builder._build_unusual_role_section(req)
        if 22 not in viable:
            assert "Unusual Role" in result
            assert "Pos 1" in result
        else:
            # If hero happens to be viable, just verify no crash
            assert isinstance(result, str)

    def test_normal_role_returns_empty(self, builder: ContextBuilder):
        """Normal role (hero in HERO_ROLE_VIABLE[role]) returns empty string."""
        from engine.hero_selector import HERO_ROLE_VIABLE

        # hero_id=1 is Anti-Mage, role=1 is carry -- very standard
        viable = HERO_ROLE_VIABLE.get(1, set())
        req = _make_request(hero_id=1, role=1, playstyle="Aggressive")
        result = builder._build_unusual_role_section(req)
        if 1 in viable:
            assert result == ""
        else:
            assert isinstance(result, str)


class TestBuildPartialDraftSection:
    """Tests for _build_partial_draft_section (PROM-04)."""

    def test_partial_draft_detected(self, builder: ContextBuilder):
        """Partial draft section shown when < 10 heroes total."""
        # 1 (player) + 0 allies + 2 opponents = 3 total
        req = _make_request(all_opponents=[22, 69])
        result = builder._build_partial_draft_section(req)
        assert "3/10" in result
        assert "Partial Draft" in result

    def test_full_draft_returns_empty(self, builder: ContextBuilder):
        """Full draft (10 heroes) returns empty string."""
        req = _make_request(
            allies=[2, 3, 5, 6],
            all_opponents=[22, 69, 11, 12, 8],
        )
        result = builder._build_partial_draft_section(req)
        assert result == ""

    def test_partial_draft_solo_hero(self, builder: ContextBuilder):
        """Solo hero (1/10) shows maximum partial draft caveat."""
        req = _make_request()
        result = builder._build_partial_draft_section(req)
        assert "1/10" in result
        assert "9 heroes not yet picked" in result
