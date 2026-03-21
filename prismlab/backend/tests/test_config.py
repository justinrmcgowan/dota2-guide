from config import Settings


def test_settings_defaults():
    """Settings should have sensible defaults when no .env is present."""
    s = Settings()
    assert s.anthropic_api_key == ""
    assert s.opendota_api_key is None
    assert "sqlite+aiosqlite" in s.database_url


def test_settings_custom_values():
    """Settings should accept custom values via constructor."""
    s = Settings(anthropic_api_key="test-key")
    assert s.anthropic_api_key == "test-key"
