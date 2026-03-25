"""Tests for GSI payload parsing, state manager, and name normalization."""

import time

import pytest

from gsi.models import GsiPayload, GsiItemSlot, GsiMap, GsiPlayer, GsiHero, GsiItems
from gsi.state_manager import ParsedGsiState, GsiStateManager


# Sample GSI JSON matching Dota 2 player-mode structure
SAMPLE_GSI_PAYLOAD = {
    "provider": {
        "name": "Dota 2",
        "appid": 570,
        "version": 47,
        "timestamp": 1234567890,
    },
    "map": {
        "name": "start",
        "matchid": "1234567890",
        "game_time": 653,
        "clock_time": 600,
        "daytime": True,
        "nightstalker_night": False,
        "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
        "paused": False,
        "win_team": "none",
        "customgamename": "",
        "ward_purchase_cooldown": 0,
    },
    "player": {
        "steamid": "76561198012345678",
        "accountid": "12345678",
        "name": "PlayerName",
        "activity": "playing",
        "kills": 3,
        "deaths": 1,
        "assists": 7,
        "last_hits": 145,
        "denies": 12,
        "kill_streak": 2,
        "commands_issued": 4521,
        "team_name": "radiant",
        "gold": 1523,
        "gold_reliable": 500,
        "gold_unreliable": 1023,
        "gold_from_hero_kills": 800,
        "gold_from_creep_kills": 4200,
        "gold_from_income": 2000,
        "gold_from_shared": 300,
        "gpm": 456,
        "xpm": 512,
        "net_worth": 12500,
    },
    "hero": {
        "id": 1,
        "name": "npc_dota_hero_antimage",
        "level": 12,
        "xpos": -1234,
        "ypos": 567,
        "alive": True,
        "respawn_seconds": 0,
        "buyback_cost": 876,
        "buyback_cooldown": 0,
        "health": 1200,
        "max_health": 1400,
        "health_percent": 85,
        "mana": 400,
        "max_mana": 600,
        "mana_percent": 66,
        "silenced": False,
        "stunned": False,
        "disarmed": False,
        "magicimmune": False,
        "hexed": False,
        "muted": False,
        "break": False,
        "has_debuff": False,
        "aghanims_scepter": False,
        "aghanims_shard": False,
    },
    "items": {
        "slot0": {
            "name": "item_power_treads",
            "purchaser": 0,
            "can_cast": False,
            "cooldown": 0,
            "passive": True,
            "charges": 0,
        },
        "slot1": {
            "name": "item_bfury",
            "purchaser": 0,
            "can_cast": False,
            "cooldown": 0,
            "passive": True,
            "charges": 0,
        },
        "slot2": {
            "name": "item_manta",
            "purchaser": 0,
            "can_cast": True,
            "cooldown": 0,
            "passive": False,
            "charges": 0,
        },
        "slot3": {"name": "empty"},
        "slot4": {"name": "empty"},
        "slot5": {"name": "empty"},
        "slot6": {
            "name": "item_tpscroll",
            "purchaser": 0,
            "can_cast": True,
            "cooldown": 0,
            "passive": False,
            "charges": 1,
        },
        "slot7": {"name": "empty"},
        "slot8": {"name": "empty"},
        "stash0": {"name": "empty"},
        "stash1": {"name": "empty"},
        "stash2": {"name": "empty"},
        "stash3": {"name": "empty"},
        "stash4": {"name": "empty"},
        "stash5": {"name": "empty"},
        "teleport0": {
            "name": "item_tpscroll",
            "purchaser": 0,
            "can_cast": True,
            "cooldown": 0,
            "passive": False,
            "charges": 1,
        },
        "neutral0": {
            "name": "item_mysterious_hat",
            "purchaser": 0,
            "can_cast": False,
            "cooldown": 0,
            "passive": True,
            "charges": 0,
        },
    },
    "auth": {"token": "prismlab"},
    "previously": {"player": {"gold": 1480}, "map": {"clock_time": 599}},
    "added": {},
}


class TestGsiPayloadParsing:
    """Tests for GsiPayload Pydantic model validation."""

    def test_payload_parses_sample_gsi_json(self):
        """GsiPayload.model_validate should parse complete GSI JSON without error."""
        payload = GsiPayload.model_validate(SAMPLE_GSI_PAYLOAD)
        assert payload.map is not None
        assert payload.player is not None
        assert payload.hero is not None
        assert payload.items is not None
        assert payload.auth is not None

    def test_payload_extracts_map_fields(self):
        """Map fields are correctly parsed."""
        payload = GsiPayload.model_validate(SAMPLE_GSI_PAYLOAD)
        assert payload.map.game_state == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
        assert payload.map.clock_time == 600
        assert payload.map.matchid == "1234567890"

    def test_payload_extracts_player_fields(self):
        """Player fields are correctly parsed."""
        payload = GsiPayload.model_validate(SAMPLE_GSI_PAYLOAD)
        assert payload.player.kills == 3
        assert payload.player.deaths == 1
        assert payload.player.assists == 7
        assert payload.player.gold == 1523
        assert payload.player.gpm == 456
        assert payload.player.net_worth == 12500
        assert payload.player.team_name == "radiant"

    def test_payload_extracts_hero_fields(self):
        """Hero fields are correctly parsed."""
        payload = GsiPayload.model_validate(SAMPLE_GSI_PAYLOAD)
        assert payload.hero.name == "npc_dota_hero_antimage"
        assert payload.hero.id == 1
        assert payload.hero.level == 12
        assert payload.hero.alive is True

    def test_payload_ignores_extra_fields(self):
        """GsiPayload should accept unknown top-level keys (provider, previously, added)."""
        payload = GsiPayload.model_validate(SAMPLE_GSI_PAYLOAD)
        # Should not raise -- extra="allow" handles provider, previously, added
        assert payload is not None


