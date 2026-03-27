"""Tests for DataCache ability and timing extensions (Phase 19).

These tests verify DATA-01, DATA-02, DATA-03 cache layer behavior.
Tests are written BEFORE implementation (Nyquist rule) and will fail
until Plan 02 extends DataCache with ability and timing support.
"""
import pytest
from data.cache import data_cache, AbilityCached, TimingBucket


class TestAbilityCachedDataclass:
    """Test AbilityCached frozen dataclass properties."""

    def test_ability_cached_properties(self):
        """DATA-01: AbilityCached exposes is_channeled and is_passive."""
        channeled = AbilityCached(
            key="crystal_maiden_freezing_field",
            dname="Freezing Field",
            behavior=("No Target", "Channeled"),
            bkbpierce=False,
            dispellable=None,
            dmg_type="Magical",
        )
        assert channeled.is_channeled is True
        assert channeled.is_passive is False

        passive = AbilityCached(
            key="antimage_mana_break",
            dname="Mana Break",
            behavior=("Passive",),
            bkbpierce=False,
            dispellable=None,
            dmg_type="Physical",
        )
        assert passive.is_channeled is False
        assert passive.is_passive is True

    def test_ability_cached_is_frozen(self):
        """AbilityCached instances are immutable."""
        ability = AbilityCached(
            key="test", dname="Test", behavior=(),
            bkbpierce=False, dispellable=None, dmg_type=None,
        )
        with pytest.raises(AttributeError):
            ability.key = "modified"


class TestTimingBucketDataclass:
    """Test TimingBucket frozen dataclass properties."""

    def test_timing_bucket_win_rate(self):
        """DATA-03: TimingBucket.win_rate computes correctly."""
        bucket = TimingBucket(time=900, games=277, wins=175, confidence="moderate")
        assert abs(bucket.win_rate - 175 / 277) < 0.001

    def test_timing_bucket_zero_games(self):
        """DATA-03: TimingBucket.win_rate returns 0.0 for zero games."""
        bucket = TimingBucket(time=900, games=0, wins=0, confidence="weak")
        assert bucket.win_rate == 0.0

    def test_timing_confidence_levels(self):
        """DATA-07: Confidence classification: strong >= 1000, moderate >= 200, weak < 200."""
        # These test that the confidence field is stored correctly
        # (classification happens during load, verified in test_ability_cache_load)
        strong = TimingBucket(time=900, games=1500, wins=800, confidence="strong")
        assert strong.confidence == "strong"
        moderate = TimingBucket(time=900, games=500, wins=250, confidence="moderate")
        assert moderate.confidence == "moderate"
        weak = TimingBucket(time=900, games=50, wins=25, confidence="weak")
        assert weak.confidence == "weak"


class TestDataCacheAbilityLoading:
    """Test DataCache ability data loading from DB."""

    @pytest.mark.asyncio
    async def test_ability_cache_load(self, test_db_setup):
        """DATA-01: After load(), DataCache contains ability metadata for seeded heroes."""
        abilities = data_cache.get_hero_abilities(1)  # Anti-Mage
        assert abilities is not None
        assert len(abilities) == 4  # 4 abilities seeded
        names = {a.dname for a in abilities}
        assert "Mana Break" in names
        assert "Mana Void" in names

    @pytest.mark.asyncio
    async def test_hero_ability_mapping(self, test_db_setup):
        """DATA-02: get_hero_abilities resolves hero_id to ability list."""
        abilities = data_cache.get_hero_abilities(3)  # Crystal Maiden
        assert abilities is not None
        assert len(abilities) == 3
        # Verify Freezing Field is channeled
        ff = next(a for a in abilities if a.key == "crystal_maiden_freezing_field")
        assert ff.is_channeled is True
        assert ff.dmg_type == "Magical"

    @pytest.mark.asyncio
    async def test_ability_behavior_normalization(self, test_db_setup):
        """DATA-01: behavior field normalized to tuple regardless of input type."""
        abilities = data_cache.get_hero_abilities(1)
        mana_break = next(a for a in abilities if a.key == "antimage_mana_break")
        # Input was string "Passive" -- should be tuple ("Passive",)
        assert isinstance(mana_break.behavior, tuple)
        assert mana_break.behavior == ("Passive",)

        blink = next(a for a in abilities if a.key == "antimage_blink")
        # Input was list ["Unit Target", "Point Target"] -- should be tuple
        assert isinstance(blink.behavior, tuple)
        assert blink.behavior == ("Unit Target", "Point Target")

    @pytest.mark.asyncio
    async def test_no_abilities_returns_none(self, test_db_setup):
        """get_hero_abilities returns None for hero without ability data."""
        abilities = data_cache.get_hero_abilities(2)  # Axe -- no ability data seeded
        assert abilities is None


