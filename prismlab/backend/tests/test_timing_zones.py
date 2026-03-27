"""Unit tests for timing zone classification utility.

Tests zone classification (good/on-track/late), urgency detection,
time range formatting, confidence aggregation, and ItemTimingResponse schema.
"""

import pytest
from data.cache import TimingBucket
from engine.timing_zones import classify_timing_zones
from engine.schemas import ItemTimingResponse


def _bucket(time_s: int, games: int, wins: int, confidence: str = "strong") -> TimingBucket:
    """Helper to create a TimingBucket with minimal args."""
    return TimingBucket(time=time_s, games=games, wins=wins, confidence=confidence)


class TestClassifyTimingZones:
    """Tests for classify_timing_zones utility function."""

    def test_returns_none_for_empty_bucket_list(self):
        """Empty bucket list returns None."""
        result = classify_timing_zones([])
        assert result is None

    def test_returns_none_for_single_bucket(self):
        """Fewer than 2 buckets returns None."""
        result = classify_timing_zones([_bucket(600, 100, 55)])
        assert result is None

    def test_returns_none_for_insufficient_games(self):
        """Total games < 50 returns None."""
        result = classify_timing_zones([
            _bucket(600, 20, 10),
            _bucket(900, 15, 8),
        ])
        assert result is None

    def test_classifies_buckets_into_zones(self):
        """Given 5 buckets with declining win rates, classifies good/ontrack/late.

        Buckets: 600s/55%, 900s/58%, 1200s/52%, 1500s/48%, 1800s/41%
        Peak WR = 0.58, so good threshold = 0.56
        Weighted avg = (55*200 + 58*300 + 52*250 + 48*200 + 41*150) / 1100 = ~51.5%
        Good: 900s (0.58 >= 0.56) -- 600s is 0.55, below 0.56 threshold
        On-track: 600s (0.55 >= ~0.515), 1200s (0.52 >= ~0.515)
        Late: 1500s (0.48 < ~0.515), 1800s (0.41 < ~0.515)
        """
        buckets = [
            _bucket(600, 200, 110),   # 55% WR
            _bucket(900, 300, 174),    # 58% WR
            _bucket(1200, 250, 130),   # 52% WR
            _bucket(1500, 200, 96),    # 48% WR
            _bucket(1800, 150, 61),    # ~40.67% WR
        ]
        result = classify_timing_zones(buckets)
        assert result is not None

        # Check zones are assigned in the classified buckets
        zone_map = {b["time"]: b["zone"] for b in result["buckets_classified"]}
        assert zone_map[900] == "good"     # 58% >= 56% (peak - 2%)
        assert zone_map[1500] == "late"    # 48% < weighted avg
        assert zone_map[1800] == "late"    # 41% < weighted avg

        # Good and late win rates should be populated
        assert result["good_win_rate"] > 0
        assert result["late_win_rate"] > 0
        assert result["total_games"] == 1100

    def test_urgency_detection_steep_falloff(self):
        """Good WR minus late WR > 10pp flags is_urgent=True.

        Good zone avg ~56.5%, late zone avg ~44.5% -> spread = 12pp > 10pp.
        """
        buckets = [
            _bucket(600, 200, 110),   # 55% WR
            _bucket(900, 300, 174),    # 58% WR
            _bucket(1200, 250, 130),   # 52% WR
            _bucket(1500, 200, 96),    # 48% WR
            _bucket(1800, 150, 61),    # ~40.67% WR
        ]
        result = classify_timing_zones(buckets)
        assert result is not None
        assert result["is_urgent"] is True

    def test_urgency_detection_small_spread(self):
        """Spread < 10pp yields is_urgent=False."""
        buckets = [
            _bucket(600, 200, 106),   # 53% WR
            _bucket(900, 300, 156),    # 52% WR
            _bucket(1200, 250, 125),   # 50% WR
            _bucket(1500, 200, 96),    # 48% WR
            _bucket(1800, 150, 72),    # 48% WR
        ]
        result = classify_timing_zones(buckets)
        assert result is not None
        assert result["is_urgent"] is False

    def test_time_ranges_formatted_as_minutes(self):
        """Time ranges convert from seconds to minutes."""
        buckets = [
            _bucket(600, 200, 110),   # 10 min
            _bucket(900, 300, 174),    # 15 min
            _bucket(1200, 250, 130),   # 20 min
            _bucket(1500, 200, 96),    # 25 min
            _bucket(1800, 150, 61),    # 30 min
        ]
        result = classify_timing_zones(buckets)
        assert result is not None

        # All time ranges should be in minutes, not seconds
        assert "min" in result["good_range"]
        assert "min" in result["late_range"]
        # Should not contain raw second values
        assert "600" not in result["good_range"]
        assert "1800" not in result["late_range"]

    def test_confidence_aggregation_all_strong(self):
        """All strong buckets produce strong aggregate confidence."""
        buckets = [
            _bucket(600, 200, 110, "strong"),
            _bucket(900, 300, 174, "strong"),
            _bucket(1200, 250, 130, "strong"),
        ]
        result = classify_timing_zones(buckets)
        assert result is not None
        assert result["confidence"] == "strong"

    def test_confidence_aggregation_any_moderate(self):
        """Any moderate bucket produces moderate aggregate confidence."""
        buckets = [
            _bucket(600, 200, 110, "strong"),
            _bucket(900, 300, 174, "moderate"),
            _bucket(1200, 250, 130, "strong"),
        ]
        result = classify_timing_zones(buckets)
        assert result is not None
        assert result["confidence"] == "moderate"

    def test_confidence_aggregation_any_weak(self):
        """Any weak bucket produces weak aggregate confidence (weakest wins)."""
        buckets = [
            _bucket(600, 200, 110, "strong"),
            _bucket(900, 300, 174, "moderate"),
            _bucket(1200, 250, 130, "weak"),
        ]
        result = classify_timing_zones(buckets)
        assert result is not None
        assert result["confidence"] == "weak"


class TestItemTimingResponseSchema:
    """Tests for ItemTimingResponse Pydantic model."""

    def test_validates_with_all_required_fields(self):
        """ItemTimingResponse validates with all required fields."""
        response = ItemTimingResponse(
            item_name="black_king_bar",
            buckets=[
                {"time": 600, "games": 200, "win_rate": 0.55, "confidence": "strong", "zone": "good"},
                {"time": 900, "games": 300, "win_rate": 0.48, "confidence": "strong", "zone": "late"},
            ],
            is_urgent=True,
            good_range="< 15 min",
            ontrack_range="15-20 min",
            late_range="> 20 min",
            good_win_rate=0.565,
            ontrack_win_rate=0.52,
            late_win_rate=0.445,
            confidence="strong",
            total_games=1100,
        )
        assert response.item_name == "black_king_bar"
        assert response.is_urgent is True
        assert response.confidence == "strong"
        assert len(response.buckets) == 2
