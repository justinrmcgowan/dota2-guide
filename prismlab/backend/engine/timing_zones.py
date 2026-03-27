"""Timing zone classification utility.

Converts raw TimingBucket data from DataCache into good/on-track/late zones
with aggregate win rates, urgency detection, and pre-formatted display strings.

Consumed by: context_builder (Claude user message), recommender (API response enrichment).
"""

from __future__ import annotations

from typing import Any

from data.cache import TimingBucket


def classify_timing_zones(
    buckets: list[TimingBucket],
) -> dict[str, Any] | None:
    """Classify timing buckets into good/on-track/late zones.

    Returns zone ranges, aggregate win rates, and urgency flag.
    Returns None if insufficient data (empty, <2 buckets, or <50 total games).

    Zone classification:
    - good: win_rate >= peak_wr - 0.02 (within 2% of peak)
    - ontrack: win_rate >= weighted_avg_wr (above average)
    - late: win_rate < weighted_avg_wr (below average)

    Urgency: is_urgent if good_avg_wr - late_avg_wr > 0.10 (10pp threshold)
    """
    if not buckets or len(buckets) < 2:
        return None

    total_games = sum(b.games for b in buckets)
    if total_games < 50:
        return None

    # Weighted average and peak win rate
    weighted_avg_wr = sum(b.win_rate * b.games for b in buckets) / total_games
    peak_wr = max(b.win_rate for b in buckets)

    good_buckets: list[TimingBucket] = []
    ontrack_buckets: list[TimingBucket] = []
    late_buckets: list[TimingBucket] = []

    for b in buckets:
        if b.win_rate >= peak_wr - 0.02:
            good_buckets.append(b)
        elif b.win_rate >= weighted_avg_wr:
            ontrack_buckets.append(b)
        else:
            late_buckets.append(b)

    # Aggregate win rates per zone (weighted by games)
    good_avg_wr = (
        sum(b.win_rate * b.games for b in good_buckets)
        / sum(b.games for b in good_buckets)
    ) if good_buckets else 0.0

    ontrack_avg_wr = (
        sum(b.win_rate * b.games for b in ontrack_buckets)
        / sum(b.games for b in ontrack_buckets)
    ) if ontrack_buckets else 0.0

    late_avg_wr = (
        sum(b.win_rate * b.games for b in late_buckets)
        / sum(b.games for b in late_buckets)
    ) if late_buckets else 0.0

    is_urgent = (good_avg_wr - late_avg_wr) > 0.10

    return {
        "good_range": _format_time_range(good_buckets, zone="good"),
        "ontrack_range": _format_time_range(ontrack_buckets, zone="ontrack"),
        "late_range": _format_time_range(late_buckets, zone="late"),
        "good_win_rate": round(good_avg_wr, 3),
        "ontrack_win_rate": round(ontrack_avg_wr, 3),
        "late_win_rate": round(late_avg_wr, 3),
        "is_urgent": is_urgent,
        "confidence": _aggregate_confidence(buckets),
        "total_games": total_games,
        "buckets_classified": [
            {
                "time": b.time,
                "games": b.games,
                "win_rate": round(b.win_rate, 3),
                "confidence": b.confidence,
                "zone": (
                    "good" if b in good_buckets else
                    "ontrack" if b in ontrack_buckets else
                    "late"
                ),
            }
            for b in buckets
        ],
    }


def _format_time_range(
    buckets: list[TimingBucket], zone: str = "ontrack"
) -> str:
    """Format a list of buckets into a display time range.

    CRITICAL: TimingBucket.time is in SECONDS. All display strings
    must convert to minutes (divide by 60).

    Zone formatting:
    - good (lowest times): "< {max_time} min"
    - late (highest times): "> {min_time} min"
    - ontrack (middle): "{min_time}-{max_time} min"
    - single bucket: "~{time} min"
    """
    if not buckets:
        return ""

    min_time = min(b.time for b in buckets) // 60
    max_time = max(b.time for b in buckets) // 60

    if min_time == max_time:
        return f"~{min_time} min"

    if zone == "good":
        return f"< {max_time} min"
    elif zone == "late":
        return f"> {min_time} min"
    else:
        return f"{min_time}-{max_time} min"


def _aggregate_confidence(buckets: list[TimingBucket]) -> str:
    """Aggregate confidence across all buckets (weakest wins).

    "weak" if any bucket is weak, "moderate" if any is moderate, else "strong".
    """
    confidences = {b.confidence for b in buckets}
    if "weak" in confidences:
        return "weak"
    if "moderate" in confidences:
        return "moderate"
    return "strong"