class TestGsiStateManager:
    """Tests for GsiStateManager parsing and state management."""

    def test_update_populates_all_d13_fields(self):
        """update() should populate all D-13 fields from sample GSI JSON."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()

        assert state is not None
        assert state.hero_name == "antimage"
        assert state.hero_id == 1
        assert state.hero_level == 12
        assert state.gold == 1523
        assert state.gpm == 456
        assert state.net_worth == 12500
        assert state.kills == 3
        assert state.deaths == 1
        assert state.assists == 7
        assert state.game_clock == 600
        assert state.game_state == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
        assert state.team_side == "radiant"
        assert state.is_alive is True

    def test_hero_name_normalization(self):
        """Hero name 'npc_dota_hero_antimage' should normalize to 'antimage'."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert state.hero_name == "antimage"

    def test_item_name_normalization(self):
        """Item name 'item_power_treads' should normalize to 'power_treads'."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert state.items_inventory[0] == "power_treads"
        assert state.items_inventory[1] == "bfury"
        assert state.items_inventory[2] == "manta"

    def test_empty_item_becomes_empty_string(self):
        """Item name 'empty' should become empty string ''."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert state.items_inventory[3] == ""
        assert state.items_inventory[4] == ""
        assert state.items_inventory[5] == ""

    def test_inventory_has_six_slots(self):
        """items_inventory should have exactly 6 entries (slot0-slot5)."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert len(state.items_inventory) == 6

    def test_backpack_has_three_slots(self):
        """items_backpack should have exactly 3 entries (slot6-slot8)."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert len(state.items_backpack) == 3
        assert state.items_backpack[0] == "tpscroll"  # slot6
        assert state.items_backpack[1] == ""  # slot7 empty
        assert state.items_backpack[2] == ""  # slot8 empty

    def test_neutral_item_parsed(self):
        """neutral0 item should be parsed and normalized."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        state = manager.get_state()
        assert state.items_neutral == "mysterious_hat"

    def test_is_connected_true_after_update(self):
        """is_connected should return True within 10s of update."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        assert manager.is_connected is True

    def test_is_connected_false_before_any_update(self):
        """is_connected should return False before any update."""
        manager = GsiStateManager()
        assert manager.is_connected is False

    def test_is_connected_false_after_timeout(self):
        """is_connected should return False after 10s with no update."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        # Simulate time passing by backdating _last_update
        manager._last_update = time.time() - 11
        assert manager.is_connected is False

    def test_get_connection_info(self):
        """get_connection_info() returns dict with required keys."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        info = manager.get_connection_info()
        assert "connected" in info
        assert "last_update" in info
        assert "game_clock" in info
        assert "game_state" in info
        assert info["connected"] is True
        assert info["game_clock"] == 600
        assert info["game_state"] == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"

    def test_get_connection_info_before_update(self):
        """get_connection_info() before any update returns None for game fields."""
        manager = GsiStateManager()
        info = manager.get_connection_info()
        assert info["connected"] is False
        assert info["game_clock"] is None
        assert info["game_state"] is None

    def test_to_broadcast_dict(self):
        """to_broadcast_dict() returns serialized state dict."""
        manager = GsiStateManager()
        manager.update(SAMPLE_GSI_PAYLOAD)
        d = manager.to_broadcast_dict()
        assert d is not None
        assert d["hero_name"] == "antimage"
        assert d["gold"] == 1523
        assert isinstance(d["items_inventory"], list)

    def test_to_broadcast_dict_none_before_update(self):
        """to_broadcast_dict() returns None before any update."""
        manager = GsiStateManager()
        assert manager.to_broadcast_dict() is None


# --- Integration tests (require test_client fixture from conftest.py) ---


@pytest.mark.asyncio
async def test_gsi_endpoint_returns_200(test_client):
    """POST /gsi with valid payload + correct auth token returns 200."""
    response = await test_client.post("/gsi", json=SAMPLE_GSI_PAYLOAD)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_gsi_endpoint_rejects_bad_token(test_client):
    """POST /gsi with wrong auth token returns 401."""
    payload = {**SAMPLE_GSI_PAYLOAD, "auth": {"token": "wrong_token"}}
    response = await test_client.post("/gsi", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_gsi_endpoint_returns_200_on_parse_error(test_client):
    """POST /gsi with malformed body (but valid token) still returns 200."""
    malformed_payload = {
        "auth": {"token": "prismlab"},
        "hero": "not_a_dict",  # This will cause parsing to fail
    }
    response = await test_client.post("/gsi", json=malformed_payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_gsi_config_generation(test_client):
    """GET /api/gsi-config?host=192.168.1.100 returns config with correct IP."""
    response = await test_client.get("/api/gsi-config?host=192.168.1.100")
    assert response.status_code == 200
    content = response.text
    assert "192.168.1.100" in content
    assert "8421" in content
    assert "gamestate_integration_prismlab" in content
    assert "prismlab" in content  # auth token


@pytest.mark.asyncio
async def test_gsi_config_custom_port(test_client):
    """GET /api/gsi-config with custom port includes the port in the URI."""
    response = await test_client.get("/api/gsi-config?host=10.0.0.1&port=9000")
    assert response.status_code == 200
    content = response.text
    assert "10.0.0.1" in content
    assert "9000" in content
