import pytest


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
