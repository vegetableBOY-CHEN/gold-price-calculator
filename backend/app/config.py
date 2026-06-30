from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Gold Price Calculator"
    debug: bool = True
    rules_dir: str = str(PROJECT_ROOT / "rules")
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'gold.db'}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
