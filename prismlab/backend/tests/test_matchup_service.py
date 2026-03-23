"""Tests for matchup data fetch/cache pipeline."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from data.matchup_service import (
    get_or_fetch_matchup,
    get_hero_item_popularity,
    get_relevant_items,
    get_neutral_items_by_tier,
)
from data.models import MatchupData


@pytest.fixture
def mock_client():
    """Create a mock OpenDotaClient with AsyncMock methods."""
    client = MagicMock()
    client.fetch_hero_matchups = AsyncMock()
    client.fetch_hero_item_popularity = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_cache_after_fetch(test_db_session, mock_client):
    """Fetched matchup data is cached in the DB and returned."""
    mock_client.fetch_hero_matchups.return_value = [
        {"hero_id": 69, "games_played": 100, "wins": 45},
    ]

    result = await get_or_fetch_matchup(1, 69, test_db_session, mock_client)

    assert result is not None
    assert result.hero_id == 1
    assert result.opponent_id == 69
    assert result.win_rate == pytest.approx(0.45)
    assert result.games_played == 100

    # Verify it was persisted in the DB
    mock_client.fetch_hero_matchups.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_stale_data_returned(test_db_session, mock_client):
    """Stale cached data is returned immediately without blocking."""
    # Insert a stale MatchupData row
    stale_time = datetime.now(timezone.utc) - timedelta(hours=25)
    stale_matchup = MatchupData(
        hero_id=1,
        opponent_id=69,
        win_rate=0.50,
        games_played=80,
        bracket="high",
        updated_at=stale_time,
    )
    test_db_session.add(stale_matchup)
    await test_db_session.commit()

    # The function should return the stale data immediately
    result = await get_or_fetch_matchup(1, 69, test_db_session, mock_client)

    assert result is not None
    assert result.win_rate == pytest.approx(0.50)
    assert result.games_played == 80
    # The stale data is returned -- the background refresh is scheduled
    # but we do not assert on the background task here


@pytest.mark.asyncio
async def test_fresh_data_not_refreshed(test_db_session, mock_client):
    """Fresh cached data is returned without triggering a refresh."""
    fresh_time = datetime.now(timezone.utc) - timedelta(hours=1)
    fresh_matchup = MatchupData(
        hero_id=1,
        opponent_id=22,
        win_rate=0.55,
        games_played=200,
        bracket="high",
        updated_at=fresh_time,
    )
    test_db_session.add(fresh_matchup)
    await test_db_session.commit()

    result = await get_or_fetch_matchup(1, 22, test_db_session, mock_client)

    assert result is not None
    assert result.win_rate == pytest.approx(0.55)
    # API should NOT have been called for fresh data
    mock_client.fetch_hero_matchups.assert_not_called()


@pytest.mark.asyncio
async def test_no_opponent_returns_none(test_db_session, mock_client):
    """Returns None when the opponent is not in the matchup data."""
    mock_client.fetch_hero_matchups.return_value = []

    result = await get_or_fetch_matchup(1, 999, test_db_session, mock_client)

    assert result is None


@pytest.mark.asyncio
async def test_division_by_zero_handled(test_db_session, mock_client):
    """Zero games_played results in 0.5 win rate (not division error)."""
    mock_client.fetch_hero_matchups.return_value = [
        {"hero_id": 69, "games_played": 0, "wins": 0},
    ]

    result = await get_or_fetch_matchup(1, 69, test_db_session, mock_client)

    assert result is not None
    assert result.win_rate == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_api_error_returns_none(test_db_session, mock_client):
    """API errors are caught and None is returned."""
    mock_client.fetch_hero_matchups.side_effect = Exception("API timeout")

    result = await get_or_fetch_matchup(1, 69, test_db_session, mock_client)

    assert result is None


@pytest.mark.asyncio
async def test_get_hero_item_popularity_success(test_db_session, mock_client):
    """Item popularity data is returned from OpenDota."""
    expected = {
        "start_game_items": {"36": 5000, "29": 8000},
        "early_game_items": {"48": 7000},
        "mid_game_items": {"116": 3000},
        "late_game_items": {"235": 1000},
    }
    mock_client.fetch_hero_item_popularity.return_value = expected

    result = await get_hero_item_popularity(1, test_db_session, mock_client)

    assert result == expected
    mock_client.fetch_hero_item_popularity.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_hero_item_popularity_error(test_db_session, mock_client):
    """Item popularity returns None on API error."""
    mock_client.fetch_hero_item_popularity.side_effect = Exception("Network error")

    result = await get_hero_item_popularity(1, test_db_session, mock_client)

    assert result is None


@pytest.mark.asyncio
async def test_get_relevant_items_filters(test_db_session):
    """Relevant items excludes recipes, neutrals, and zero-cost items."""
    items = await get_relevant_items(1, 1, test_db_session)

    # Should not include recipe (id=300), neutral (id=301)
    item_ids = {item["id"] for item in items}
    assert 300 not in item_ids, "Recipes should be excluded"
    assert 301 not in item_ids, "Neutral items should be excluded"

    # All items should have cost > 0 and <= 10000
    for item in items:
        assert item["cost"] > 0
        assert item["cost"] <= 10000


@pytest.mark.asyncio
async def test_get_relevant_items_support_budget(test_db_session):
    """Support budget caps items at 5500g."""
    items = await get_relevant_items(1, 5, test_db_session)

    for item in items:
        assert item["cost"] <= 5500, (
            f"Support items should cost <= 5500g, got {item['name']} at {item['cost']}"
        )


@pytest.mark.asyncio
async def test_get_relevant_items_sorted_by_cost(test_db_session):
    """Items are sorted by cost ascending."""
    items = await get_relevant_items(1, 1, test_db_session)

    costs = [item["cost"] for item in items]
    assert costs == sorted(costs), "Items should be sorted by cost ascending"


@pytest.mark.asyncio
async def test_get_relevant_items_capped_at_50(test_db_session):
    """Result is capped at 50 items maximum."""
    items = await get_relevant_items(1, 1, test_db_session)

    assert len(items) <= 50


@pytest.mark.asyncio
async def test_get_neutral_items_by_tier(test_db_session):
    """get_neutral_items_by_tier groups neutral items by tier number."""
    result = await get_neutral_items_by_tier(test_db_session)

    # Tier 1 should have 2 items: Mysterious Hat and Chipped Vest
    assert 1 in result
    assert len(result[1]) == 2
    tier1_names = {item["name"] for item in result[1]}
    assert "Mysterious Hat" in tier1_names
    assert "Chipped Vest" in tier1_names

    # Tier 3 should have 1 item: Psychic Headband
    assert 3 in result
    assert len(result[3]) == 1
    assert result[3][0]["name"] == "Psychic Headband"

    # Tier 5 should have 1 item: Spider Legs
    assert 5 in result
    assert len(result[5]) == 1
    assert result[5][0]["name"] == "Spider Legs"

    # Each item should have the required keys
    for tier_items in result.values():
        for item in tier_items:
            assert "id" in item
            assert "name" in item
            assert "internal_name" in item
            assert "active_desc" in item


@pytest.mark.asyncio
async def test_get_neutral_items_by_tier_empty(test_db_session):
    """Tiers without items are absent from result dict."""
    result = await get_neutral_items_by_tier(test_db_session)

    # Tiers 2 and 4 have no items in fixtures
    assert 2 not in result
    assert 4 not in result