class TestDataCacheTimingLoading:
    """Test DataCache timing benchmark loading from DB."""

    @pytest.mark.asyncio
    async def test_timing_cache_load(self, test_db_setup):
        """DATA-03: After load(), DataCache contains timing benchmarks for seeded heroes."""
        timings = data_cache.get_hero_timings(1)  # Anti-Mage
        assert timings is not None
        assert "bfury" in timings
        assert "manta" in timings

    @pytest.mark.asyncio
    async def test_timing_bucket_parsing(self, test_db_setup):
        """DATA-03: Timing buckets have games/wins as ints (not strings)."""
        timings = data_cache.get_hero_timings(1)
        bfury_buckets = timings["bfury"]
        assert len(bfury_buckets) == 4
        first = bfury_buckets[0]
        assert isinstance(first.games, int)
        assert isinstance(first.wins, int)
        assert first.time == 720
        assert first.games == 40
        assert first.wins == 30

    @pytest.mark.asyncio
    async def test_timing_confidence_assignment(self, test_db_setup):
        """DATA-07: Confidence assigned based on games count thresholds."""
        timings = data_cache.get_hero_timings(1)
        bfury_buckets = timings["bfury"]
        # 40 games -> weak, 277 games -> moderate, 284 -> moderate, 19 -> weak
        assert bfury_buckets[0].confidence == "weak"       # 40 games
        assert bfury_buckets[1].confidence == "moderate"    # 277 games
        assert bfury_buckets[2].confidence == "moderate"    # 284 games
        assert bfury_buckets[3].confidence == "weak"        # 19 games

    @pytest.mark.asyncio
    async def test_no_timings_returns_none(self, test_db_setup):
        """get_hero_timings returns None for hero without timing data."""
        timings = data_cache.get_hero_timings(2)  # Axe -- no timing data seeded
        assert timings is None


class TestDataCacheInternalNameLookup:
    """Test the new hero internal_name -> id reverse lookup."""

    @pytest.mark.asyncio
    async def test_hero_internal_name_to_id(self, test_db_setup):
        """DATA-02: Lookup hero ID by internal_name (needed for ability mapping)."""
        hero_id = data_cache.hero_internal_name_to_id("npc_dota_hero_antimage")
        assert hero_id == 1
        hero_id = data_cache.hero_internal_name_to_id("npc_dota_hero_crystal_maiden")
        assert hero_id == 3

    @pytest.mark.asyncio
    async def test_hero_internal_name_not_found(self, test_db_setup):
        """hero_internal_name_to_id returns None for unknown name."""
        assert data_cache.hero_internal_name_to_id("npc_dota_hero_nonexistent") is None


class TestDataCacheAtomicSwap:
    """Test that ability + timing data participates in atomic swap."""

    @pytest.mark.asyncio
    async def test_atomic_swap_coherence(self, test_db_setup):
        """Coherence: After load(), heroes, abilities, and timings are all populated."""
        # All caches should be populated after a single load()
        assert data_cache.get_hero(1) is not None           # heroes
        assert data_cache.get_hero_abilities(1) is not None  # abilities
        assert data_cache.get_hero_timings(1) is not None    # timings
        # Internal name lookup also populated
        assert data_cache.hero_internal_name_to_id("npc_dota_hero_antimage") == 1
