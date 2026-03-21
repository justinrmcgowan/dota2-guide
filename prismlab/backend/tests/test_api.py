import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_health(test_client):
    """Health endpoint should return 200 with status ok."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_list_heroes(test_client):
    """GET /api/heroes should return all seeded heroes."""
    response = await test_client.get("/api/heroes")
    assert response.status_code == 200
    heroes = response.json()
    assert isinstance(heroes, list)
    assert len(heroes) >= 2
    for hero in heroes:
        assert "id" in hero
        assert "localized_name" in hero
        assert "primary_attr" in hero


@pytest.mark.asyncio
async def test_get_hero(test_client):
    """GET /api/heroes/1 should return Anti-Mage."""
    response = await test_client.get("/api/heroes/1")
    assert response.status_code == 200
    hero = response.json()
    assert hero["id"] == 1


@pytest.mark.asyncio
async def test_get_hero_not_found(test_client):
    """GET /api/heroes/99999 should return 404."""
    response = await test_client.get("/api/heroes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_items(test_client):
    """GET /api/items should return all seeded items."""
    response = await test_client.get("/api/items")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1
    for item in items:
        assert "id" in item
        assert "name" in item
        assert "cost" in item


@pytest.mark.asyncio
async def test_get_item(test_client):
    """GET /api/items/1 should return Blink Dagger."""
    response = await test_client.get("/api/items/1")
    assert response.status_code == 200
    item = response.json()
    assert item["id"] == 1


@pytest.mark.asyncio
async def test_get_item_not_found(test_client):
    """GET /api/items/99999 should return 404."""
    response = await test_client.get("/api/items/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recommend_endpoint(test_client):
    """POST /api/recommend should return a valid recommendation response.

    Uses mocked LLM engine to avoid real Claude API calls in tests.
    Rules engine should still fire based on test data.
    """
    # Mock the LLM engine to return None (fallback mode) to avoid real API calls
    with patch("api.routes.recommend._llm") as mock_llm:
        mock_llm.generate = AsyncMock(return_value=None)

        response = await test_client.post("/api/recommend", json={
            "hero_id": 1,
            "role": 1,
            "playstyle": "farming",
            "side": "radiant",
            "lane": "safe",
            "lane_opponents": [69],  # Bristleback (spell-spammer)
            "allies": [],
        })

    assert response.status_code == 200
    data = response.json()
    assert "phases" in data
    assert "fallback" in data
    assert data["fallback"] is True  # Since LLM is mocked to return None
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], int)

    # Verify rules engine fired (Magic Stick vs Bristleback)
    all_item_ids = []
    for phase in data["phases"]:
        assert "phase" in phase
        assert "items" in phase
        for item in phase["items"]:
            assert "item_id" in item
            assert "reasoning" in item
            all_item_ids.append(item["item_id"])

    # Magic Stick (id=36) should be recommended vs Bristleback
    assert 36 in all_item_ids


@pytest.mark.asyncio
async def test_recommend_endpoint_validation(test_client):
    """POST /api/recommend with invalid data should return 422."""
    response = await test_client.post("/api/recommend", json={
        "hero_id": 1,
        "role": 6,  # Invalid: must be 1-5
        "playstyle": "farming",
        "side": "radiant",
        "lane": "safe",
    })
    assert response.status_code == 422
