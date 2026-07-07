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
    alltick_token: str | None = None
    alltick_base_url: str = "https://quote.alltick.io"
    alltick_timeout_seconds: float = 4
    alltick_international_symbols: str = "XAUUSD:OANDA:国际现货黄金:USD/oz"
    alltick_domestic_symbols: str = "AU9999:SGE:上海金 AU9999:CNY/g"


@lru_cache
def get_settings() -> Settings:
    return Settings()
