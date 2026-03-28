from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    anthropic_api_key: str = ""
    opendota_api_key: str | None = None
    stratz_api_token: str | None = None
    database_url: str = "sqlite+aiosqlite:///./data/prismlab.db"
    gsi_auth_token: str = "prismlab"
    response_cache_ttl_seconds: int = 300  # 5 minutes default
    steam_id: str | None = None  # Default Steam ID from .env for auto-draft

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
